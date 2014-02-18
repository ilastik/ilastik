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

import os
import math

import numpy

from lazyflow.graph import Operator, InputSlot
from lazyflow.utility import OrderedSignal
from lazyflow.roi import roiFromShape
from lazyflow.operators.generic import OpSubRegion

from .opExportMultipageTiff import OpExportMultipageTiff

import logging
logger = logging.getLogger(__name__)

class OpExportMultipageTiffSequence(Operator):
    Input = InputSlot() # The last two non-singleton axes (except 'c') are the axes of the slices.
                        # Re-order the axes yourself if you want an alternative slicing direction

    FilepathPattern = InputSlot() # A complete filepath including a {slice_index} member and a valid file extension.
    SliceIndexOffset = InputSlot(value=0) # Added to the {slice_index} in the export filename.

    def __init__(self, *args, **kwargs):
        super(OpExportMultipageTiffSequence, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def run_export(self):
        """
        Request the volume in slices (running in parallel), and write each slice to the correct page.
        Note: We can't use BigRequestStreamer here, because the data for each slice wouldn't be 
              guaranteed to arrive in the correct order.
        """
        # Make the directory first if necessary
        export_dir = os.path.split(self.FilepathPattern.value)[0]
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        # Blockshape is the same as the input shape, except for the sliced dimension
        step_axis = self._volume_axes[0]
        tagged_blockshape = self.Input.meta.getTaggedShape()
        tagged_blockshape[step_axis] = 1
        block_shape = (tagged_blockshape.values())
        logger.debug("Starting Multipage Sequence Export with block shape: {}".format( block_shape ))

        # Block step is all zeros except step axis, e.g. (0, 1, 0, 0, 0)
        block_step = numpy.array( self.Input.meta.getAxisKeys() ) == step_axis
        block_step = block_step.astype(int)

        filepattern = self.FilepathPattern.value

        # If the user didn't provide custom formatting for the slice field,
        #  auto-format to include zero-padding
        if '{slice_index}' in filepattern:
            filepattern = filepattern.format( slice_index='{' + 'slice_index:0{}'.format(self._max_slice_digits) + '}' )        

        self.progressSignal(0)
        # Nothing fancy here: Just loop over the blocks in order.
        tagged_shape = self.Input.meta.getTaggedShape()
        for block_index in xrange( tagged_shape[step_axis] ):
            roi = numpy.array(roiFromShape(block_shape))
            roi += block_index*block_step

            try:
                opSubregion = OpSubRegion( parent=self )
                opSubregion.Start.setValue( tuple(roi[0]) )
                opSubregion.Stop.setValue( tuple(roi[1]) )
                opSubregion.Input.connect( self.Input )

                formatted_path = filepattern.format( slice_index=(block_index + self.SliceIndexOffset.value) )
                opExportBlock = OpExportMultipageTiff( parent=self )
                opExportBlock.Input.connect( opSubregion.Output )
                opExportBlock.Filepath.setValue( formatted_path )

                block_start_progress = 100*block_index / tagged_shape[step_axis]
                def _handleBlockProgress(block_progress):
                    self.progressSignal( block_start_progress + block_progress/tagged_shape[step_axis] )
                opExportBlock.progressSignal.subscribe( _handleBlockProgress )

                # Run the export for this block
                opExportBlock.run_export()
            finally:
                opExportBlock.cleanUp()
                opSubregion.cleanUp()

        self.progressSignal(100)

    def setupOutputs(self):
        # If stacking XY images in Z-steps,
        #  then self._volume_axes = 'zxy'
        self._volume_axes = self.get_nonsingleton_axes()
        step_axis = self._volume_axes[0]
        max_slice = self.SliceIndexOffset.value + self.Input.meta.getTaggedShape()[step_axis]
        self._max_slice_digits = int(math.ceil(math.log10(max_slice+1)))

        # Check for errors
        assert len(self._volume_axes) == 4 or len(self._volume_axes) == 5 and 'c' in self._volume_axes[1:], \
            "Exported stacks must have exactly 4 non-singleton dimensions (other than the channel dimension).  "\
            "You stack dimensions are: {}".format( self.Input.meta.getTaggedShape() )

        # Test to make sure the filepath pattern includes slice index field        
        filepath_pattern = self.FilepathPattern.value
        assert '123456789' in filepath_pattern.format( slice_index=123456789 ), \
            "Output filepath pattern must contain the '{slice_index}' field for formatting.\n"\
            "Your format was: {}".format( filepath_pattern )

    # No output slots...
    def execute(self, slot, subindex, roi, result): pass 
    def propagateDirty(self, slot, subindex, roi): pass

    def get_nonsingleton_axes(self):
        return self.get_nonsingleton_axes_for_tagged_shape( self.Input.meta.getTaggedShape() )

    @classmethod
    def get_nonsingleton_axes_for_tagged_shape(self, tagged_shape):
        # Find the non-singleton axes.
        # The first non-singleton axis is the step axis.
        # The last 2 non-channel non-singleton axes will be the axes of the slices.
        tagged_items = tagged_shape.items()
        filtered_items = filter( lambda (k, v): v > 1, tagged_items )
        filtered_axes = zip( *filtered_items )[0]
        return filtered_axes


