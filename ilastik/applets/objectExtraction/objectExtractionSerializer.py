import logging
import warnings
from functools import partial

import numpy

from lazyflow.rtype import SubRegion
from lazyflow.roi import getIntersectingBlocks, TinyVector, getBlockBounds, roiToSlice
from lazyflow.request import Request, RequestLock, RequestPool

from ilastik.applets.base.appletSerializer import AppletSerializer,\
    deleteIfPresent, getOrCreateGroup, SerialSlot

from ilastik.utility.timer import timeLogged

logger = logging.getLogger(__name__)

class SerialLabelImageSlot(SerialSlot):

    @timeLogged(logger)
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        for i in range(len(mainOperator)):
            opLabel = mainOperator.getLane(i)._opLabelImage
            subgroup = getOrCreateGroup(group, str(i))

            cleanBlockRois = opLabel.CleanBlocks.value
            for roi in cleanBlockRois:
                logger.debug('Saving labels into dataset: "{}/{}"'.format( subgroup.name, str(roi) ))
                # This will be a little slow because the data is passing through a numpy array
                #  instead of somehow directly copying the h5py datasets in their compressed form.
                # We could maybe speed this up, but we'll lose some abstraction in the cache interface.
                data = opLabel.Output( *roi ).wait()
                subgroup.create_dataset(name=str(roi), data=data, compression='lzf')

        self.dirty = False

    @timeLogged(logger)
    def deserialize(self, group):
        if not self.name in group:
            return
        
        mainOperator = self.slot.getRealOperator()
        opgroup = group[self.name]
        for i, (_, subgroup) in enumerate( sorted(opgroup.items() ) ):
            opLabel = mainOperator.getLane(i)._opLabelImage

            for roiString, dataset in subgroup.items():
                logger.debug('Loading labels from dataset: "{}/{}"'.format( subgroup.name, dataset.name ))
                roi = eval(roiString)

                roiShape = TinyVector(roi[1]) - TinyVector(roi[0])
                assert roiShape == dataset.shape

                # Further subdivide the roi into small blocks that can be applied one at a time.
                # This avoids allocating an enormous temporary numpy array
                chunk_shape = dataset.chunks
                assert chunk_shape is not None
                block_shape = TinyVector(chunk_shape) * 10
                block_shape = numpy.minimum(block_shape, dataset.shape)
                block_starts = getIntersectingBlocks(block_shape, roi)

                for block_start in block_starts:
                    block_roi = getBlockBounds( roi[1], block_shape, block_start )
                    dataset_relative_roi = numpy.array(block_roi) - roi[0]
                    slotRoi = SubRegion( opLabel.Input, *block_roi )
                    sub_block_data = dataset[roiToSlice( *dataset_relative_roi )]
                    opLabel.setInSlot( opLabel.Input, (), slotRoi, sub_block_data )
                    
        self.dirty = False


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
            SerialLabelImageSlot(operator.LabelImage, name="LabelImage"),
            SerialObjectFeaturesSlot(operator.RegionFeatures, name="samples"),
        ]

        super(ObjectExtractionSerializer, self).__init__(projectFileGroupName,
                                                         slots=slots)
