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

# Built-in
import logging

# Third-party
import numpy

# Lazyflow
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import TinyVector, getIntersectingBlocks, getBlockBounds, roiToSlice, getIntersection
from lazyflow.operators.opCache import OpCache
from lazyflow.operators.opCompressedCache import OpCompressedCache
from lazyflow.rtype import SubRegion

logger = logging.getLogger(__name__)

class OpCompressedUserLabelArray(OpCompressedCache):
    #Input = InputSlot()
    shape = InputSlot(optional=True) # Should not be used.
    eraser = InputSlot()
    deleteLabel = InputSlot(optional = True)
    blockShape = InputSlot()

    #Output = OutputSlot()
    #nonzeroValues = OutputSlot()
    #nonzeroCoordinates = OutputSlot()
    nonzeroBlocks = OutputSlot()
    #maxLabel = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpCompressedUserLabelArray, self).__init__( *args, **kwargs )
        self._blockshape = None
        self._label_to_purge = 0
    
    def setupOutputs(self):
        # Due to a temporary naming clash, pass our subclass blockshape to the superclass
        # TODO: Fix this by renaming the BlockShape slots to be consistent.
        self.BlockShape.setValue( self.blockShape.value )
        
        super( OpCompressedUserLabelArray, self ).setupOutputs()
        self.nonzeroBlocks.meta.dtype = object
        self.nonzeroBlocks.meta.shape = (1,)
        
        # Overwrite the Output metadata (should be uint8 no matter what the input data is...)
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.uint8
        self.Output.meta.shape = self.Input.meta.shape[:-1] + (1,)
        self.Output.meta.drange = (0,255)
        self.OutputHdf5.meta.assignFrom(self.Output.meta)

        # Overwrite the blockshape
        if self._blockshape is None:
            self._blockshape = numpy.minimum( self.BlockShape.value, self.Output.meta.shape )
        else:
            assert self.blockShape.value == self._blockshape, \
                "Not allowed to change the blockshape after initial setup"

        # Overwrite chunkshape now that blockshape has been overwritten
        self._chunkshape = self._chooseChunkshape(self._blockshape)

        self._eraser_magic_value = self.eraser.value
        
        # Are we being told to delete a label?
        if self.deleteLabel.ready():
            new_purge_label = self.deleteLabel.value
            if self._label_to_purge != new_purge_label:
                self._label_to_purge = new_purge_label
                if self._label_to_purge > 0:
                    self._purge_label( self._label_to_purge )
    
    def _purge_label(self, label_to_purge):
        """
        Scan through all labeled pixels.
        (1) Clear all pixels of the given value (set to 0)
        (2) Decrement all labels above that value so the set of stored labels is consecutive
        """
        changed_block_rois = []
        #stored_block_rois = self.CleanBlocks.value
        stored_block_roi_destination = [None]
        self.execute(self.CleanBlocks, (), SubRegion( self.Output, (0,),(1,) ), stored_block_roi_destination)
        stored_block_rois = stored_block_roi_destination[0]

        for block_roi in stored_block_rois:
            # Get data
            block_shape = numpy.subtract( block_roi[1], block_roi[0] )
            block = numpy.ndarray( shape=block_shape, dtype=self.Output.meta.dtype )
            self.execute(self.Output, (), SubRegion( self.Output, *block_roi ), block)

            # Locate pixels to change
            matching_label_coords = numpy.nonzero( block == label_to_purge )
            coords_to_decrement = block > label_to_purge

            # Change the data
            block[matching_label_coords] = 0
            block = numpy.where( coords_to_decrement, block-1, block )
            
            # Update cache with the new data (only if something really changed)
            if len(matching_label_coords[0]) > 0 or len(coords_to_decrement[0]) > 0:
                super( OpCompressedUserLabelArray, self )._setInSlotInput( self.Input, (), SubRegion( self.Output, *block_roi ), block, store_zero_blocks=False )
                changed_block_rois.append( block_roi )

        for block_roi in changed_block_rois:
            # FIXME: Shouldn't this dirty notification be handled in OpCompressedCache?
            self.Output.setDirty( *block_roi )
    
    def execute(self, slot, subindex, roi, destination):
        if slot == self.Output:
            self._executeOutput(roi, destination)
        elif slot == self.nonzeroBlocks:
            stored_block_rois = self.CleanBlocks.value
            block_slicings = map( lambda block_roi: roiToSlice(*block_roi), stored_block_rois )
            destination[0] = block_slicings
            return
        else:
            return super( OpCompressedUserLabelArray, self ).execute( slot, subindex, roi, destination )

    def _executeOutput(self, roi, destination):
        assert len(roi.stop) == len(self.Input.meta.shape), \
            "roi: {} has the wrong number of dimensions for Input shape: {}"\
            "".format( roi, self.Input.meta.shape )
        assert numpy.less_equal(roi.stop, self.Input.meta.shape).all(), \
            "roi: {} is out-of-bounds for Input shape: {}"\
            "".format( roi, self.Input.meta.shape )
        
        block_starts = getIntersectingBlocks( self._blockshape, (roi.start, roi.stop) )
        self._copyData(roi, destination, block_starts)
        return destination

    def _copyData(self, roi, destination, block_starts):
        """
        Copy data from each block into the destination array.
        For blocks that aren't currently stored, just write zeros.
        """
        # (Parallelism not needed here: h5py will serialize these requests anyway)
        block_starts = map( tuple, block_starts )
        for block_start in block_starts:
            entire_block_roi = getBlockBounds( self.Output.meta.shape, self._blockshape, block_start )

            # This block's portion of the roi
            intersecting_roi = getIntersection( (roi.start, roi.stop), entire_block_roi )
            
            # Compute slicing within destination array and slicing within this block
            destination_relative_intersection = numpy.subtract(intersecting_roi, roi.start)
            block_relative_intersection = numpy.subtract(intersecting_roi, block_start)
            
            if block_start in self._cacheFiles:
                # Copy from block to destination
                dataset = self._getBlockDataset( entire_block_roi )
                destination[ roiToSlice(*destination_relative_intersection) ] = dataset[ roiToSlice( *block_relative_intersection ) ]
            else:
                # Not stored yet.  Overwrite with zeros.
                destination[ roiToSlice(*destination_relative_intersection) ] = 0

    def propagateDirty(self, slot, subindex, roi):
        # There should be no way to make the output dirty except via setInSlot()
        pass

    def setInSlot(self, slot, subindex, roi, new_pixels):
        if slot == self.Input:
            self._setInSlotInput(slot, subindex, roi, new_pixels)
        else:
            # We don't yet support the InputHdf5 slot in this function.
            assert False, "Unsupported slot for setInSlot: {}".format( slot.name )
            
    def _setInSlotInput(self, slot, subindex, roi, new_pixels):
        """
        Since this is a label array, inserting pixels has a special meaning:
        We only overwrite the new non-zero pixels. In the new data, zeros mean "don't change".
        
        So, here's what each pixel we're adding means:
        0: don't change
        1: change to 1
        2: change to 2
        ...
        N: change to N
        magic_eraser_value: change to 0  
        """

        # Extract the data to modify
        original_data = numpy.ndarray( shape=new_pixels.shape, dtype=self.Output.meta.dtype )
        self.execute(self.Output, (), roi, original_data)
        
        # Reset the pixels we need to change (so we can use |= below)
        original_data[new_pixels.nonzero()] = 0
        
        # Update
        original_data |= new_pixels

        # Replace 'eraser' values with zeros.
        cleaned_data = numpy.where(original_data == self._eraser_magic_value, 0, original_data[:])

        # Set in the cache (our superclass).
        super( OpCompressedUserLabelArray, self )._setInSlotInput( slot, subindex, roi, cleaned_data, store_zero_blocks=False )
        
        # FIXME: Shouldn't this notification be triggered from within OpCompressedCache?
        self.Output.setDirty( roi.start, roi.stop )
