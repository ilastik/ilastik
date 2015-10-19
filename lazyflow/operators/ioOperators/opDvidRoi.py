###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#           http://ilastik.org/license/
###############################################################################
import os
import httplib
import collections
import logging
import warnings
from itertools import groupby, chain

import numpy
import h5py
import vigra

from lazyflow.graph import Operator, OutputSlot
from lazyflow.roi import determineBlockShape, roiToSlice
from lazyflow.utility import blockwise_view

from libdvid import DVIDException, ErrMsg, DVIDNodeService
from libdvid.voxels import DVID_BLOCK_WIDTH

logger = logging.getLogger(__name__)

class OpDvidRoi(Operator):
    """
    DVID supports a special type of dataset called 'ROI', which represents a mask 
    of blocks that contain a particular object of interest.  ROIs are only 
    defined with block-level resolution. (In DVID, voxels are stored natively in 
    blocks of size 32,32,32.)  Therefore, the resolution of a ROI is 32x lower 
    than the grayscale dataset it accompanies.
    
    This operator fetches the entire contents of a given ROI and stores it as an in-memory hdf5 file.
    The output slot exposes a voxel-level interface for requesting ROI mask pixels.
    The stored ROI mask is upsampled by 32x in each dimension to provide the requested mask.
    
    A note on terminology:
    Throughout lazyflow, we use the term 'roi' for something different: for 
    representing rectangular regions of ND images, specifically as start/stop 
    coordinate pairs.  We continue to use that convention in this file, with the 
    exception of the words 'OpDvidRoi' and 'DVIDNodeService.get_roi()', which 
    refer to the DVID concept.
    """
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass
    
    def __init__(self, hostname, uuid, roi_name, transpose_axes, *args, **kwargs):
        super( OpDvidRoi, self ).__init__(*args, **kwargs)
        self._transpose_axes = transpose_axes
        self._hostname = hostname
        self._uuid = uuid
        self._roi_name = roi_name
        self._mem_file = None
        self._dset = None

    def _after_init(self):
        self.ingest_data()
        super(OpDvidRoi, self)._after_init()

    def cleanUp(self):
        self._dset = None
        if self._mem_file:
            self._mem_file.close()
        super(OpDvidRoi, self).cleanUp()

    def ingest_data(self):
        """
        Ideally, this would be run within the __init__ function,
        but operators should never raise non-fatal exceptions within Operator.__init__()
        (See OperatorMetaClass.__call__)
        This serves as an alternative init function, from which we are allowed to raise exceptions.
        """
        try:
            node_service = DVIDNodeService(self._hostname, self._uuid)
            roi_blocks_xyz = numpy.array( node_service.get_roi(self._roi_name) )
        except DVIDException as ex:
            if ex.status == httplib.NOT_FOUND:
                raise OpDvidRoi.DatasetReadError("DVIDException: " + ex.message)
            raise
        except ErrMsg as ex:
            raise OpDvidRoi.DatasetReadError("ErrMsg: " + str(ex))

        # Store a dense array of the block flags
        # Each voxel of this dataset represents a dvid block, so this volume
        # is 32x smaller than the full-res data in every dimension.
        # TODO: For now, we only respect the high-side of the bounding box, and force the low-side to 0,0,0.
        shape = tuple(1 + numpy.max( roi_blocks_xyz, axis=0 ))
        slice_shape = shape[:2] + (1,)
        self._mem_file = h5py.File(str(id(self)), driver='core', backing_store=False, mode='w')
        dset = self._mem_file.create_dataset('data',
                                             shape=shape,
                                             dtype=numpy.uint8,
                                             chunks=slice_shape,
                                             compression='lzf')
        
        # Allocate temporary array slice for writing into the dataset
        z_slice = numpy.ndarray( slice_shape, numpy.uint8 )

        # Group the block indexes by z-coordinate
        # FIXME: This might get slow for lots of blocks because of all the calls to this lambda.
        #        Consider upgrading to cytools.groupby instead
        group_iter = groupby(roi_blocks_xyz, lambda block_index: block_index[2])
        
        # Set a pixel for each block index, one z-slice at a time
        for z, block_indexes_iter in group_iter:
            block_indexes = numpy.array(list(block_indexes_iter))
            block_indexes = block_indexes[:,:2] # drop z index
            z_slice[:] = 0
            z_slice[ tuple(block_indexes.transpose()) ] = 1
            dset[:,:,z] = z_slice[...,0]
        self._dset = dset

    def setupOutputs(self):
        shape = tuple(numpy.array(self._dset.shape) * DVID_BLOCK_WIDTH)
        dtype = self._dset.dtype
        axiskeys = "xyz"        

        try:
            no_extents_checking = bool(int(os.getenv("LAZYFLOW_NO_DVID_EXTENTS", 0)))
        except ValueError:
            raise RuntimeError("Didn't understand value for environment variable "\
                               "LAZYFLOW_NO_DVID_EXTENTS: '{}'.  Please use either 0 or 1."
                               .format(os.getenv("LAZYFLOW_NO_DVID_EXTENTS")))

        if no_extents_checking:
            # In headless mode, we allow the users to request regions outside the currently valid regions of the image.
            # For now, the easiest way to allow that is to simply hard-code DVID volumes to have a really large (1M cubed) shape.
            logger.info("Using absurdly large DVID volume extents, to allow out-of-bounds requests.")
            tagged_shape = collections.OrderedDict( zip(axiskeys, shape) )
            for k,v in tagged_shape.items():
                if k in 'xyz':
                    tagged_shape[k] = int(1e6)
            shape = tuple(tagged_shape.values())

        if self._transpose_axes:
            shape = tuple(reversed(shape))
            axiskeys = "".join(reversed(axiskeys))

        self.Output.meta.shape = shape
        self.Output.meta.dtype = dtype.type
        self.Output.meta.axistags = vigra.defaultAxistags( axiskeys ) # FIXME: Also copy resolution, etc.

    def execute(self, slot, subindex, roi, result):
        block_roi_start = roi.start / DVID_BLOCK_WIDTH
        block_roi_stop = ( roi.stop + DVID_BLOCK_WIDTH-1 ) / DVID_BLOCK_WIDTH
        block_slicing = roiToSlice(block_roi_start, block_roi_stop)

        if (numpy.array( (roi.start, roi.stop) ) % DVID_BLOCK_WIDTH).any():
            # Create an array that is bigger than the result, but block-aligned.
            aligned_result_shape = (block_roi_stop - block_roi_start) * DVID_BLOCK_WIDTH
            aligned_result = numpy.ndarray( aligned_result_shape, numpy.uint8 )
        else:
            aligned_result = result

        aligned_result_view = blockwise_view(aligned_result, 3*(DVID_BLOCK_WIDTH,), require_aligned_blocks=False)

        if self._transpose_axes:
            dset_slicing = tuple(reversed(block_slicing))
            # broadcast 3d data into 6d view
            aligned_result_view[:] = self._dset[dset_slicing].transpose()[..., None, None, None]
        else:
            # broadcast 3d data into 6d view
            aligned_result_view[:] = self._dset[block_slicing][..., None, None, None]
        
        # If the result wasn't aligned, we couldn't broadcast directly to it.
        # Copy the data now.
        if aligned_result is not result:
            start = roi.start - (block_roi_start*DVID_BLOCK_WIDTH)
            stop = start + (roi.stop - roi.start)
            result[:] = aligned_result[roiToSlice(start, stop)]

    def propagateDirty(self, *args):
        pass
