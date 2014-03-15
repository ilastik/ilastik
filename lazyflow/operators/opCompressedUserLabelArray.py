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
from lazyflow.roi import roiToSlice
from lazyflow.operators.opCache import OpCache
from lazyflow.operators.opCompressedCache import OpCompressedCache

logger = logging.getLogger(__name__)

class OpCompressedUserLabelArray(OpCache):
    Input = InputSlot()
    shape = InputSlot(optional=True) # Should not be used.
    eraser = InputSlot()
    deleteLabel = InputSlot(optional = True)
    blockShape = InputSlot()

    Output = OutputSlot()
    #nonzeroValues = OutputSlot()
    #nonzeroCoordinates = OutputSlot()
    nonzeroBlocks = OutputSlot()
    #maxLabel = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpCompressedUserLabelArray, self).__init__( *args, **kwargs )
        self._blockshape = None
        self._label_to_purge = 0
        
        # We want our cache to have direct access to the input, but not for "setInSlot", which
        self._opInputConnectionProvider = OpCompressedUserLabelArray._OpLabelInputConnectionProvider( parent=self )
        self._opInputConnectionProvider.Input.connect( self.Input )

        # Labels are stored blockwise in a compressed cache
        self._opCompressedCache = OpCompressedCache( parent=self )
        self._opCompressedCache.Input.connect( self._opInputConnectionProvider.Output )
        
        self.Output.connect( self._opCompressedCache.Output )
    
    def setupOutputs(self):
        self.nonzeroBlocks.meta.dtype = object
        self.nonzeroBlocks.meta.shape = (1,)

        if self._blockshape is None:
            self._blockshape = self.blockShape.value
        else:
            assert self.blockShape.value == self._blockshape, \
                "Not allowed to change the blockshape after initial setup"

        self._opCompressedCache.BlockShape.setValue( self._blockshape )
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
        stored_block_rois = self._opCompressedCache.CleanBlocks.value
        for block_roi in stored_block_rois:
            # Get data
            block = self._opCompressedCache.Output(block_roi[0], block_roi[1]).wait()

            # Locate pixels to change
            matching_label_coords = numpy.nonzero( block == label_to_purge )
            coords_to_decrement = block > label_to_purge

            # Change the data
            block[matching_label_coords] = 0
            block = numpy.where( coords_to_decrement, block-1, block )
            
            # Update cache with the new data (only if something really changed)
            if len(matching_label_coords[0]) > 0 or len(coords_to_decrement[0]) > 0:
                self._opCompressedCache.Input[roiToSlice(*block_roi)] = block
                changed_block_rois.append( block_roi )

        for block_roi in changed_block_rois:
            # FIXME: Shouldn't this dirty notification be handled in OpCompressedCache?
            self.Output.setDirty( *block_roi )
    
    def execute(self, slot, subindex, roi, destination):
        assert slot != self.Output, "Output is supposed to be directly connected to our cache..."
        if slot == self.nonzeroBlocks:
            stored_block_rois = self._opCompressedCache.CleanBlocks.value
            block_slicings = map( lambda block_roi: roiToSlice(*block_roi), stored_block_rois )
            destination[0] = block_slicings
            return
        assert False, "Unknown slot: {}".format( slot.name )            

    def propagateDirty(self, slot, subindex, roi):
        # There should be no way to make the output dirty except via setInSlot()
        pass

    def setInSlot(self, slot, subindex, roi, new_pixels):
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
        assert slot == self.Input

        # Extract the data to modify
        original_data = self._opCompressedCache.Output(roi.start, roi.stop).wait()
        
        # Reset the pixels we need to change (so we can use |= below)
        original_data[new_pixels.nonzero()] = 0
        
        # Update
        original_data |= new_pixels

        # Replace 'eraser' values with zeros.
        cleaned_data = numpy.where(original_data == self._eraser_magic_value, 0, original_data[:])

        # Set in the cache.
        self._opCompressedCache.Input[roiToSlice(roi.start, roi.stop)] = cleaned_data
        
        # FIXME: Shouldn't this notification be triggered from within opCompressedCache?
        self.Output.setDirty( roi.start, roi.stop )
    
    class _OpLabelInputConnectionProvider(Operator):
        """
        Provides an input slot for the compressed cache that allows the compressed cache to be used for labeling.
        - Output is intended to be connected to a CompressedCache
        - Output will have the same shape as Input (except just one channel)
        - Output has dtype uint8 (for user label data)
        - If the cache requests 'input' data, it is provided zeros only.
        - setInSlot() is NOT implemented, and calls to setInSlot are not forwarded to the cache
        """
        Input = InputSlot()
        Output = OutputSlot()
        
        def setupOutputs(self):
            assert self.Input.meta.getAxisKeys()[-1] == 'c', "OpCompressedUserLabels assumes that the last axis is channel."
            self.Output.meta.assignFrom(self.Input.meta)
            self.Output.meta.dtype = numpy.uint8
            self.Output.meta.shape = self.Input.meta.shape[:-1] + (1,)
            self.Output.meta.drange = (0,255)
        
        def execute(self, slot, subindex, roi, destination):
            # The cache is asking for initial label data.
            # The only real label data in the cache is inserted via setInSlot()
            # All block initial values are zero.
            destination[:] = 0
            return
        
        def propagateDirty(self, slot, subindex, roi):
            # The cache is only changed via setInSlot(), and that's the only place it becomes dirty.
            pass
        
        def setInSlot(self, *args):
            pass

