# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

#Python
import time
import copy
from functools import partial
import logging
traceLogger = logging.getLogger("TRACE." + __name__)

#SciPy
import numpy
import vigra

#lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.request import Request, RequestPool
from lazyflow.utility import traceLogged

class OpTrainRandomForest(Operator):
    name = "TrainRandomForest"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1),InputSlot("Labels", level=1), InputSlot("fixClassifier", stype="bool")]
    outputSlots = [OutputSlot("Classifier")]
    
    logger = logging.getLogger(__name__+".OpTrainRandomForest")

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

    #FIXME: It is not possible to access the class variable logger here.
    #
    #@traceLogged(OpTrainRandomForest.logger, level=logging.INFO, msg="OpTrainRandomForest: Training Classifier")
    def execute(self, slot, subindex, roi, result):
        featMatrix=[]
        labelsMatrix=[]
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.meta.shape is not None:
                labels=labels[:].wait()

                indexes=numpy.nonzero(labels[...,0].view(numpy.ndarray))
                #Maybe later request only part of the region?

                image=self.inputs["Images"][i][:].wait()

                features=image[indexes]
                labels=labels[indexes]

                featMatrix.append(features)
                labelsMatrix.append(labels)


        featMatrix=numpy.concatenate(featMatrix,axis=0)
        labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)

        # train and store self._forest_count forests in parallel
        pool = RequestPool()
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

    inputSlots = [InputSlot("Images", level=1),InputSlot("Labels", level=1), \
                  InputSlot("nonzeroLabelBlocks", level=1), InputSlot("MaxLabel")]
    outputSlots = [OutputSlot("Classifier")]

    WarningEmitted = False
    
    logger = logging.getLogger(__name__+".OpTrainRandomForestBlocked")

    def __init__(self, *args, **kwargs):
        super(OpTrainRandomForestBlocked, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._forest_count = 10
        # TODO: Make treecount configurable via an InputSlot
        self._tree_count = 10
        self._forests = (None,) * self._forest_count

    def setupOutputs(self):
        self.outputs["Classifier"].meta.dtype = object
        self.outputs["Classifier"].meta.shape = (self._forest_count,)

    @traceLogged(logger, level=logging.DEBUG, msg="OpTrainRandomForestBlocked: Training Classifier")
    def execute(self, slot, subindex, roi, result):
        progress = 0
        self.progressSignal(progress)
        numImages = len(self.Images)

        featMatrix=[]
        labelsMatrix=[]
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
                    req.notify_finished(progressNotify)
                    req.submit()

                for ir, req in enumerate(reqlistlabels):
                    req.notify_finished(progressNotify)
                    req.submit()

                traceLogger.debug("Requests fired")

                for ir, req in enumerate(reqlistlabels):
                    traceLogger.debug("Waiting for a label block...")
                    labblock = req.wait()

                    traceLogger.debug("Waiting for an image block...")
                    image = reqlistfeat[ir].wait()

                    indexes=numpy.nonzero(labblock[...,0].view(numpy.ndarray))
                    
                    # Even though our input is supposed to be "nonzeroLabelBlocks"
                    #  users are allowed to give some all-zero blocks.
                    # If this block all zero, discard and continue with next block.
                    if len(indexes[0]) > 0:
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
            self.progressSignal(100)
        else:
            featMatrix=numpy.concatenate(featMatrix,axis=0)
            labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)
            maxLabel = self.MaxLabel.value
            labelList = range(1, maxLabel+1) if maxLabel > 0 else list()

            try:
                self.logger.debug("Learning %d random forests with %d trees each with vigra..." % (self._forest_count, self._tree_count))
                t = time.time()
                # train and store self._forest_count forests in parallel
                pool = RequestPool()

                for i in range(self._forest_count):
                    def train_and_store(number):
                        result[number] = vigra.learning.RandomForest(self._tree_count, labels=labelList)
                        result[number].learnRF( numpy.asarray(featMatrix, dtype=numpy.float32),
                                                numpy.asarray(labelsMatrix, dtype=numpy.uint32))
                    req = pool.request(partial(train_and_store, i))

                pool.wait()
                pool.clean()

                self.logger.debug("Learning %d random forests with %d trees each with vigra took %f sec." % \
                    (self._forest_count, self._tree_count, time.time()-t))
            except:
                self.logger.error( "ERROR: could not learn classifier" )
                self.logger.error( "featMatrix shape={}, max={}, dtype={}".format(featMatrix.shape, featMatrix.max(), featMatrix.dtype) )
                self.logger.error( "labelsMatrix shape={}, max={}, dtype={}".format(labelsMatrix.shape, labelsMatrix.max(), labelsMatrix.dtype ) )
                raise
            finally:
                self.progressSignal(100)

        self._forests = result
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.Classifier.setDirty()

class OpPredictRandomForest(Operator):
    name = "PredictRandomForest"
    description = "Predict on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Image"),InputSlot("Classifier"), InputSlot("LabelsCount")]
    outputSlots = [OutputSlot("PMaps")]
    
    logger = logging.getLogger(__name__+".OpPredictRandomForestBlocked")

    def __init__(self, *args, **kwargs):
        super( OpPredictRandomForest, self ).__init__(*args, **kwargs)

    def setupOutputs(self):
        nlabels = max(self.LabelsCount.value, 1) #we'll have at least 2 labels once we actually predict something
                                                #not setting it to 0 here is friendlier to possible downstream
                                                #ilastik operators, setting it to 2 causes errors in pixel classification
                                                #(live prediction doesn't work when only two labels are present)
        
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.axistags = copy.copy(self.Image.meta.axistags)
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)

    def execute(self, slot, subindex, roi, result):
        t1 = time.time()
        key = roi.toSlice()

        traceLogger.debug("OpPredictRandomForest: Requesting classifier. roi={}".format(roi))
        forests=self.inputs["Classifier"][:].wait()

        if forests is None or any(x is None for x in forests):
            # Training operator may return 'None' if there was no data to train with
            return numpy.zeros(numpy.subtract(roi.stop, roi.start), dtype=numpy.float32)[...]

        traceLogger.debug("OpPredictRandomForest: Got classifier")

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
        pool = RequestPool()

        for i,f in enumerate(forests):
            pool.add( Request(partial(predict_forest, i)) )

        pool.wait()
        pool.clean()

        prediction=numpy.dstack(predictions)
        prediction = numpy.average(prediction, axis=2)
        prediction.shape =  shape[:-1] + (forests[0].labelCount(),)

        # Copy only the prediction channels the client requested.
        result[...] = prediction[...,roi.start[-1]:roi.stop[-1]]
        
        t3 = time.time()

        self.logger.debug("predict roi=%r took %fseconds, actual RF time was %fs, feature time was %fs" % (key, t3-t1, t3-t2, t2-t1))
        
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.inputs["Classifier"]:
            self.logger.debug("classifier changed, setting dirty")
            self.outputs["PMaps"].setDirty()
        elif slot == self.inputs["Image"]:
            self.outputs["PMaps"].setDirty()


class OpSegmentation(Operator):
    name = "OpSegmentation"
    description = "displaying highest probability class for each pixel"

    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]
    
    logger = logging.getLogger(__name__+".OpSegmentation")

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
        img = self.inputs["Input"][rkey].wait()
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

    logger = logging.getLogger(__name__+".OpAreas")

    def setupOutputs(self):

        self.outputs["Areas"].meta.shape = (self.inputs["NumberOfChannels"].value,)

    def execute(self, slot, subindex, roi, result):
        img = self.inputs["Input"][:].wait()

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
