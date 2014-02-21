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
import collections

import numpy
import vigra

from lazyflow.graph import Operator, InputSlot
from lazyflow.utility import OrderedSignal
from lazyflow.roi import roiFromShape

import logging
logger = logging.getLogger(__name__)

class OpExportMultipageTiff(Operator):
    Input = InputSlot() # The last two non-singleton axes (except 'c') are the axes of the 'pages'.
                        # Re-order the axes yourself if you want an alternative slicing direction
    Filepath = InputSlot()

    BATCH_SIZE = 4

    def __init__(self, *args, **kwargs):
        super(OpExportMultipageTiff, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    def run_export(self):
        """
        Request the volume in slices (running in parallel), and write each slice to the correct page.
        Note: We can't use BigRequestStreamer here, because the data for each slice wouldn't be 
              guaranteed to arrive in the correct order.
        """
        # Delete existing image if present
        image_path = self.Filepath.value
        if os.path.exists(image_path):
            os.remove(image_path)

        # Sliceshape is the same as the input shape, except for the sliced dimension
        step_axis = self._volume_axes[0]
        tagged_sliceshape = self.Input.meta.getTaggedShape()
        tagged_sliceshape[step_axis] = 1
        slice_shape = (tagged_sliceshape.values())
        logger.debug("Starting Multipage Export with slicing shape: {}".format( slice_shape ))

        # Slice step is all zeros except step axis, e.g. (0, 1, 0, 0, 0)
        slice_step = numpy.array( self.Input.meta.getAxisKeys() ) == step_axis
        slice_step = slice_step.astype(int)

        def create_slice_req( index ):
            roi = roiFromShape(slice_shape)
            roi += index*slice_step
            return self.Input(*roi)

        tagged_shape = self.Input.meta.getTaggedShape()

        # Start with a batch of images
        reqs = collections.deque()
        for slice_index in range( min(self.BATCH_SIZE, tagged_shape[step_axis]) ):
            reqs.append( create_slice_req( slice_index ) )
        
        self.progressSignal(0)
        while reqs:
            self.progressSignal( 100*slice_index / tagged_shape[step_axis] )
            req = reqs.popleft()
            slice_data = req.wait()
            slice_index += 1
            # Add a new request to the batch
            if slice_index < tagged_shape[step_axis]:
                reqs.append( create_slice_req( slice_index ) )
            
            squeezed_data = slice_data.squeeze()
            squeezed_data = vigra.taggedView(squeezed_data, vigra.defaultAxistags("".join(self._volume_axes[1:])))
            assert len(squeezed_data.shape) == len(self._volume_axes)-1

            # Append a slice to the multipage tiff file
            vigra.impex.writeImage( squeezed_data, image_path, dtype='', compression='', mode='a' )

        self.progressSignal(100)

    def setupOutputs(self):
        # If stacking XY images in Z-steps,
        #  then self._volume_axes = 'zxy'
        self._volume_axes = self.get_nonsingleton_axes()

        # Check for errors
        assert len(self._volume_axes) == 3 or len(self._volume_axes) == 4 and 'c' in self._volume_axes[1:], \
            "Exported stacks must have exactly 3 non-singleton dimensions (other than the channel dimension).  "\
            "You stack dimensions are: {}".format( self.Input.meta.getTaggedShape() )

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


