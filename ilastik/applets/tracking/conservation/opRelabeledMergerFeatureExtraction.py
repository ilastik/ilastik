from builtins import range
import numpy as np
import math
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion, List
from lazyflow.roi import roiToSlice
from ilastik.applets.objectExtraction.opObjectExtraction import OpRegionFeatures,\
    default_features_key, OpAdaptTimeListRoi
from ilastik.applets.trackingFeatureExtraction import config

import logging
from ilastik.applets.base.applet import DatasetConstraintError
logger = logging.getLogger(__name__)

class OpDifference(Operator):
    """
    Returns the value of ImageB in those places where both images differ,
    zero everywhere else.
    """
    name = "Difference"

    ImageA = InputSlot()
    ImageB = InputSlot()

    Output = OutputSlot()

    def __init__(self, parent):
        super(OpDifference, self).__init__(parent)

        self.ImageA.notifyReady(self._checkConstraints)
        self.ImageB.notifyReady(self._checkConstraints)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.ImageB.meta)

    def _checkConstraints(self, *args):
        if self.ImageA.ready() and self.ImageB.ready():
            shapeA = self.ImageA.meta.getTaggedShape()
            shapeB = self.ImageB.meta.getTaggedShape()

            if shapeA != shapeB:
                raise DatasetConstraintError("Label Image Difference",
                                             "Cannot compute difference of images with different shapes")

    def execute(self, slot, subindex, roi, result):
        if slot == self.Output:
            imageA = self.ImageA.get(roi).wait()
            self.ImageB.get(roi).writeInto(result).wait()

            result[result == imageA] = 0  # only differing indices are of interest
            return result

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.ImageA or inputSlot is self.ImageB:
            self.Output.setDirty(roi)

    def setInSlot(self, slot, subindex, roi, value):
        assert False, "OpDifference does not allow setInSlot()"

class OpZeroBasedConsecutiveIndexRelabeling(Operator):
    """
    To be able to compute vigra region features on a label image,
    it must contain zero based consecutive indexes. This operator
    provides a relabeled ROI of the image and the respective mapping as output.
    """
    name = "Zero Based Consecutive Index Relabeling"

    LabelImage = InputSlot()

    Output = OutputSlot()
    Mapping = OutputSlot(rtype=List, stype=Opaque)

    def __init__(self, parent):
        super(OpZeroBasedConsecutiveIndexRelabeling, self).__init__(parent)
        self._mapping = {}

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.LabelImage.meta)

    def _updateMapping(self, roi, t):
        labelImage = self.LabelImage.get(roi).wait()
        labels = list(np.sort(vigra.analysis.unique(labelImage)))
        # if 0 not in labels:
        #     labels = [0, ] + labels
        newIndices = list(range(0, len(labels)))
        self._mapping[t] = dict(list(zip(labels, newIndices)))
        return labelImage

    def execute(self, slot, subindex, roi, result):
        if slot == self.Output:
            taggedShape = self.LabelImage.meta.getTaggedShape()
            timeIndex = list(taggedShape.keys()).index('t')
            t = roi.start[timeIndex]
            labelImage = self._updateMapping(roi, t)
            result = np.zeros_like(result)
            for k, v in self._mapping[t].items():
                result[labelImage == k] = v

            return result
        elif slot == self.Mapping:
            if not self.Output.ready():
                t = roi.start[timeIndex]
                self._updateMapping(roi, t)
            return self._mapping

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.LabelImage:
            self.Output.setDirty(roi)

    def setInSlot(self, slot, subindex, roi, value):
        assert False, "OpZeroBasedConsecutiveIndexRelabeling does not allow setInSlot()"

    def cleanUp(self):
        self.LabelImage.disconnect()
        super( OpZeroBasedConsecutiveIndexRelabeling, self ).cleanUp()


class OpRelabeledMergerFeatureExtraction(Operator):
    """
    This operator computes the features of relabeled segments, and combines them
    with the already computed and cached region features of the original label image.

    ATTENTION: the new features are not cached, as they are intended only for export
    ATTENTION: No division features are recomputed, but divisions are not allowed to interact with mergers anyway
    """
    name = "Relabeled Merger Feature Extraction"

    RawImage = InputSlot()
    LabelImage = InputSlot()
    RelabeledImage = InputSlot()
    OriginalRegionFeatures = InputSlot(stype=Opaque, rtype=List, value={})

    FeatureNames = InputSlot(rtype=List, stype=Opaque, value={})

    # the computed features.
    # nested dictionary with format:
    # dict[plugin_name][feature_name] = feature_value
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)
    RegionFeaturesVigra = OutputSlot(stype=Opaque, rtype=List)

    def __init__(self, parent):
        super(OpRelabeledMergerFeatureExtraction, self).__init__(parent)

        # TODO: uncached! combine old and new features for export

        # internal operators
        self._opMergersOnly = OpDifference(parent=self)
        self._opMergersOnly.ImageA.connect(self.LabelImage)
        self._opMergersOnly.ImageB.connect(self.RelabeledImage)

        self._opZeroBasedMergerImage = OpZeroBasedConsecutiveIndexRelabeling(parent=self)
        self._opZeroBasedMergerImage.LabelImage.connect(self._opMergersOnly.Output)

        self._opRegionFeatures = OpRegionFeatures(parent=self)
        self._opRegionFeatures.RawVolume.connect(self.RawImage)
        self._opRegionFeatures.LabelVolume.connect(self._opZeroBasedMergerImage.Output)
        self._opRegionFeatures.Features.connect(self.FeatureNames)

        self._opAdaptTimeListRoi = OpAdaptTimeListRoi(parent=self)
        self._opAdaptTimeListRoi.Input.connect(self._opRegionFeatures.Output)
        self.RegionFeaturesVigra.connect(self._opAdaptTimeListRoi.Output)

    def setupOutputs(self, *args, **kwargs):
        self.RegionFeatures.meta.assignFrom(self.RegionFeaturesVigra.meta)

    @staticmethod
    def _merge_features(featuresA, featuresB, mapping):
        assert featuresA.shape[1] == featuresB.shape[1], "Feature dimensions must match!"
        max_label = max(max(mapping.keys())+1, len(featuresA))

        features = np.zeros((max_label, featuresA.shape[1]), dtype=featuresA.dtype)
        features[:len(featuresA), ...] = featuresA

        for k, v in mapping.items():
            if k == 0:
                continue
            features[k, ...] = featuresB[v, ...]

        return features

    def execute(self, slot, subindex, roi, result):
        if slot == self.RegionFeatures:
            feat_vigra = self.RegionFeaturesVigra(roi).wait()
            orig_feat_all = self.OriginalRegionFeatures(roi).wait()
            mapping = self._opZeroBasedMergerImage.Mapping(roi).wait()

            import copy
            result = copy.deepcopy(orig_feat_all)

            # merge the features in each frame
            for t, feature_groups in feat_vigra.items():
                for name, features in feature_groups.items():
                    for k, v in features.items():
                        if k in result[t][name] and t in mapping:
                            result[t][name][k] = self._merge_features(result[t][name][k], v, mapping[t])
                        else:
                            logger.debug("Ignoring feature {}-{} when merging".format(name, k))

            return result
        else:
            assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.LabelImage or slot == self.RelabeledImage \
            or slot == self.RawImage or slot == self.FeatureNames or slot == self.OriginalRegionFeatures:
            self.RegionFeatures.setDirty(roi)
            self.RegionFeaturesVigra.setDirty(roi)

    def setInSlot(self, slot, subindex, roi, value):
        assert False, "Invalid slot for setInSlot(): {}".format(slot.name)

    def _checkConstraints(self, *args):
        if self.RawImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            if 't' not in rawTaggedShape or rawTaggedShape['t'] < 2:
                msg = "Raw image must have a time dimension with at least 2 images.\n"\
                    "Your dataset has shape: {}".format(self.RawImage.meta.shape)

        if self.LabelImage.ready():
            rawTaggedShape = self.LabelImage.meta.getTaggedShape()
            if 't' not in rawTaggedShape or rawTaggedShape['t'] < 2:
                msg = "Binary image must have a time dimension with at least 2 images.\n"\
                    "Your dataset has shape: {}".format(self.LabelImage.meta.shape)

        if self.RelabeledImage.ready():
            rawTaggedShape = self.RelabeledImage.meta.getTaggedShape()
            if 't' not in rawTaggedShape or rawTaggedShape['t'] < 2:
                msg = "Relabeled image must have a time dimension with at least 2 images.\n"\
                    "Your dataset has shape: {}".format(self.RelabeledImage.meta.shape)

        if self.RawImage.ready() and self.LabelImage.ready():
            rawTaggedShape = self.RawImage.meta.getTaggedShape()
            labelImageTaggedShape= self.LabelImage.meta.getTaggedShape()
            rawTaggedShape['c'] = None
            labelImageTaggedShape['c'] = None
            if dict(rawTaggedShape) != dict(labelImageTaggedShape):
                logger.info("Raw data and other data must have equal dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawImage.meta.shape, self.LabelImage.meta.shape ))

                msg = "Raw data and other data must have equal dimensions (different channels are okay).\n"\
                      "Your datasets have shapes: {} and {}".format( self.RawImage.meta.shape, self.LabelImage.meta.shape )
                raise DatasetConstraintError( "Object Extraction", msg )

    def cleanUp(self):
        self.LabelImage.disconnect()
        self.RelabeledImage.disconnect()
        self.OriginalRegionFeatures.disconnect()
        self.RawImage.disconnect()
        self.FeatureNames.disconnect()

        super( OpRelabeledMergerFeatureExtraction, self ).cleanUp()



