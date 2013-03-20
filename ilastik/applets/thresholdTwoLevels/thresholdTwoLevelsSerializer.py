import logging

import numpy

from lazyflow.rtype import SubRegion
from lazyflow.roi import getIntersectingBlocks, TinyVector, getBlockBounds, roiToSlice

from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialDictSlot, \
                                                  deleteIfPresent, getOrCreateGroup


from ilastik.utility.timer import timeLogged

logger = logging.getLogger(__name__)

class SerialOutputBinaryImageSlot(SerialSlot):

    # FIXME: I copied/modified this code from ObjectExtractionSerializer.
    #        This should be refactored so they can share code.
    #        I'm a bad, bad man.

    @timeLogged(logger)
    def serialize(self, group):
        if not self.shouldSerialize(group):
            return
        deleteIfPresent(group, self.name)
        group = getOrCreateGroup(group, self.name)
        mainOperator = self.slot.getRealOperator()
        for i in range(len(mainOperator)):
            opTwoLevelThreshold = mainOperator.getLane(i)._opCache
            subgroup = getOrCreateGroup(group, str(i))

            cleanBlockRois = opTwoLevelThreshold.CleanBlocks.value
            for roi in cleanBlockRois:
                logger.debug('Saving two-level threshold output into dataset: "{}/{}"'.format( subgroup.name, str(roi) ))
                # This will be a little slow because the data is passing through a numpy array
                #  instead of somehow directly copying the h5py datasets in their compressed form.
                # We could maybe speed this up, but we'll lose some abstraction in the cache interface.
                data = opTwoLevelThreshold.Output( *roi ).wait()
                subgroup.create_dataset(name=str(roi), data=data, compression='lzf')

        self.dirty = False

    @timeLogged(logger)
    def deserialize(self, group):
        if not self.name in group:
            return
        
        mainOperator = self.slot.getRealOperator()
        opgroup = group[self.name]
        for i, (_, subgroup) in enumerate( sorted(opgroup.items() ) ):
            opTwoLevelThreshold = mainOperator.getLane(i)._opCache

            for roiString, dataset in subgroup.items():
                logger.debug('Loading two-level threshold output from dataset: "{}/{}"'.format( subgroup.name, dataset.name ))
                roi = eval(roiString)

                roiShape = TinyVector(roi[1]) - TinyVector(roi[0])
                assert roiShape == dataset.shape

                # Further subdivide the roi into small blocks that can be applied one at a time.
                # This avoids allocating an enormous temporary numpy array
                chunk_shape = dataset.chunks
                assert chunk_shape is not None
                block_shape = TinyVector(chunk_shape) * 3
                block_shape = numpy.minimum(block_shape, dataset.shape)
                block_starts = getIntersectingBlocks(block_shape, roi)

                for block_start in block_starts:
                    block_roi = getBlockBounds( roi[1], block_shape, block_start )
                    dataset_relative_roi = numpy.array(block_roi) - roi[0]

                    slotRoi = SubRegion( opTwoLevelThreshold.Input, *block_roi )
                    opTwoLevelThreshold.setInSlot( opTwoLevelThreshold.Input, (), slotRoi, dataset[roiToSlice( *dataset_relative_roi )] )

        self.dirty = False


class ThresholdTwoLevelsSerializer(AppletSerializer):
    def __init__(self, operator, projectFileGroupName):
        slots = [SerialSlot(operator.MinSize, autodepends=True),
                 SerialSlot(operator.MaxSize, autodepends=True),
                 SerialSlot(operator.HighThreshold, autodepends=True),
                 SerialSlot(operator.LowThreshold, autodepends=True),
                 SerialDictSlot(operator.SmootherSigma, autodepends=True),
                 SerialSlot(operator.Channel, autodepends=True),
                 SerialOutputBinaryImageSlot(operator.CachedOutput)
                ]
        
        super(self.__class__, self).__init__(projectFileGroupName, slots=slots)
