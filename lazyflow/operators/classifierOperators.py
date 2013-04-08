import numpy
import time
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.request import Request, Pool
import vigra
import copy
from functools import partial

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)
from lazyflow.utility import traceLogged

class OpTrainRandomForest(Operator):
    name = "TrainRandomForest"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1),InputSlot("Labels", level=1), InputSlot("fixClassifier", stype="bool")]
    outputSlots = [OutputSlot("Classifier")]

    def __init__(self, parent = None):
        Operator.__init__(self, parent)
        self._forest_count = 4
        # TODO: Make treecount configurable via an InputSlot
        self._tree_count = 25

    def setupOutputs(self):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self._forest_count,)
            self.outputs["Classifier"].setDirty((slice(0,1,None),))


    @traceLogged(logger, level=logging.INFO, msg="OpTrainRandomForest: Training Classifier")
    def execute(self, slot, subindex, roi, result):
        featMatrix=[]
        labelsMatrix=[]
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.meta.shape is not None:
                labels=labels[:].allocate().wait()

                indexes=numpy.nonzero(labels[...,0].view(numpy.ndarray))
                #Maybe later request only part of the region?

                image=self.inputs["Images"][i][:].allocate().wait()

                features=image[indexes]
                labels=labels[indexes]

                featMatrix.append(features)
                labelsMatrix.append(labels)


        featMatrix=numpy.concatenate(featMatrix,axis=0)
        labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)

        # train and store self._forest_count forests in parallel
        pool = Pool()
        for i in range(self._forest_count):
            def train_and_store(number):
                result[number] = vigra.learning.RandomForest(self._tree_count)
                result[number].learnRF(featMatrix.astype(numpy.float32),labelsMatrix.astype(numpy.uint32))
            req = pool.request(partial(train_and_store, i))

        pool.wait()

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.inputs["fixClassifier"] and self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))


class OpTrainRandomForestBlocked(Operator):
    name = "TrainRandomForestBlocked"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1),InputSlot("Labels", level=1), InputSlot("fixClassifier", stype="bool"), \
                  InputSlot("nonzeroLabelBlocks", level=1)]
    outputSlots = [OutputSlot("Classifier")]

    WarningEmitted = False

    def __init__(self, *args, **kwargs):
        super(OpTrainRandomForestBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._forest_count = 10
        # TODO: Make treecount configurable via an InputSlot
        self._tree_count = 10

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

        key = roi.toSlice()
        featMatrix=[]
        labelsMatrix=[]
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.meta.shape is not None:
                #labels=labels[:].allocate().wait()
                blocks = self.inputs["nonzeroLabelBlocks"][i][0].allocate().wait()

                progress += 10/numImages
                self.progressSignal(progress)

                reqlistlabels = []
                reqlistfeat = []
                traceLogger.debug("Sending requests for {} non-zero blocks (labels and data)".format( len(blocks[0])) )
                for b in blocks[0]:

                    request = labels[b].allocate()
                    featurekey = list(b)
                    featurekey[-1] = slice(None, None, None)
                    request2 = self.inputs["Images"][i][featurekey].allocate()

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
                    image = req.notify(progressNotify)

                for ir, req in enumerate(reqlistlabels):
                    labblock = req.notify(progressNotify)

                traceLogger.debug("Requests fired")

                for ir, req in enumerate(reqlistlabels):
                    traceLogger.debug("Waiting for a label block...")
                    labblock = req.wait()

                    traceLogger.debug("Waiting for an image block...")
                    image = reqlistfeat[ir].wait()

                    indexes=numpy.nonzero(labblock[...,0].view(numpy.ndarray))
                    features=image[indexes]
                    labbla=labblock[indexes]

                    featMatrix.append(features)
                    labelsMatrix.append(labbla)

                progress = progress_outer[0]

                traceLogger.debug("Requests processed")

        self.progressSignal(80/numImages)

        if len(featMatrix) == 0 or len(labelsMatrix) == 0:
            # If there was no actual data for the random forest to train with, we return None
            result[:] = None
        else:
            featMatrix=numpy.concatenate(featMatrix,axis=0)
            labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)

            try:
                logger.debug("Learning with Vigra...")
                # train and store self._forest_count forests in parallel
                pool = Pool()

                for i in range(self._forest_count):
                    def train_and_store(number):
                        result[number] = vigra.learning.RandomForest(self._tree_count)
                        result[number].learnRF( numpy.asarray(featMatrix, dtype=numpy.float32),
                                                numpy.asarray(labelsMatrix, dtype=numpy.uint32))
                    req = pool.request(partial(train_and_store, i))

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


class OpPredictRandomForest(Operator):
    name = "PredictRandomForest"
    description = "Predict on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Image"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("PMaps")]

    def setupOutputs(self):
        nlabels=self.inputs["LabelsCount"].value
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.axistags = copy.copy(self.Image.meta.axistags)
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)

    def execute(self, slot, subindex, roi, result):
        t1 = time.time()
        key = roi.toSlice()
        nlabels=self.inputs["LabelsCount"].value

        traceLogger.debug("OpPredictRandomForest: Requesting classifier. roi={}".format(roi))
        forests=self.inputs["Classifier"][:].wait()

        if forests is None:
            # Training operator may return 'None' if there was no data to train with
            return numpy.zeros(numpy.subtract(roi.stop, roi.start), dtype=numpy.float32)[...]

        traceLogger.debug("OpPredictRandomForest: Got classifier")
        #assert RF.labelCount() == nlabels, "ERROR: OpPredictRandomForest, labelCount differs from true labelCount! %r vs. %r" % (RF.labelCount(), nlabels)

        newKey = key[:-1]
        newKey += (slice(0,self.inputs["Image"].meta.shape[-1],None),)

        res = self.inputs["Image"][newKey].wait()

        shape=res.shape
        prod = numpy.prod(shape[:-1])
        res.shape = (prod, shape[-1])
        features=res

        predictions = [0]*len(forests)

        def predict_forest(number):
            predictions[number] = forests[number].predictProbabilities(numpy.asarray(features, dtype=numpy.float32))

        t2 = time.time()

        # predict the data with all the forests in parallel
        pool = Pool()

        for i,f in enumerate(forests):
            req = pool.request(partial(predict_forest, i))

        pool.wait()
        pool.clean()

        prediction=numpy.dstack(predictions)
        prediction = numpy.average(prediction, axis=2)
        prediction.shape =  shape[:-1] + (forests[0].labelCount(),)
        #prediction = prediction.reshape(*(shape[:-1] + (forests[0].labelCount(),)))

        # If our LabelsCount is higher than the number of labels in the training set,
        # then our results aren't really valid.
        # Duplicate the last label's predictions
        chanslice = slice(min(key[-1].start, forests[0].labelCount()-1), min(key[-1].stop, forests[0].labelCount()))

        t3 = time.time()

        # logger.info("Predict took %fseconds, actual RF time was %fs, feature time was %fs" % (t3-t1, t3-t2, t2-t1))

        return prediction[...,chanslice] # FIXME: This assumes that channel is the last axis



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


class OpSegmentation(Operator):
    name = "OpSegmentation"
    description = "displaying highest probability class for each pixel"

    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"].meta.shape = inputSlot.meta.shape[:-1] + (1,)
        self.outputs["Output"].meta.dtype = numpy.uint8 #who is going to have more than 256 classes?
        self.outputs["Output"].meta.axistags = inputSlot.meta.axistags

    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)
        shape = self.inputs["Input"].meta.shape

        rstart, rstop = sliceToRoi(key, self.outputs["Output"].meta.shape)
        rstart[-1] = 0
        rstop[-1] = shape[-1]
        rkey = roiToSlice(rstart, rstop)
        img = self.inputs["Input"][rkey].allocate().wait()
        axis = img.ndim - 1
        result = numpy.argmax(img, axis=axis)
        result.resize(result.shape + (1,))
        return result

    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        ndim = len(self.outputs['Output'].meta.shape)
        if len(key) > ndim:
            key = key[:ndim]
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"].meta.shape

    @property
    def dtype(self):
        return self.outputs["Output"].meta.dtype


class OpAreas(Operator):
    name = "OpAreas"
    description = "counting pixel areas"

    inputSlots = [InputSlot("Input"), InputSlot("NumberOfChannels")]
    outputSlots = [OutputSlot("Areas")]

    def setupOutputs(self):

        self.outputs["Areas"].meta.shape = (self.inputs["NumberOfChannels"].value,)

    def execute(self, slot, subindex, roi, result):
        img = self.inputs["Input"][:].allocate().wait()

        numC = self.inputs["NumberOfChannels"].value

        areas = []
        for i in range(numC):
            areas.append(0)

        for i in img.flat:
            areas[int(i)] +=1

        return numpy.array(areas)



    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"].meta.shape

    @property
    def dtype(self):
        return self.outputs["Output"].meta.dtype
