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

    def __init__(self, inslot, outslot, blockslot, *args, **kwargs):
        super( SerialObjectFeaturesSlot, self).__init__(outslot, *args, **kwargs )
        self.inslot = inslot
        self.outslot = outslot
        self.blockslot = blockslot
        self._bind(outslot)

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
                region_features_arr = self.outslot[i]( *roi ).wait()
                assert region_features_arr.shape == (1,)
                region_features = region_features_arr[0]
                roi_grp = subgroup.create_group(name=str(roi))
                logger.debug('Saving region features into group: "{}"'.format( roi_grp.name ))
                for key, val in region_features.iteritems():
                    roi_grp.create_dataset(name=key, data=val)

        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        opgroup = group[self.name]
        for i, (_, subgroup) in enumerate( sorted(opgroup.items() ) ):
            for roiString, roi_grp in subgroup.items():
                logger.debug('Loading region features from dataset: "{}"'.format( roi_grp.name ))
                roi = eval(roiString)
                
                region_features = {}
                for key, val in roi_grp.items():
                    region_features[key] = val[...]
                
                slicing = roiToSlice( *roi )
                self.inslot[i][slicing] = numpy.array([region_features])
        
        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialHdf5BlockSlot(operator.LabelInputHdf5,
                                operator.LabelOutputHdf5,
                                operator.CleanLabelBlocks,
                                name="LabelImage"),
            SerialObjectFeaturesSlot(operator.RegionFeaturesCacheInput,
                                     operator.BlockwiseRegionFeatures,
                                     operator.RegionFeaturesCleanBlocks,
                                     name="RegionFeatures"),
            SerialDictSlot(operator.Features)
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
