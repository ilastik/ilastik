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
#		   http://ilastik.org/license/
###############################################################################
import os
import httplib
import collections
import logging

import numpy
import vigra
from lazyflow.graph import Operator, OutputSlot
from lazyflow.roi import determineBlockShape

from libdvid import DVIDException, ErrMsg
from libdvid.voxels import VoxelsAccessor

logger = logging.getLogger(__name__)

class OpDvidVolume(Operator):
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass
    
    def __init__(self, hostname, uuid, dataname, query_args, transpose_axes, *args, **kwargs):
        super( OpDvidVolume, self ).__init__(*args, **kwargs)
        self._transpose_axes = transpose_axes
        self._default_accessor = None
        self._throttled_accessor = None
        self._hostname = hostname
        self._uuid = uuid
        self._dataname = dataname
        self._query_args = query_args

    def _after_init(self):
        self.init_client()
        super(OpDvidVolume, self)._after_init()

    def init_client(self):
        """
        Ideally, this would be run within the __init__ function,
        but operators should never raise non-fatal exceptions within Operator.__init__()
        (See OperatorMetaClass.__call__)
        This serves as an alternative init function, from which we are allowed to raise exceptions.
        """
        try:
            self._default_accessor = VoxelsAccessor( self._hostname, self._uuid, self._dataname, self._query_args )
            self._throttled_accessor = VoxelsAccessor( self._hostname, self._uuid, self._dataname, self._query_args, throttle=True )
        except DVIDException as ex:
            if ex.status == httplib.NOT_FOUND:
                raise OpDvidVolume.DatasetReadError("DVIDException: " + ex.message)
            raise
        except ErrMsg as ex:
            raise OpDvidVolume.DatasetReadError("ErrMsg: " + str(ex))
    
    def cleanUp(self):
        self._default_accessor = None
        self._throttled_accessor = None
        super( OpDvidVolume, self ).cleanUp()
    
    def setupOutputs(self):
        shape, dtype, axiskeys = self._default_accessor.shape, self._default_accessor.dtype, self._default_accessor.axiskeys
        
        try:
            no_extents_checking = bool(int(os.getenv("LAZYFLOW_NO_DVID_EXTENTS", 0)))
        except ValueError:
            raise RuntimeError("Didn't understand value for environment variable "\
                               "LAZYFLOW_NO_DVID_EXTENTS: '{}'.  Please use either 0 or 1."
                               .format(os.getenv("LAZYFLOW_NO_DVID_EXTENTS")))

        if no_extents_checking or (None in shape):
            # In headless mode, we allow the users to request regions outside the currently valid regions of the image.
            # For now, the easiest way to allow that is to simply hard-code DVID volumes to have a really large (1M cubed) shape.
            logger.info("Using absurdly large DVID volume extents, to allow out-of-bounds requests.")
            tagged_shape = collections.OrderedDict( zip(axiskeys, shape) )
            for k,v in tagged_shape.items():
                if k in 'xyz':
                    tagged_shape[k] = int(1e6)
            shape = tuple(tagged_shape.values())
        
        num_channels = shape[0]
        if self._transpose_axes:
            shape = tuple(reversed(shape))
            axiskeys = "".join(reversed(axiskeys))

        self.Output.meta.shape = shape
        self.Output.meta.dtype = dtype.type
        self.Output.meta.axistags = vigra.defaultAxistags( axiskeys ) # FIXME: Also copy resolution, etc.
        
        # To avoid requesting extremely large blocks, limit each request to 500MB each.
        max_pixels = 2**29 / self.Output.meta.dtype().nbytes
        self.Output.meta.ideal_blockshape = determineBlockShape( self.Output.meta.shape, max_pixels )
        
        # For every request, we probably need room RAM for the array and for the http buffer
        # (and hopefully nothing more)
        self.Output.meta.ram_usage_per_requested_pixel = 2 * dtype.type().nbytes * num_channels

    def execute(self, slot, subindex, roi, result):
        if numpy.prod(roi.stop - roi.start) > 1e9:
            logger.error("Requesting a very large volume from DVID: {}\n"\
                         "Is that really what you meant to do?"
                         .format( roi ))
            
        # TODO: Modify accessor implementation to accept a pre-allocated array.

# FIXME: Disabled throttling for now.  Need a better heuristic or explicit setting.
#         # For "heavy" requests, we'll use the throttled accessor
#         HEAVY_REQ_SIZE = 256*256*10
#         if numpy.prod(result.shape) > HEAVY_REQ_SIZE:
#             accessor = self._throttled_accessor
#         else:
#             accessor = self._default_accessor

        accessor = self._default_accessor # FIXME (see above)
        
        if self._transpose_axes:
            roi_start = tuple(reversed(roi.start))
            roi_stop = tuple(reversed(roi.stop))
            result[:] = accessor.get_ndarray(roi_start, roi_stop).transpose()
        else:
            result[:] = accessor.get_ndarray(roi.start, roi.stop)
        return result

    def propagateDirty(self, *args):
        pass

