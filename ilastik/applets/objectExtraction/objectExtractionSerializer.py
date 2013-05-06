import logging
import warnings
from functools import partial

import numpy

from lazyflow.rtype import SubRegion
from lazyflow.roi import getIntersectingBlocks, TinyVector, getBlockBounds, roiToSlice
from lazyflow.request import Request, RequestLock, RequestPool

from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup, SerialSlot, SerialHdf5BlockSlot, SerialDictSlot

from ilastik.utility.timer import timeLogged

logger = logging.getLogger(__name__)

class SerialObjectFeaturesSlot(SerialSlot):

    def __init__(self, slot, inslot, blockslot, name=None,
                 subname=None, default=None, depends=None,
                 selfdepends=True):
        super(SerialObjectFeaturesSlot, self).__init__(
            slot, inslot, name, subname, default, depends, selfdepends
        )

        self.blockslot = blockslot
        self._bind(slot)

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()

        for i in range(len(mainOperator)):
            subgroup = getOrCreateGroup(group, str(i))

            cleanBlockRois = self.blockslot[i].value
            for roi in cleanBlockRois:
                region_features_arr = self.slot[i]( *roi ).wait()
                assert region_features_arr.shape == (1,)
                region_features = region_features_arr[0]
                roi_grp = subgroup.create_group(name=str(roi))
                logger.debug('Saving region features into group: "{}"'.format( roi_grp.name ))
                for key, val in region_features.iteritems():
                    plugin_group = getOrCreateGroup(roi_grp, key)
                    for featname, featval in val.iteritems():
                        plugin_group.create_dataset(name=featname, data=featval)

        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        opgroup = group[self.name]
        for i, (_, subgroup) in enumerate( sorted(opgroup.items() ) ):
            for roiString, roi_grp in subgroup.iteritems():
                logger.debug('Loading region features from dataset: "{}"'.format( roi_grp.name ))
                roi = eval(roiString)

                region_features = {}
                for key, val in roi_grp.iteritems():
                    region_features[key] = {}
                    for featname, featval in val.iteritems():
                        region_features[key][featname] = featval[...]

                slicing = roiToSlice( *roi )
                self.inslot[i][slicing] = numpy.array([region_features])

        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialHdf5BlockSlot(operator.LabelOutputHdf5,
                                operator.LabelInputHdf5,
                                operator.CleanLabelBlocks,
                                name="LabelImage"),
            SerialDictSlot(operator.Features, transform=str),
            SerialObjectFeaturesSlot(operator.BlockwiseRegionFeatures,
                                     operator.RegionFeaturesCacheInput,
                                     operator.RegionFeaturesCleanBlocks,
                                     name="RegionFeatures"),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
