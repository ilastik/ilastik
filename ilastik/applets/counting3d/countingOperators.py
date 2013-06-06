
import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)
import numpy as np
import time
import copy
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow.request import Request, RequestPool
from lazyflow.utility import traceLogged

from ilastik.applets.counting3d.countingsvr import SVR


class OpTrainCounter(Operator):
    name = "TrainCounter"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1),InputSlot("Labels", level=1), InputSlot("fixClassifier", stype="bool"),
                  InputSlot("nonzeroLabelBlocks", level=1),
                  InputSlot("Sigma", stype = "object"), 
                  InputSlot("Epsilon", value = 1E-3, stype = "float"), 
                  InputSlot("UnderMult", value = 100, stype = "float"),
                  InputSlot("OverMult", value = 100, stype = "float"), 
                  InputSlot("SelectedOption", 
                            value = SVR.options[0],
                            stype = "object"),
                  InputSlot("BoxConstraints", optional = True)
                 ]
    outputSlots = [OutputSlot("Classifier")]
    options = SVR.options

    def __init__(self, *args, **kwargs):
        super(OpTrainCounter, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._forest_count = 1

    def setupOutputs(self):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self._forest_count,)


    @traceLogged(logger, level=logging.INFO, msg="OpTrainRandomForest: Training Classifier")
    def execute(self, slot, subindex, roi, result):
        featMatrix=[]
        labelsMatrix=[]
        tagList = []

        result[0] = SVR(self.UnderMult.value, self.OverMult.value, limitDensity = True, **self.SelectedOption.value)
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.meta.shape is not None:
                labels=labels[:].wait()

                #Maybe later request only part of the region?

                image=self.inputs["Images"][i][:].wait()

                newImg, newDot, mapping, tags = \
                result[0].prepareData(image, labels, sigma = self.Sigma.value, smooth = True, normalize = False)
                features=newImg[mapping]
                labels=newDot[mapping]

                featMatrix.append(features)
                labelsMatrix.append(labels)
                tagList.append(tags)
                #tagsMatrix.append(tags)

        posTags = [tag[0] for tag in tagList]
        negTags = [tag[1] for tag in tagList]
        numPosTags = np.sum(posTags)
        numTags = np.sum(posTags) + np.sum(negTags)
        fullFeatMatrix = np.ndarray((numTags, self.Images[0].meta.shape[-1]))
        fullLabelsMatrix = np.ndarray((numTags))
        fullFeatMatrix[:] = np.NAN
        fullLabelsMatrix[:] = np.NAN
        currPosCount = 0
        currNegCount = numPosTags
        for i, posCount in enumerate(posTags):
            fullFeatMatrix[currPosCount:currPosCount + posTags[i],:] = featMatrix[i][:posCount,:]
            fullLabelsMatrix[currPosCount:currPosCount + posTags[i]] = labelsMatrix[i][:posCount]
            fullFeatMatrix[currNegCount:currNegCount + negTags[i],:] = featMatrix[i][posCount:,:]
            fullLabelsMatrix[currNegCount:currNegCount + negTags[i]] = labelsMatrix[i][posCount:]
            currPosCount += posTags[i]
            currNegCount += negTags[i]


        if np.isnan(np.sum(fullFeatMatrix)):
            raise Exception("NAN NAN NAN NAN BATMAN")
        #featMatrix=np.concatenate(featMatrix,axis=0)
        #labelsMatrix=np.concatenate(labelsMatrix,axis=0)
        #tagsMatrix=np.concatenate(tagsMatrix,axis=0)

        # train and store self._forest_count forests in parallel

        fullTags = [np.sum(posTags), np.sum(negTags)]
        #pool = RequestPool()

        result[0].fitPrepared(fullFeatMatrix, fullLabelsMatrix, fullTags, self.Epsilon.value)
        #req = pool.request(partial(result[0].fitPrepared, featMatrix, labelsMatrix, tagsMatrix, self.Epsilon.value))
        #pool.wait()
        #pool.clean()

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.inputs["fixClassifier"] and self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(None),))



class OpTrainCounterBlocked(Operator):

    name = "TrainCounterBlocked"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1),InputSlot("Labels", level=1), InputSlot("fixClassifier", stype="bool"),
                  InputSlot("nonzeroLabelBlocks", level=1),
                  InputSlot("Sigma", stype = "object"), 
                  InputSlot("Epsilon", value = 1E-3, stype = "float"), 
                  InputSlot("UnderMult", value = 100, stype = "float"),
                  InputSlot("OverMult", value = 100, stype = "float"), 
                  InputSlot("SelectedOption", 
                            value = {"optimization" : "svr", "kernel" : "rbf"},
                            stype = "object")
                 ]
    outputSlots = [OutputSlot("Classifier")]

    WarningEmitted = False
    options = SVR.options

    def __init__(self, *args, **kwargs):
        super(OpTrainCounterBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._forest_count = 1
        # TODO: Make treecount configurable via an InputSlot
        #self._tree_count = 10

    def setupOutputs(self):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self._forest_count,)

            # No need to set dirty here: notifyDirty handles it.
            #self.outputs["Classifier"].setDirty((slice(0,1,None),))

    @traceLogged(logger, level=logging.INFO, msg="OpTrainRandomForestBlocked: Training Classifier")
    def execute(self, slot, subindex, roi, result):
        progress = 0
        self.progressSignal(progress)
        numImages = len(self.Images)

        featMatrix=[]
        labelsMatrix=[]
        tagsMatrix = []

        result[0] = SVR(self.UnderMult.value, self.OverMult.value, limitDensity = True, **self.SelectedOption.value)
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.meta.shape is not None:
                #labels=labels[:].wait()
                blocks = self.inputs["nonzeroLabelBlocks"][i][0].wait()

                progress += 10/numImages
                self.progressSignal(progress)

                reqlistlabels = []
                reqlistfeat = []
                traceLogger.debug("Sending requests for {} non-zero blocks (labels and data)".format( len(blocks[0])) )
                for b in blocks[0]:

                    request = labels[b]
                    featurekey = list(b)
                    featurekey[-1] = slice(None, None, None)
                    request2 = self.inputs["Images"][i][featurekey]

                    reqlistlabels.append(request)
                    reqlistfeat.append(request2)

                traceLogger.debug("Requests prepared")

                numLabelBlocks = len(reqlistlabels)
                progress_outer = [progress] # Store in list for closure access
                if numLabelBlocks > 0:
                    progressInc = (80-10)/numLabelBlocks/numImages

                def progressNotify(req):
                    # Note: If we wanted perfect progress reporting, we could use lock here
                    #       to protect the progress from being incremented simultaneously.
                    #       But that would slow things down and imperfect reporting is okay for our purposes.
                    progress_outer[0] += progressInc/2
                    self.progressSignal(progress_outer[0])

                for ir, req in enumerate(reqlistfeat):
                    image = req.notify_finished(progressNotify)

                for ir, req in enumerate(reqlistlabels):
                    labblock = req.notify_finished(progressNotify)

                traceLogger.debug("Requests fired")

                for ir, req in enumerate(reqlistlabels):
                    traceLogger.debug("Waiting for a label block...")
                    labblock = req.wait()

                    traceLogger.debug("Waiting for an image block...")
                    image = reqlistfeat[ir].wait()

                    newImg, newDot, mapping, tags = \
                    result[0].prepareData(image, labblock, sigma = self.Sigma.value, smooth = True, normalize = False)

                    features = newImg[mapping]
                    labbla = newDot[mapping]

                    #indexes=np.nonzero(labblock[...,0].view(np.ndarray))
                    #features=image[indexes]
                    #labbla=labblock[indexes]

                    featMatrix.append(features)
                    labelsMatrix.append(labbla)
                    tagsMatrix.append(tags)

                progress = progress_outer[0]

                traceLogger.debug("Requests processed")

        self.progressSignal(80/numImages)

        if len(featMatrix) == 0 or len(labelsMatrix) == 0:
            # If there was no actual data for the random forest to train with, we return None
            result[:] = None
        else:
            featMatrix=np.concatenate(featMatrix,axis=0)
            labelsMatrix=np.concatenate(labelsMatrix,axis=0)
            tagsMatrix=np.concatenate(tagsMatrix,axis=0)

            try:
                logger.debug("Learning with Vigra...")

                pool = RequestPool()

                #result[0].fitPrepared(featMatrix, labelsMatrix, tagsMatrix, self.Epsilon.value)
                req = pool.request(partial(result[0].fitPrepared, featMatrix, labelsMatrix, tagsMatrix, self.Epsilon.value))
                pool.wait()
                pool.clean()

                logger.debug("Vigra finished")
            except:
                logger.error( "ERROR: could not learn classifier" )
                logger.error( "featMatrix shape={}, max={}, dtype={}".format(featMatrix.shape, featMatrix.max(), featMatrix.dtype) )
                logger.error( "labelsMatrix shape={}, max={}, dtype={}".format(labelsMatrix.shape, labelsMatrix.max(), labelsMatrix.dtype ) )
                raise
            finally:
                self.progressSignal(100)

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.fixClassifier and self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))


class OpPredictCounter(Operator):
    name = "PredictCounter"
    description = "Predict on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Image"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("PMaps")]

    def setupOutputs(self):
        nlabels=self.inputs["LabelsCount"].value
        self.PMaps.meta.dtype = np.float32
        self.PMaps.meta.axistags = copy.copy(self.Image.meta.axistags)
        self.PMaps.meta.shape = self.Image.meta.shape[:-1] + (1,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)

    def execute(self, slot, subindex, roi, result):
        t1 = time.time()
        key = roi.toSlice()
        nlabels=self.inputs["LabelsCount"].value

        traceLogger.debug("OpPredictRandomForest: Requesting classifier. roi={}".format(roi))
        forests=self.inputs["Classifier"][:].wait()

        if forests is None:
            # Training operator may return 'None' if there was no data to train with
            return np.zeros(np.subtract(roi.stop, roi.start), dtype=np.float32)[...]

        traceLogger.debug("OpPredictRandomForest: Got classifier")
        #assert RF.labelCount() == nlabels, "ERROR: OpPredictRandomForest, labelCount differs from true labelCount! %r vs. %r" % (RF.labelCount(), nlabels)

        newKey = key[:-1]
        newKey += (slice(0,self.inputs["Image"].meta.shape[-1],None),)

        res = self.inputs["Image"][newKey].wait()
        print newKey

        shape=res.shape
        prod = np.prod(shape[:-1])
        res.shape = (prod, shape[-1])
        features=res

        predictions = [0]*len(forests)

        t2 = time.time()

        ## predict the data with all the forests in parallel
        #pool = RequestPool()

        #for i,f in enumerate(forests):
        #    req = pool.request(partial(predict_forest, i))

        #def predictCounter(number):
        #    predictions[number] = forests[number].predict(np.asarray(features, dtype = np.float32), normalize = False)
        #    predictions[number] = predictions[number].reshape(result.shape)
        ##req = pool.request(partial(forests[0].predict, np.asarray(features, dtype=np.float32), normalize = False))
        #for i,f in enumerate(forests):
        #    req = pool.request(partial(predictCounter, i))

        #pool.wait()
        #pool.clean()

        #prediction=np.dstack(predictions)
        #prediction = np.average(prediction, axis=2)
        #prediction.shape =  shape[:-1] + (forests[0].labelCount(),)
        #prediction = prediction.reshape(*(shape[:-1] + (forests[0].labelCount(),)))
        
        #import sitecustomize
        #sitecustomize.debug_trace()

        #result[...] = 0
        #for i,p in enumerate(predictions):
        #    result[...] += p
        #result[...] /= len(predictions)
        

        predictions[0] = forests[0].predict(np.asarray(features, dtype = np.float32), normalize = False)
        predictions[0] = predictions[0].reshape(result.shape)
        result[...] = predictions[0]
        # If our LabelsCount is higher than the number of labels in the training set,
        # then our results aren't really valid.  FIXME !!!
        # Duplicate the last label's predictions
        #for c in range(result.shape[-1]):
        #    result[...,c] = prediction[...,min(c+key[-1].start, prediction.shape[-1]-1)]

        t3 = time.time()

        logger.info("Predict took %fseconds, actual RF time was %fs, feature time was %fs" % (t3-t1, t3-t2, t2-t1))
        return result



    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        if slot == self.inputs["Classifier"]:
            logger.debug("OpPredictRandomForest: Classifier changed, setting dirty")
            if self.LabelsCount.ready() and self.LabelsCount.value > 0:
                self.outputs["PMaps"].setDirty(slice(None,None,None))
        elif slot == self.inputs["Image"]:
            nlabels=self.inputs["LabelsCount"].value
            if nlabels > 0:
                self.outputs["PMaps"].setDirty(key[:-1] + (slice(0,nlabels,None),))
        elif slot == self.inputs["LabelsCount"]:
            # When the labels count changes, we must resize the output
            if self.configured():
                # FIXME: It's ugly that we call the 'private' _setupOutputs() function here,
                #  but the output shape needs to change when this input becomes dirty,
                #  and the output change needs to be propagated to the rest of the graph.
                self._setupOutputs()
            self.outputs["PMaps"].setDirty(slice(None,None,None))


