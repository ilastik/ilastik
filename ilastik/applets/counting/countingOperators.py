###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)
import numpy as np
import time
import copy
import importlib
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow.request import Request, RequestPool
from lazyflow.utility import traceLogged
from lazyflow.operators import OpPixelOperator

from ilastik.applets.counting.countingsvr import SVR



from lazyflow.operators.imgFilterOperators import OpGaussianSmoothing

class OpLabelPreviewer(OpGaussianSmoothing):
    name = "LabelPreviewer"

class OpLabelPreviewerRefactored(Operator):

    name = "LabelPreviewer"

    inputSlots = [InputSlot("Images", level=1)]
    outputSlots = [OutputSlot("Output", level=1)]






def checkOption(reqlist):
    for req in reqlist:
        try:
            importlib.import_module(req)
        except:
            return False
    return True



class OpTrainCounter(Operator):
    name = "TrainCounter"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1),
                  InputSlot("ForegroundLabels", level=1), 
                  InputSlot("BackgroundLabels", level=1),
                  InputSlot("fixClassifier", stype="bool"),
                  InputSlot("nonzeroLabelBlocks", level=1),
                  InputSlot("Sigma", stype = "float"), 
                  InputSlot("Epsilon",  stype = "float"), 
                  InputSlot("C",  stype = "float"), 
                  InputSlot("SelectedOption", stype = "object"),
                  InputSlot("Ntrees", stype = "int"), #RF parameter
                  InputSlot("MaxDepth", stype = "object"), #RF parameter, None means grow until purity
                  InputSlot("BoxConstraintRois", level = 1, stype = "list", value = []),
                  InputSlot("BoxConstraintValues", level = 1, stype = "list", value = []),
                  InputSlot("UpperBound")
                 ]
    outputSlots = [OutputSlot("Classifier")]
    options = SVR.options
    availableOptions = [checkOption(option["req"]) for option in SVR.options]
    numRegressors = 4

    def __init__(self, *args, **kwargs):
        super(OpTrainCounter, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._svr = SVR()
        params = self._svr.get_params()
        self.initInputs(params)
        self.Classifier.meta.dtype = object
        self.Classifier.meta.shape = (self.numRegressors,)

    def initInputs(self, params):
        fix = False
        if self.fixClassifier.ready():
            fix = self.fixClassifier.value
        self.fixClassifier.setValue(True)
        self.Sigma.setValue(params["Sigma"])
        self.Epsilon.setValue(params["epsilon"])
        self.C.setValue(params["C"])
        self.Ntrees.setValue(params["ntrees"])
        self.MaxDepth.setValue(params["maxdepth"])
        self.SelectedOption.setValue(params["method"])

        self.fixClassifier.setValue(fix)

    def setupOutputs(self):
        if self.inputs["fixClassifier"].value == False:
            method = self.SelectedOption.value
            if type(method) is dict:
                method = method["method"]
            
            params = {"method" : method,
                      "Sigma": self.Sigma.value,
                      "epsilon" : self.Epsilon.value,
                      "C" : self.C.value,
                      "ntrees" : self.Ntrees.value,
                      "maxdepth" :self.MaxDepth.value
                     }
            self._svr.set_params(**params)
            #self.Classifier.setValue(self._svr)
            #self.outputs["Classifier"].meta.dtype = object
            #self.outputs["Classifier"].meta.shape = (self._forest_count,)



    #@traceLogged(logger, level=logging.INFO, msg="OpTrainCounter: Training Counting Regressor")
    def execute(self, slot, subindex, roi, result):

        progress = 0
        numImages = len(self.Images)
        self.progressSignal(progress)
        featMatrix=[]
        labelsMatrix=[]
        tagList = []

        
        #result[0] = self._svr

        for i,labels in enumerate(self.inputs["ForegroundLabels"]):
            if labels.meta.shape is not None:
                opGaussian = OpGaussianSmoothing(parent = self, graph = self.graph)
                opGaussian.Sigma.setValue(self.Sigma.value)
                opGaussian.Input.connect(self.ForegroundLabels[i])
                blocks = self.inputs["nonzeroLabelBlocks"][i][0].wait()
                
                reqlistlabels = []
                reqlistbg = []
                reqlistfeat = []
                progress += 10 / numImages
                self.progressSignal(progress)
                
                for b in blocks[0]:
                    request = opGaussian.Output[b]
                    #request = labels[b]
                    featurekey = list(b)
                    featurekey[-1] = slice(None, None, None)
                    request2 = self.Images[i][featurekey]
                    request3 = self.inputs["BackgroundLabels"][i][b]
                    reqlistlabels.append(request)
                    reqlistfeat.append(request2)
                    reqlistbg.append(request3)

                traceLogger.debug("Requests prepared")

                numLabelBlocks = len(reqlistlabels)
                progress_outer = [progress]
                if numLabelBlocks > 0:
                    progressInc = (80 - 10)/(numLabelBlocks * numImages)

                def progressNotify(req):
                    progress_outer[0] += progressInc/2
                    self.progressSignal(progress_outer[0])

                for ir, req in enumerate(reqlistfeat):
                    req.notify_finished(progressNotify)
                    req.submit()

                for ir, req in enumerate(reqlistlabels):
                    req.notify_finished(progressNotify)
                    req.submit()

                for ir, req in enumerate(reqlistbg):
                    req.notify_finished(progressNotify)
                    req.submit()
                
                traceLogger.debug("Requests fired")
                

                #Fixme: Maybe later request only part of the region?

                #image=self.inputs["Images"][i][:].wait()
                for ir, req in enumerate(reqlistlabels):
                    
                    labblock = req.wait()
                    
                    image = reqlistfeat[ir].wait()
                    labbgblock = reqlistbg[ir].wait()
                    labblock = labblock.reshape((image.shape[:-1]))
                    image = image.reshape((-1, image.shape[-1]))
                    labbgindices = np.where(labbgblock == 2)            
                    labbgindices = np.ravel_multi_index(labbgindices, labbgblock.shape)
                    
                    newDot, mapping, tags = \
                    self._svr.prepareDataRefactored(labblock, labbgindices)
                    #self._svr.prepareData(labblock, smooth = True)

                    labels   = newDot[mapping]
                    features = image[mapping]

                    featMatrix.append(features)
                    labelsMatrix.append(labels)
                    tagList.append(tags)
                
                progress = progress_outer[0]

                traceLogger.debug("Requests processed")


        self.progressSignal(80 / numImages)
        if len(featMatrix) == 0 or len(labelsMatrix) == 0:
            result[:] = None

        else:
            posTags = [tag[0] for tag in tagList]
            negTags = [tag[1] for tag in tagList]
            numPosTags = np.sum(posTags)
            numTags = np.sum(posTags) + np.sum(negTags)
            fullFeatMatrix = np.ndarray((numTags, self.Images[0].meta.shape[-1]), dtype = np.float64)
            fullLabelsMatrix = np.ndarray((numTags), dtype = np.float64)
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


            assert(not np.isnan(np.sum(fullFeatMatrix)))

            fullTags = [np.sum(posTags), np.sum(negTags)]
            #pool = RequestPool()

            maxima = np.max(fullFeatMatrix, axis=0)
            minima = np.min(fullFeatMatrix, axis=0)
            normalizationFactors = (minima,maxima)
            



            boxConstraintList = []
            boxConstraints = None
            if self.BoxConstraintRois.ready() and self.BoxConstraintValues.ready():
                for i, slot in enumerate(zip(self.BoxConstraintRois,self.BoxConstraintValues)):
                    for constr, val in zip(slot[0].value, slot[1].value):
                        boxConstraintList.append((i, constr, val))
                if len(boxConstraintList) > 0:
                    boxConstraints = self.constructBoxConstraints(boxConstraintList)

            params = self._svr.get_params() 
            try:
                pool = RequestPool()
                def train_and_store(i):
                    result[i] = SVR(minmax = normalizationFactors, **params)
                    result[i].fitPrepared(fullFeatMatrix, fullLabelsMatrix, tags = fullTags, boxConstraints = boxConstraints, numRegressors
                         = self.numRegressors, trainAll = False)
                for i in range(self.numRegressors):
                    req = pool.request(partial(train_and_store, i))
                
                pool.wait()
                pool.clean()
            
            except:
                logger.error("ERROR: could not learn regressor")
                logger.error("fullFeatMatrix shape = {}, dtype = {}".format(fullFeatMatrix.shape, fullFeatMatrix.dtype) )
                logger.error("fullLabelsMatrix shape = {}, dtype = {}".format(fullLabelsMatrix.shape, fullLabelsMatrix.dtype) )
                raise
            finally:
                self.progressSignal(100) 

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.inputs["fixClassifier"] and self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(None),))
    
    def constructBoxConstraints(self, constraints):
        
        try:
            shape = np.array([[stop - start for start, stop in zip(constr[0][1:-2], constr[1][1:-2])] for _, constr,_ in
                       constraints])
            taggedShape = self.Images[0].meta.getTaggedShape()
            numcols = taggedShape['c']
            shape = shape[:,0] * shape[:,1]
            shape = np.sum(shape,axis = 0)
            constraintmatrix = np.ndarray(shape = (shape, numcols))
            constraintindices = []
            constraintvalues =  []
            offset = 0
            for imagenumber, constr, value in constraints:
                    slicing = [slice(start,stop) for start, stop in zip(constr[0][1:-2], constr[1][1:-2])]
                    numrows = (slicing[0].stop - slicing[0].start) * (slicing[1].stop - slicing[1].start)
                    slicing.append(slice(None)) 
                    slicing = tuple(slicing)

                    constraintmatrix[offset:offset + numrows,:] = self.Images[imagenumber][slicing].wait().reshape((numrows,
                                                                                                          -1))
                    constraintindices.append(offset)
                    constraintvalues.append(value)
                    offset = offset + numrows
            constraintindices.append(offset)

            constraintvalues = np.array(constraintvalues, np.float64)
            constraintindices = np.array(constraintindices, np.int)

            boxConstraints = {"boxFeatures" : constraintmatrix, "boxValues" : constraintvalues, "boxIndices" :
                              constraintindices}
        except:
            boxConstraints = None
            logger.error("An error has occured with the box Constraints: {} ".format(constraints))
        
        return boxConstraints

if not any(OpTrainCounter.availableOptions):
    raise ImportError("None of the implemented methods are available")



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
        self.PMaps.meta.shape = self.Image.meta.shape[:-1] + (OpTrainCounter.numRegressors,) # FIXME: This assumes that channel is the last axis
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

        shape=res.shape
        prod = np.prod(shape[:-1])
        res.shape = (prod, shape[-1])
        features=res

        predictions = [0]*len(forests)

        t2 = time.time()

        pool = RequestPool()
        
        def predict_forest(i):
            predictions[i] = forests[i].predict(np.asarray(features, dtype = np.float32))
            predictions[i] = predictions[i].reshape(result.shape[:-1])


        for i,f in enumerate(forests):
            req = pool.request(partial(predict_forest,i))

        pool.wait()
        pool.clean()
        #predictions[0] = forests[0].predict(np.asarray(features, dtype = np.float32), normalize = False)
        #predictions[0] = predictions[0].reshape(result.shape)
        prediction=np.dstack(predictions)
        result[...] = prediction

        # If our LabelsCount is higher than the number of labels in the training set,
        # then our results aren't really valid.  FIXME !!!
        # Duplicate the last label's predictions
        #for c in range(result.shape[-1]):
        #    result[...,c] = prediction[...,min(c+key[-1].start, prediction.shape[-1]-1)]

        t3 = time.time()

        logger.debug("Predict took %fseconds, actual RF time was %fs, feature time was %fs" % (t3-t1, t3-t2, t2-t1))
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


