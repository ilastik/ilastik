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
import httplib
import socket

import numpy
import vigra
from lazyflow.graph import Operator, OutputSlot
from lazyflow.roi import determineBlockShape

import pydvid

class OpDvidVolume(Operator):
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass
    
    def __init__(self, hostname, uuid, dataname, transpose_axes, *args, **kwargs):
        super( OpDvidVolume, self ).__init__(*args, **kwargs)
        self._transpose_axes = transpose_axes
        self._default_accessor = None
        self._throttled_accessor = None
        self._hostname = hostname
        self._uuid = uuid
        self._dataname = dataname

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
            self._connection = pydvid.dvid_connection.DvidConnection( self._hostname )
            self._default_accessor = pydvid.voxels.VoxelsAccessor( self._connection, self._uuid, self._dataname )
            self._throttled_accessor = pydvid.voxels.VoxelsAccessor( self._connection, self._uuid, self._dataname, throttle=True )
        except pydvid.errors.DvidHttpError as ex:
            if ex.status_code == httplib.NOT_FOUND:
                raise OpDvidVolume.DatasetReadError("Host not found: {}".format( self._hostname ))
            raise
        except socket.error as ex:
            import errno
            if ex.errno == errno.ECONNREFUSED:
                raise OpDvidVolume.DatasetReadError("Connection refused: {}".format( self._hostname ))
            raise
    
    def cleanUp(self):
        self._connection.close()
        super( OpDvidVolume, self ).cleanUp()
    
    def setupOutputs(self):
        shape, dtype, axiskeys = self._default_accessor.shape, self._default_accessor.dtype, self._default_accessor.axiskeys
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
        # TODO: Modify accessor implementation to accept a pre-allocated array.

        # For "heavy" requests, we'll use the throttled accessor
        HEAVY_REQ_SIZE = 256**3
        if numpy.prod(result.shape) > HEAVY_REQ_SIZE:
            accessor = self._throttled_accessor
        else:
            accessor = self._default_accessor
        
        if self._transpose_axes:
            roi_start = tuple(reversed(roi.start))
            roi_stop = tuple(reversed(roi.stop))
            result[:] = accessor.get_ndarray(roi_start, roi_stop).transpose()
        else:
            result[:] = accessor.get_ndarray(roi.start, roi.stop)
        return result

    def propagateDirty(self, *args):
        pass

