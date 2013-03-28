import logging
import warnings
from functools import partial

import numpy

from lazyflow.rtype import SubRegion
from lazyflow.roi import getIntersectingBlocks, TinyVector, getBlockBounds, roiToSlice
from lazyflow.request import Request, RequestLock, RequestPool

from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup, SerialSlot, SerialHdf5BlockSlot

from ilastik.utility.timer import timeLogged

logger = logging.getLogger(__name__)

class SerialObjectFeaturesSlot(SerialSlot):

    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()

        for i in range(len(mainOperator)):
            opRegFeats = mainOperator.getLane(i)._opRegFeats
            subgroup = getOrCreateGroup(group, str(i))

            cleanBlockRois = opRegFeats.CleanBlocks.value
            for roi in cleanBlockRois:
                region_features_arr = opRegFeats.Output( *roi ).wait()
                assert region_features_arr.shape == (1,1)
                region_features = region_features_arr[0,0]
                roi_grp = subgroup.create_group(name=str(roi))
                logger.debug('Saving region features into group: "{}"'.format( roi_grp.name ))
                for key, val in region_features.iteritems():
                    roi_grp.create_dataset(name=key, data=val)

        self.dirty = False

    def deserialize(self, group):
        if not self.name in group:
            return
        mainOperator = self.slot.getRealOperator()
        opgroup = group[self.name]
        for i, (_, subgroup) in enumerate( sorted(opgroup.items() ) ):
            opRegFeats = mainOperator.getLane(i)._opRegFeats

            for roiString, roi_grp in subgroup.items():
                logger.debug('Loading region features from dataset: "{}"'.format( roi_grp.name ))
                roi = eval(roiString)
                
                region_features = {}
                for key, val in roi_grp.items():
                    region_features[key] = val[...]
                
                slotRoi = SubRegion( opRegFeats.CacheInput, *roi )
                opRegFeats.setInSlot( opRegFeats.CacheInput, (), slotRoi, numpy.array( [[region_features]] ) )
        
        self.dirty = False


class ObjectExtractionSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [
            SerialHdf5BlockSlot(operator.LabelInputHdf5,
                                operator.LabelOutputHdf5,
                                operator.CleanLabelBlocks,
                                name="LabelImage"),
            SerialObjectFeaturesSlot(operator.RegionFeatures, name="samples"),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
