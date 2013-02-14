import numpy
import h5py
import vigra
import vigra.analysis
import copy
from collections import defaultdict

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OperatorWrapper, OpBlockedSparseLabelArray, OpValueCache, \
OpMultiArraySlicer2, OpSlicedBlockedArrayCache, OpPrecomputedInput
from lazyflow.request import Request, Pool
from functools import partial

from ilastik.applets.pixelClassification.opPixelClassification import OpShapeReader, OpMaxValue
from ilastik.utility import OperatorSubView, MultiLaneOperatorABC, OpMultiLaneWrapper
from ilastik.utility.mode import mode

# Right now we only support having two types of objects.
_MAXLABELS = 2

# Features that are uninformative for classification purposes, but
# calculated for other reasons.
BLACKLIST_FEATS = ['RegionCenter',
                 'Coord<Minimum>',
                 'Coord<Maximum>',
                 'Coord<PowerSum<1>>',
                 'Coord<ArgMaxWeight>',
                 # FIXME: duplicate features with space before '>'
                 'Coord<Minimum >',
                 'Coord<Maximum >',
                 'Coord<PowerSum<1> >',
                 'Coord<ArgMaxWeight >',
]

WHITELIST_FEATS = ['Mean', 'Variance']

# WARNING: since we assume the input image is binary, we also assume
# that it only has one channel. If there are multiple channels, only
# features from the first channel are used in this operater.

class OpObjectClassification(Operator, MultiLaneOperatorABC):
    name = "OpObjectClassification"
    category = "Top-level"

    ###############
    # Input slots #
    ###############
    BinaryImages = InputSlot(level=1) # for visualization
    RawImages = InputSlot(level=1) # for visualization
    SegmentationImages = InputSlot(level=1)
    ObjectFeatures = InputSlot(rtype=List, level=1)
    LabelsAllowedFlags = InputSlot(stype='bool', level=1)
    LabelInputs = InputSlot(stype=Opaque, rtype=List, optional=True, level=1)
    FreezePredictions = InputSlot(stype='bool')

    ################
    # Output slots #
    ################
    NumLabels = OutputSlot()
    Classifier = OutputSlot()
    LabelImages = OutputSlot(level=1)
    PredictionImages = OutputSlot(level=1)
    SegmentationImagesOut = OutputSlot(level=1)

    # TODO: not actually used
    Eraser = OutputSlot()
    DeleteLabel = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)

        # internal operators
        opkwargs = dict(parent=self)
        self.opInputShapeReader = OpMultiLaneWrapper(OpShapeReader, **opkwargs)
        self.opTrain = OpObjectTrain(parent=self)
        self.opPredict = OpMultiLaneWrapper(OpObjectPredict, **opkwargs)
        self.opLabelsToImage = OpMultiLaneWrapper(OpToImage, **opkwargs)
        self.opPredictionsToImage = OpMultiLaneWrapper(OpToImage, **opkwargs)

        self.classifier_cache = OpValueCache(parent=self)

        # connect inputs
        self.opInputShapeReader.Input.connect(self.SegmentationImages)

        self.opTrain.inputs["Features"].connect(self.ObjectFeatures)
        self.opTrain.inputs['Labels'].connect(self.LabelInputs)
        self.opTrain.inputs['FixClassifier'].setValue(False)

        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        self.opPredict.inputs["Features"].connect(self.ObjectFeatures)
        self.opPredict.inputs["Classifier"].connect(self.classifier_cache.outputs['Output'])
        self.opPredict.inputs["LabelsCount"].setValue(_MAXLABELS)

        self.opLabelsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opLabelsToImage.inputs["ObjectMap"].connect(self.LabelInputs)
        self.opLabelsToImage.inputs["Features"].connect(self.ObjectFeatures)

        self.opPredictionsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opPredictionsToImage.inputs["ObjectMap"].connect(self.opPredict.Predictions)
        self.opPredictionsToImage.inputs["Features"].connect(self.ObjectFeatures)

        # connect outputs
        self.NumLabels.setValue(_MAXLABELS)
        self.LabelImages.connect(self.opLabelsToImage.Output)
        self.PredictionImages.connect(self.opPredictionsToImage.Output)
        self.Classifier.connect(self.opTrain.Classifier)

        self.SegmentationImagesOut.connect(self.SegmentationImages)

        self.Eraser.setValue(100)
        self.DeleteLabel.setValue(-1)

        def handleNewInputImage(multislot, index, *args):
            def handleInputReady(slot):
                self.setupCaches(multislot.index(slot))
            multislot[index].notifyReady(handleInputReady)

        self.SegmentationImages.notifyInserted(handleNewInputImage)

    def setupCaches(self, imageIndex):
        """Setup the label input to correct dimensions"""
        numImages=len(self.SegmentationImages)
        self.LabelInputs.resize(numImages)
        self.LabelInputs[imageIndex].meta.shape = (1,)
        self.LabelInputs[imageIndex].meta.dtype = object
        self.LabelInputs[imageIndex].meta.axistags = None
        self._resetLabelInputs(imageIndex)

    def _resetLabelInputs(self, imageIndex, roi=None):
        labels = dict()
        for t in range(self.SegmentationImages[imageIndex].meta.shape[0]):
            labels[t] = numpy.zeros((2,))
        self.LabelInputs[imageIndex].setValue(labels)

    def setupOutputs(self):
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass

    def addLane(self, laneIndex):
        numLanes = len(self.SegmentationImages)
        assert numLanes == laneIndex, "Image lanes must be appended."
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == laneIndex:
                slot.resize(numLanes + 1)

    def removeLane(self, laneIndex, finalLength):
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == finalLength + 1:
                slot.removeSlot(laneIndex, finalLength)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)


def _atleast_nd(a, ndim):
    """Like numpy.atleast_1d and friends, but supports arbitrary ndim,
    always puts extra dimensions last, and resizes.

    """
    if ndim < a.ndim:
        return
    nnew = ndim - a.ndim
    newshape = tuple(list(a.shape) + [1] * nnew)
    a.resize(newshape)


def _concatenate(arrays, axis):
    """wrapper to numpy.concatenate that resizes arrays first."""
    arrays = list(a for a in arrays if 0 not in a.shape)
    if len(arrays) == 0:
        return numpy.array([])
    maxd = max(max(a.ndim for a in arrays), 2)
    for a in arrays:
        _atleast_nd(a, maxd)
    return numpy.concatenate(arrays, axis=axis)


class OpObjectTrain(Operator):
    name = "TrainRandomForestObjects"
    description = "Train a random forest on multiple images"
    category = "Learning"

    Labels = InputSlot(level=1, stype=Opaque, rtype=List)
    Features = InputSlot(level=1, rtype=List)
    FixClassifier = InputSlot(stype="bool")
    ForestCount = InputSlot(stype="int", value=1)

    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectTrain, self).__init__(*args, **kwargs)
        self._tree_count = 100
        self.FixClassifier.setValue(False)

    def setupOutputs(self):
        if self.inputs["FixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self.ForestCount.value,)
            self.outputs["Classifier"].meta.axistags = None

    def execute(self, slot, subindex, roi, result):

        featMatrix = []
        labelsMatrix = []

        for i in range(len(self.Labels)):
            feats = self.Features[i]([]).wait()

            # TODO: we should be able to use self.Labels[i].value,
            # but the current implementation of Slot.value() does not
            # do the right thing.
            labels = self.Labels[i]([]).wait()

            for t in feats:
                featsMatrix_tmp = []
                labelsMatrix_tmp = []
                lab = labels[t].squeeze()
                index = numpy.nonzero(lab)
                labelsMatrix_tmp.append(lab[index])

                for key, value in feats[t][0].iteritems():
                    if not key in WHITELIST_FEATS:
                        continue
                    ft = numpy.asarray(value.squeeze())
                    featsMatrix_tmp.append(ft[index])

                featMatrix.append(_concatenate(featsMatrix_tmp, axis=1))
                labelsMatrix.append(_concatenate(labelsMatrix_tmp, axis=1))

        if len(featMatrix) == 0 or len(labelsMatrix) == 0:
            result[:] = None
        else:
            featMatrix = _concatenate(featMatrix, axis=0)
            labelsMatrix = _concatenate(labelsMatrix, axis=0)

            try:
                # train and store forests in parallel
                pool = Pool()
                for i in range(self.ForestCount.value):
                    def train_and_store(number):
                        result[number] = vigra.learning.RandomForest(self._tree_count)
                        result[number].learnRF(featMatrix.astype(numpy.float32),
                                               labelsMatrix.astype(numpy.uint32))
                    req = pool.request(partial(train_and_store, i))
                pool.wait()
                pool.clean()
            except:
                print ("couldn't learn classifier")
                raise

        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.FixClassifier and \
           self.inputs["FixClassifier"].value == False:
            slcs = (slice(0, self.ForestCount.value, None),)
            self.outputs["Classifier"].setDirty(slcs)


class OpObjectPredict(Operator):
    # WARNING: right now we predict and cache a whole time slice. We
    # expect this to be fast because there are relatively few objects
    # compared to the number of pixels in pixel classification. If
    # this should be too slow, we should instead cache at the object
    # level, and only predict for objects visible in the roi.

    name = "OpObjectPredict"

    Features = InputSlot(rtype=List)
    LabelsCount = InputSlot(stype='integer')
    Classifier = InputSlot()

    Predictions = OutputSlot(stype=Opaque, rtype=List)

    def setupOutputs(self):
        self.Predictions.meta.shape = self.Features.meta.shape
        self.Predictions.meta.dtype = object
        self.Predictions.meta.axistags = None

        self.cache = dict()

    def execute(self, slot, subindex, roi, result):
        forests=self.inputs["Classifier"][:].wait()

        if forests is None:
            # this happens if there was no data to train with
            return numpy.zeros(numpy.subtract(roi.stop, roi.start),
                               dtype=numpy.float32)[...]
        feats = {}
        predictions = {}
        for t in roi._l:
            if t in self.cache:
                continue

            ftsMatrix = []
            for key, value in self.Features([t]).wait()[t][0].iteritems():
                if not key in WHITELIST_FEATS:
                    continue
                tmpfts = numpy.asarray(value).astype(numpy.float32)
                _atleast_nd(tmpfts, 2)
                ftsMatrix.append(tmpfts)

            feats[t] = _concatenate(ftsMatrix, axis=1)
            predictions[t]  = [0] * len(forests)

        def predict_forest(t, number):
            predictions[t][number] = forests[number].predictLabels(feats[t]).reshape(1, -1)

        # predict the data with all the forests in parallel
        pool = Pool()

        for t in roi._l:
            if t in self.cache:
                continue
            for i, f in enumerate(forests):
                req = pool.request(partial(predict_forest, t, i))

        pool.wait()
        pool.clean()

        final_predictions = dict()

        for t in roi._l:
            if t not in self.cache:
                # shape (ForestCount, number of objects)
                prediction = numpy.vstack(predictions[t])

                # take mode of each column
                m, _ = mode(prediction, axis=0)
                m = m.squeeze()
                assert m.ndim == 1
                m[0] = 0
                self.cache[t] = m
            final_predictions[t] = self.cache[t]

        return final_predictions

    def propagateDirty(self, slot, subindex, roi):
        self.cache = dict()
        self.Predictions.setDirty(())


class OpToImage(Operator):
    """Takes a segmentation image and a mapping and returns the
    mapped image.

    For instance, map prediction labels onto objects.

    """
    name = "OpToImage"
    Image = InputSlot()
    ObjectMap = InputSlot(stype=Opaque, rtype=List)
    Features = InputSlot(rtype=List)
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Image.meta)

    def execute(self, slot, subindex, roi, result):
        slc = roi.toSlice()
        img = self.Image[slc].wait()

        for t in range(roi.start[0], roi.stop[0]):
            map_ = self.ObjectMap([t]).wait()
            tmap = map_[t]

            # FIXME: necessary because predictions are returned
            # enclosed in a list.
            if isinstance(tmap, list):
                tmap = tmap[0]

            tmap = tmap.squeeze()

            idx = img.max()
            if len(tmap) <= idx:
                newTmap = numpy.zeros((idx + 1,))
                newTmap[:len(tmap)] = tmap[:]
                tmap = newTmap

            img[t] = tmap[img[t]]

        return img

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Image:
            self.Output.setDirty(roi)

        elif slot is self.ObjectMap or slot is self.Features:
            # this is hacky. the gui's onClick() function calls
            # setDirty with a (time, object) pair, while elsewhere we
            # call setDirty with ().
            if len(roi._l) == 0:
                self.Output.setDirty(slice(None))
            elif isinstance(roi._l[0], int):
                for t in roi._l:
                    self.Output.setDirty(slice(t))
            else:
                assert len(roi._l[0]) == 2
                # for each dirty object, only set its bounding box dirty
                ts = list(set(t for t, _ in roi._l))
                feats = self.Features(ts).wait()
                for t, obj in roi._l:
                    try:
                        min_coords = feats[t][0]['Coord<Minimum>'][obj]
                        max_coords = feats[t][0]['Coord<Maximum>'][obj]
                    except KeyError:
                        min_coords = feats[t][0]['Coord<Minimum >'][obj]
                        max_coords = feats[t][0]['Coord<Maximum >'][obj]
                    slcs = list(slice(*args) for args in zip(min_coords, max_coords))
                    slcs = [slice(t, t+1),] + slcs + [slice(None),]
                    self.Output.setDirty(slcs)
