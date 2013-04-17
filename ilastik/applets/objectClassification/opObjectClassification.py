import numpy
import vigra
import warnings
import itertools

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List
from lazyflow.operators import OpValueCache
from lazyflow.request import Request, RequestPool, RequestLock
from functools import partial

from ilastik.utility import OperatorSubView, MultiLaneOperatorABC, OpMultiLaneWrapper
from ilastik.utility.mode import mode
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_suffix

from opWarning import OpWarning

MISSING_VALUE = 0

class OpObjectClassification(Operator, MultiLaneOperatorABC):
    name = "OpObjectClassification"
    category = "Top-level"

    ###############
    # Input slots #
    ###############
    BinaryImages = InputSlot(level=1) # for visualization
    RawImages = InputSlot(level=1) # for visualization
    SegmentationImages = InputSlot(level=1) #connected components
    ObjectFeatures = InputSlot(rtype=List, stype=Opaque, level=1)
    SelectedFeatures = InputSlot(rtype=List, stype=Opaque)
    LabelsAllowedFlags = InputSlot(stype='bool', level=1)
    LabelInputs = InputSlot(stype=Opaque, rtype=List, optional=True, level=1)

    ################
    # Output slots #
    ################
    NumLabels = OutputSlot()
    Classifier = OutputSlot()
    LabelImages = OutputSlot(level=1)
    Predictions = OutputSlot(level=1, stype=Opaque, rtype=List)
    Probabilities = OutputSlot(level=1, stype=Opaque, rtype=List)
    PredictionImages = OutputSlot(level=1) #Labels, by the majority vote
    PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    SegmentationImagesOut = OutputSlot(level=1) #input connected components
    BadObjects = OutputSlot(level=1, stype=Opaque, rtype=List)
    BadObjectImages = OutputSlot(level=1)

    # TODO: not actually used
    Eraser = OutputSlot()
    DeleteLabel = OutputSlot()
    
    # GUI-only (not part of the pipeline, but saved to the project)
    LabelNames = OutputSlot()
    LabelColors = OutputSlot()
    PmapColors = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)

        # internal operators
        opkwargs = dict(parent=self)
        self.opTrain = OpObjectTrain(parent=self)
        self.opPredict = OpMultiLaneWrapper(OpObjectPredict, **opkwargs)
        self.opLabelsToImage = OpMultiLaneWrapper(OpRelabelSegmentation, **opkwargs)
        self.opPredictionsToImage = OpMultiLaneWrapper(OpRelabelSegmentation, **opkwargs)
        self.opProbabilityChannelsToImage = OpMultiLaneWrapper(OpMultiRelabelSegmentation, **opkwargs)
        self.opBadObjectsToImage = OpMultiLaneWrapper(OpRelabelSegmentation, **opkwargs)

        self.classifier_cache = OpValueCache(parent=self)

        # connect inputs
        self.opTrain.inputs["Features"].connect(self.ObjectFeatures)
        self.opTrain.inputs['Labels'].connect(self.LabelInputs)
        self.opTrain.inputs['FixClassifier'].setValue(False)

        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        # Find the highest label in all the label images
        self.opMaxLabel = OpMaxLabel( parent=self, graph=self.graph)
        self.opMaxLabel.Inputs.connect( self.LabelInputs )

        self.opPredict.inputs["Features"].connect(self.ObjectFeatures)
        self.opPredict.inputs["Classifier"].connect(self.classifier_cache.outputs['Output'])
        self.opPredict.inputs["LabelsCount"].connect(self.opMaxLabel.Output)

        self.opLabelsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opLabelsToImage.inputs["ObjectMap"].connect(self.LabelInputs)
        self.opLabelsToImage.inputs["Features"].connect(self.ObjectFeatures)

        self.opPredictionsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opPredictionsToImage.inputs["ObjectMap"].connect(self.opPredict.Predictions)
        self.opPredictionsToImage.inputs["Features"].connect(self.ObjectFeatures)

        self.opProbabilityChannelsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opProbabilityChannelsToImage.inputs["ObjectMaps"].connect(self.opPredict.ProbabilityChannels)
        self.opProbabilityChannelsToImage.inputs["Features"].connect(self.ObjectFeatures)
        
        self.opBadObjectsToImage.inputs["Image"].connect(self.SegmentationImages)
        self.opBadObjectsToImage.inputs["ObjectMap"].connect(self.opPredict.BadObjects)
        self.opBadObjectsToImage.inputs["Features"].connect(self.ObjectFeatures)

        self.LabelNames.setValue( [] )
        self.LabelColors.setValue( [] )
        self.PmapColors.setValue( [] )

        # connect outputs
        self.NumLabels.connect( self.opMaxLabel.Output )
        self.LabelImages.connect(self.opLabelsToImage.Output)
        self.Predictions.connect(self.opPredict.Predictions)
        self.Probabilities.connect(self.opPredict.Probabilities)
        self.PredictionImages.connect(self.opPredictionsToImage.Output)
        self.PredictionProbabilityChannels.connect(self.opProbabilityChannelsToImage.Output)
        self.BadObjects.connect(self.opPredict.BadObjects)
        self.BadObjectImages.connect(self.opBadObjectsToImage.Output)
        
        self.Classifier.connect(self.classifier_cache.Output)

        self.SegmentationImagesOut.connect(self.SegmentationImages)

        self.Eraser.setValue(100)
        self.DeleteLabel.setValue(-1)

        self._labelBBoxes = []
        self._ambiguousLabels = []
        self._needLabelTransfer = False

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
        self.LabelInputs[imageIndex].meta.mapping_dtype = numpy.uint8
        self.LabelInputs[imageIndex].meta.axistags = None

        self._resetLabelInputs(imageIndex)

    def _resetLabelInputs(self, imageIndex, roi=None):
        labels = dict()
        for t in range(self.SegmentationImages[imageIndex].meta.shape[0]):
            #initialize, because volumina needs to reshape to use it as a datasink
            labels[t] = numpy.zeros((2,))
        self.LabelInputs[imageIndex].setValue(labels)

    def removeLabel(self, label):
        #remove this label from the inputs
        for islot, label_slot in enumerate(self.LabelInputs):
            cur_labels = label_slot.value
            nTimes = self.RawImages[islot].meta.shape[0]
            nLabels = len(self.LabelNames.value)
            for t in range(nTimes):
                label_values = cur_labels[t]
                label_values[label_values==label+1] = 0
                for nextLabel in range(label, nLabels):
                    label_values[label_values==nextLabel+1]=nextLabel
                

    def setupOutputs(self):
        super(OpObjectClassification, self).setupOutputs()
        pass

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot==self.SegmentationImages:
            self._ambiguousLabels[subindex[0]] = self.LabelInputs[subindex[0]].value
            self._needLabelTransfer = True


    def assignObjectLabel(self, imageIndex, coordinate, assignedLabel):
        """
        Update the assigned label of the object located at the given coordinate.
        Does nothing if no object resides at the given coordinate.
        """
        segmentationShape = self.SegmentationImagesOut[imageIndex].meta.shape
        assert len(coordinate) == len( segmentationShape ), "Coordinate: {} is has the wrong length for this image, which is of shape: {}".format( coordinate, segmentationShape )
        slicing = tuple(slice(i, i+1) for i in coordinate)
        arr = self.SegmentationImagesOut[imageIndex][slicing].wait()

        objIndex = arr.flat[0]
        if objIndex == 0: # background; FIXME: do not hardcode
            return
        timeCoord = coordinate[0]
        labelslot = self.LabelInputs[imageIndex]
        labelsdict = labelslot.value
        labels = labelsdict[timeCoord]

        nobjects = len(labels)
        if objIndex >= nobjects:
            newLabels = numpy.zeros((objIndex + 1),)
            newLabels[:nobjects] = labels[:]
            labels = newLabels
        labels[objIndex] = assignedLabel
        labelsdict[timeCoord] = labels
        labelslot.setValue(labelsdict)
        labelslot.setDirty([(timeCoord, objIndex)])

        #Fill the cache of label bounding boxes, if it was empty
        if len(self._labelBBoxes[imageIndex].keys())==0:
            #it's the first label for this image
            feats = self.ObjectFeatures[imageIndex]([timeCoord]).wait()

            #the bboxes should be the same for all channels
            mins = feats[timeCoord]["Coord<Minimum>"+default_features_suffix]
            maxs = feats[timeCoord]["Coord<Maximum>"+default_features_suffix]
            bboxes = dict()
            bboxes["Coord<Minimum>"]=mins
            bboxes["Coord<Maximum>"]=maxs
            self._labelBBoxes[imageIndex][timeCoord]=bboxes

    def triggerTransferLabels(self, imageIndex):
        if not self._needLabelTransfer:
            return None
        if not self.SegmentationImages[imageIndex].ready():
            return None
        if len(self._labelBBoxes[imageIndex].keys())==0:
            #we either don't have any labels or we just read the project from file
            #nothing to transfer
            self._needLabelTransfer = False
            return None

        labels = dict()
        for timeCoord in range(self.SegmentationImages[imageIndex].meta.shape[0]):
            #we have to get new object features to get bounding boxes
            print "Transferring labels to the new segmentation. This might take a while..."
            new_feats = self.ObjectFeatures[imageIndex]([timeCoord]).wait()
            coords = dict()
            coords["Coord<Minimum>"]=new_feats[timeCoord]["Coord<Minimum>"+default_features_suffix]
            coords["Coord<Maximum>"]=new_feats[timeCoord]["Coord<Maximum>"+default_features_suffix]
            #FIXME: pass axistags
            new_labels, old_labels_lost, new_labels_lost = self.transferLabels(self._ambiguousLabels[imageIndex][timeCoord], \
                                             self._labelBBoxes[imageIndex][timeCoord], \
                                            coords)
            labels[timeCoord] = new_labels

            self._labelBBoxes[imageIndex][timeCoord]=coords
            self._ambiguousLabels[imageIndex][timeCoord]=numpy.zeros((2,)) #initialize ambig. labels as normal labels

        self.LabelInputs[imageIndex].setValue(labels)
        self._needLabelTransfer = False

        return new_labels, old_labels_lost, new_labels_lost

    @staticmethod
    def transferLabels(old_labels, old_bboxes, new_bboxes, axistags = None):
        #transfer labels from old segmentation to new segmentation

        mins_old = old_bboxes["Coord<Minimum>"]
        maxs_old = old_bboxes["Coord<Maximum>"]
        mins_new = new_bboxes["Coord<Minimum>"]
        maxs_new = new_bboxes["Coord<Maximum>"]
        nobj_old = mins_old.shape[0]
        nobj_new = mins_new.shape[0]
        if axistags is None:
            axistags = "xyz"
        class bbox():
            def __init__(self, minmaxs, axistags):
                self.xmin = minmaxs[0][axistags.index('x')]
                self.ymin = minmaxs[0][axistags.index('y')]
                self.zmin = minmaxs[0][axistags.index('z')]
                self.xmax = minmaxs[1][axistags.index('x')]
                self.ymax = minmaxs[1][axistags.index('y')]
                self.zmax = minmaxs[1][axistags.index('z')]
                self.rad_x = 0.5*(self.xmax - self.xmin)
                self.cent_x = self.xmin+self.rad_x
                self.rad_y = 0.5*(self.ymax-self.ymin)
                self.cent_y = self.ymin+self.rad_y
                self.rad_z = 0.5*(self.zmax-self.zmin)
                self.cent_z = self.zmin+self.rad_z

            @staticmethod
            def overlap(bbox_tuple):
                this = bbox_tuple[0]
                that = bbox_tuple[1]
                over_x = this.rad_x+that.rad_x - (abs(this.cent_x-that.cent_x))
                over_y = this.rad_y+that.rad_y - (abs(this.cent_y-that.cent_y))
                over_z = this.rad_z+that.rad_z - (abs(this.cent_z-that.cent_z))

                if over_x>0 and over_y>0 and over_z>0:
                    return over_x*over_y*over_z
                return 0

        nonzeros = numpy.nonzero(old_labels)[0]
        bboxes_old = [bbox(x, axistags) for x in zip(mins_old[nonzeros], maxs_old[nonzeros])]
        bboxes_new = [bbox(x, axistags) for x in zip(mins_new, maxs_new)]

        #remove background
        #FIXME: assuming background is 0 again
        bboxes_new = bboxes_new[1:]

        double_for_loop = itertools.product(bboxes_old, bboxes_new)
        overlaps = map(bbox.overlap, double_for_loop)

        overlaps = numpy.asarray(overlaps)
        overlaps = overlaps.reshape((len(bboxes_old), len(bboxes_new)))
        new_labels = numpy.zeros((nobj_new,), dtype=numpy.uint32)
        old_labels_lost = dict()
        old_labels_lost["full"]=[]
        old_labels_lost["partial"]=[]
        new_labels_lost = dict()
        new_labels_lost["conflict"]=[]
        for iobj in range(overlaps.shape[0]):
            #take the object with maximum overlap
            overlapsum = numpy.sum(overlaps[iobj, :])
            if overlapsum==0:
                old_labels_lost["full"].append((bboxes_old[iobj].cent_x, bboxes_old[iobj].cent_y, bboxes_old[iobj].cent_z))
                continue
            newindex = numpy.argmax(overlaps[iobj, :])
            if overlapsum-overlaps[iobj,newindex]>0:
                #this object overlaps with more than one new object
                old_labels_lost["partial"].append((bboxes_old[iobj].cent_x, bboxes_old[iobj].cent_y, bboxes_old[iobj].cent_z))

            overlaps[iobj, :] = 0
            overlaps[iobj, newindex] = 1 #doesn't matter what number>0

        for iobj in range(overlaps.shape[1]):
            labels = numpy.where(overlaps[:, iobj]>0)[0]
            if labels.shape[0]==1:
                new_labels[iobj+1]=old_labels[nonzeros[labels[0]]] #iobj+1 because of the background
            elif labels.shape[0]>1:
                new_labels_lost["conflict"].append((bboxes_new[iobj].cent_x, bboxes_new[iobj].cent_y, bboxes_new[iobj].cent_z))

        new_labels = new_labels
        new_labels[0]=0 #FIXME: hardcoded background value again
        return new_labels, old_labels_lost, new_labels_lost


    def addLane(self, laneIndex):
        numLanes = len(self.SegmentationImages)
        assert numLanes == laneIndex, "Image lanes must be appended."
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == laneIndex:
                slot.resize(numLanes + 1)

        self._ambiguousLabels.insert(laneIndex, None)
        self._labelBBoxes.insert(laneIndex, dict())

    def removeLane(self, laneIndex, finalLength):
        for slot in self.inputs.values():
            if slot.level > 0 and len(slot) == finalLength + 1:
                slot.removeSlot(laneIndex, finalLength)

        self._ambiguousLabels.pop(laneIndex)
        self._labelBBoxes.pop(laneIndex)

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


def make_feature_array(feats, labels=None):
    featlist = []
    labellist = []
    featnames = feats.values()[0].keys()

    # remove extra features used by applet only.
    featnames = sorted(list(n for n in featnames
                            if default_features_suffix not in n))
    col_names = []

    for t in sorted(feats.keys()):
        featsMatrix_tmp = []

        if labels is not None:
            labellist_tmp = []
            lab = labels[t].squeeze()
            index = numpy.nonzero(lab)
            labellist_tmp.append(lab[index])

        for featname in featnames:
            value = feats[t][featname]
            ft = numpy.asarray(value.squeeze())
            if labels is not None:
                ft = ft[index]
            featsMatrix_tmp.append(ft)
            col_names.extend([featname] * value.shape[1])

        #FIXME: we can do it all with just arrays
        featsMatrix_tmp_combined = _concatenate(featsMatrix_tmp, axis=1)
        featlist.append(featsMatrix_tmp_combined)
        if labels is not None:
            labellist_tmp_combined = _concatenate(labellist_tmp, axis=1)
            labellist.append(labellist_tmp_combined)

    featMatrix = _concatenate(featlist, axis=0)

    if labels is not None:
        labelsMatrix = _concatenate(labellist, axis=0)
        assert labelsMatrix.shape[0] == featMatrix.shape[0]
        return featMatrix, col_names, labelsMatrix
    return featMatrix, col_names

def replace_missing(a):
    rows, cols = numpy.where(numpy.isnan(a) + numpy.isinf(a))
    idx = (rows, cols)
    rows = list(set(rows.flat))
    cols = list(set(cols.flat))
    a[idx] = MISSING_VALUE
    return rows, cols



def warn_bad(op, rows, cols, col_names, t):
    badfeats = set(col_names[c] for c in cols)
    if len(rows) > 0:
        op.setWarning(title='Warning', description='Encountered objects with bad features!', details="{}".format(rows))
    if len(badfeats) > 0:
        op.setWarning(title='Warning', description='Encountered features with bad values!', details="{}".format(sorted(badfeats)))
        
    return badfeats
    
class OpObjectTrain(OpWarning):
    name = "TrainRandomForestObjects"
    description = "Train a random forest on multiple images"
    category = "Learning"

    Labels = InputSlot(level=1, stype=Opaque, rtype=List)
    Features = InputSlot(level=1, rtype=List, stype=Opaque)
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
        
        # needed for OpWarning    
        super(OpObjectTrain, self).setupOutputs()

    def execute(self, slot, subindex, roi, result):

        featList = []
        all_col_names = []
        labelsList = []

        # TODO: make these available in the GUI.
        all_bad_objects = {}
        all_bad_feats = set()

        for i in range(len(self.Labels)):
            feats = self.Features[i]([]).wait()

            # TODO: we should be able to use self.Labels[i].value,
            # but the current implementation of Slot.value() does not
            # do the right thing.
            labels = self.Labels[i]([]).wait()

            featstmp, col_names, labelstmp = make_feature_array(feats, labels)
            if featstmp.size == 0:
                # nothing to do if there are no labels in this image.
                assert labelstmp.size == 0
                continue

            rows, cols = replace_missing(featstmp)
            badfeats = warn_bad(self, rows, cols, col_names, i)

            featList.append(featstmp)
            all_col_names.append(tuple(col_names))
            labelsList.append(labelstmp)

            all_bad_objects[i] = rows
            all_bad_feats = all_bad_feats.union(badfeats)

        if not len(set(all_col_names)) == 1:
            raise Exception('different time slices did not have same features.')

        featMatrix = _concatenate(featList, axis=0)
        labelsMatrix = _concatenate(labelsList, axis=0)

        print "training on matrix of shape {}".format(featMatrix.shape)

        if featMatrix.size == 0 or labelsMatrix.size == 0:
            result[:] = None
            return
        oob = [0] * self.ForestCount.value
        try:
            # train and store forests in parallel
            pool = RequestPool()
            for i in range(self.ForestCount.value):
                def train_and_store(number):
                    result[number] = vigra.learning.RandomForest(self._tree_count)
                    oob[number] = result[number].learnRF(featMatrix.astype(numpy.float32), numpy.asarray(labelsMatrix, dtype=numpy.uint32))
                    print "intermediate oob:", oob[number]
                req = Request( partial(train_and_store, i) )
                pool.add( req )
            pool.wait()
            pool.clean()
        except:
            print ("couldn't learn classifier")
            raise
        oob_total = numpy.mean(oob)
        print "training finished, out of bag error:", oob_total
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.FixClassifier and \
           self.inputs["FixClassifier"].value == False:
            slcs = (slice(0, self.ForestCount.value, None),)
            self.outputs["Classifier"].setDirty(slcs)


class OpObjectPredict(OpWarning):
    # WARNING: right now we predict and cache a whole time slice. We
    # expect this to be fast because there are relatively few objects
    # compared to the number of pixels in pixel classification. If
    # this should be too slow, we should instead cache at the object
    # level, and only predict for objects visible in the roi.

    name = "OpObjectPredict"

    Features = InputSlot(rtype=List, stype=Opaque)
    Classifier = InputSlot()
    LabelsCount = InputSlot(stype='integer')

    Predictions = OutputSlot(stype=Opaque, rtype=List)
    Probabilities = OutputSlot(stype=Opaque, rtype=List)
    ProbabilityChannels = OutputSlot(stype=Opaque, rtype=List, level=1)
    BadObjects = OutputSlot(stype=Opaque, rtype=List)

    #SegmentationThreshold = 0.5

    def setupOutputs(self):
        self.Predictions.meta.shape = self.Features.meta.shape
        self.Predictions.meta.dtype = object
        self.Predictions.meta.axistags = None
        self.Predictions.meta.mapping_dtype = numpy.uint8

        self.Probabilities.meta.shape = self.Features.meta.shape
        self.Probabilities.meta.dtype = object
        self.Probabilities.meta.mapping_dtype = numpy.float32
        self.Probabilities.meta.axistags = None
        
        self.BadObjects.meta.shape = self.Features.meta.shape
        self.BadObjects.meta.dtype = object
        self.BadObjects.meta.mapping_dtype = numpy.uint8
        self.BadObjects.meta.axistags = None

        if self.LabelsCount.ready():
            nlabels = self.LabelsCount[:].wait()
            nlabels = int(nlabels[0])
            self.ProbabilityChannels.resize(nlabels)
            for oslot in self.ProbabilityChannels:
                oslot.meta.shape = self.Features.meta.shape
                oslot.meta.dtype = object
                oslot.meta.axistags = None
                oslot.meta.mapping_dtype = numpy.float32

        self.lock = RequestLock()
        self.prob_cache = dict()
        self.bad_objects = dict()
        
        # needed for OpWarning
        super(OpObjectPredict, self).setupOutputs()

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Predictions or slot == self.Probabilities or slot == self.ProbabilityChannels or slot==self.BadObjects

        times = roi._l
        if len(times) == 0:
            # we assume that 0-length requests are requesting everything
            times = range(self.Predictions.meta.shape[0])

        forests=self.inputs["Classifier"][:].wait()
        if forests is None or forests[0] is None:
            # this happens if there was no data to train with
            return dict((t, numpy.array([])) for t in times)

        feats = {}
        prob_predictions = {}

        # FIXME: self.prob_cache is shared, so we need to block.
        # However, this makes prediction single-threaded.
        self.lock.acquire()
        try:
            for t in times:
                if t in self.prob_cache:
                    continue

                tmpfeats = self.Features([t]).wait()
                ftmatrix, col_names = make_feature_array(tmpfeats)
                rows, cols = replace_missing(ftmatrix)
                self.bad_objects[t] = numpy.zeros((ftmatrix.shape[0],))
                self.bad_objects[t][rows] = 1
                warn_bad(self, rows, cols, col_names, t)
                feats[t] = ftmatrix
                prob_predictions[t] = [0] * len(forests)

            def predict_forest(_t, forest_index):
                # Note: We can't use RandomForest.predictLabels() here because we're training in parallel,
                #        and we have to average the PROBABILITIES from all forests.
                #       Averaging the label predictions from each forest is NOT equivalent.
                #       For details please see wikipedia:
                #       http://en.wikipedia.org/wiki/Electoral_College_%28United_States%29#Irrelevancy_of_national_popular_vote
                #       (^-^)
                prob_predictions[_t][forest_index] = forests[forest_index].predictProbabilities(feats[_t].astype(numpy.float32))

            # predict the data with all the forests in parallel
            pool = RequestPool()
            for t in times:
                if t in self.prob_cache:
                    continue
                for i, f in enumerate(forests):
                    req = Request( partial(predict_forest, t, i) )
                    pool.add(req)

            pool.wait()
            pool.clean()

            for t in times:
                if t not in self.prob_cache:
                    # prob_predictions is a dict-of-lists-of-arrays, indexed as follows:
                    # prob_predictions[t][forest_index][object_index, class_index]

                    # Stack the forests together and average them.
                    stacked_predictions = numpy.array( prob_predictions[t] )
                    averaged_predictions = numpy.average( stacked_predictions, axis=0 )
                    assert averaged_predictions.shape[0] == len(feats[t])
                    self.prob_cache[t] = averaged_predictions

                    self.prob_cache[t][0] = 0 # Background probability is always zero


            if slot == self.Probabilities:
                return { t : self.prob_cache[t] for t in times }
            elif slot == self.Predictions:
                # FIXME: Support SegmentationThreshold again...
                labels = dict()
                for t in times:
                    prob_sum = numpy.sum(self.prob_cache[t], axis=1)
                    labels[t] = 1 + numpy.argmax(self.prob_cache[t], axis=1)
                    labels[t][0] = 0 # Background gets the zero label
                return labels

            elif slot == self.ProbabilityChannels:
                prob_single_channel = {t: self.prob_cache[t][:, subindex[0]] for t in times}
                return prob_single_channel
            
            elif slot == self.BadObjects:
                return { t : self.bad_objects[t] for t in times }

            else:
                assert False, "Unknown input slot"
        finally:
            self.lock.release()

    def propagateDirty(self, slot, subindex, roi):
        self.prob_cache = dict()
        self.Predictions.setDirty(())
        self.Probabilities.setDirty(())
        self.ProbabilityChannels.setDirty(())


class OpRelabelSegmentation(Operator):
    """Takes a segmentation image and a mapping and returns the
    mapped image.

    For instance, map prediction labels onto objects.

    """
    name = "OpToImage"
    Image = InputSlot()
    ObjectMap = InputSlot(stype=Opaque, rtype=List)
    Features = InputSlot(rtype=List, stype=Opaque) #this is needed to limit dirty propagation to the object bbox
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Image.meta)
        self.Output.meta.dtype = self.ObjectMap.meta.mapping_dtype

    def execute(self, slot, subindex, roi, result):
        img = self.Image(roi.start, roi.stop).wait()
        for t in range(roi.start[0], roi.stop[0]):
            map_ = self.ObjectMap([t]).wait()
            tmap = map_[t]
            # FIXME: necessary because predictions are returned
            # enclosed in a list.
            if isinstance(tmap, list):
                tmap = tmap[0]

            tmap = tmap.squeeze()

            warnings.warn("FIXME: This should be cached (and reset when the input becomes dirty)")
            idx = img.max()
            if len(tmap) <= idx:
                newTmap = numpy.zeros((idx + 1,)) # And maybe this should be cached, too?
                newTmap[:len(tmap)] = tmap[:]
                tmap = newTmap

            result[t-roi.start[0]] = tmap[img[t-roi.start[0]]]

        return result

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
                    min_coords = feats[t]['Coord<Minimum>' + default_features_suffix][obj]
                    max_coords = feats[t]['Coord<Maximum>' + default_features_suffix][obj]
                    slcs = list(slice(*args) for args in zip(min_coords, max_coords))
                    slcs = [slice(t, t+1),] + slcs + [slice(None),]
                    self.Output.setDirty(slcs)

class OpMultiRelabelSegmentation(Operator):
    """Takes a segmentation image and multiple mappings and returns the
    mapped images.

    For instance, map prediction probabilities for different classes onto objects.

    """
    name = "OpToImageMulti"
    Image = InputSlot()
    ObjectMaps = InputSlot(stype=Opaque, rtype=List, level=1)
    Features = InputSlot(rtype=List, stype=Opaque) #this is needed to limit dirty propagation to the object bbox
    Output = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpMultiRelabelSegmentation, self).__init__(*args, **kwargs)
        self._innerOperators = []

    def setupOutputs(self):
        nmaps = len(self.ObjectMaps)
        for islot in self.ObjectMaps:
            op = OpRelabelSegmentation(parent=self)
            op.Image.connect(self.Image)
            op.ObjectMap.connect(islot)
            op.Features.connect(self.Features)
            self._innerOperators.append(op)
        self.Output.resize(nmaps)
        for i, oslot in enumerate(self.Output):
            oslot.connect(self._innerOperators[i].Output)

    def propagateDirty(self, slot, subindex, roi):
        pass

class OpMaxLabel(Operator):
    """ Finds the maximum label value in the input labels
        More or less copied from opPixelClassification::OpMaxValue
    """
    name = "OpMaxLabel"
    Inputs = InputSlot(level=1, stype=Opaque)
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMaxLabel, self).__init__(*args, **kwargs)
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self._output = 0 #internal cache


    def setupOutputs(self):
        self.updateOutput()
        self.Output.setValue(self._output)

    def execute(self, slot, subindex, roi, result):
        result[0] = self._output
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.updateOutput()
        self.Output.setValue(self._output)

    def updateOutput(self):
        # Return the max value of all our inputs
        maxValue = None
        for i, inputSubSlot in enumerate(self.Inputs):
            # Only use inputs that are actually configured
            if inputSubSlot.ready():
                subSlotMax = numpy.max(inputSubSlot.value)
                #subSlotMax = 0
                #print inputSubSlot.value
                #for label_array in inputSubSlot.value.items():
                #    localMax = numpy.max(label_array)
                #    subSlotMax = max(subSlotMax, localMax)

                if maxValue is None:
                    maxValue = subSlotMax
                else:
                    maxValue = max(maxValue, subSlotMax)

        self._output = maxValue
