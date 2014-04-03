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

import vigra
from lazyflow.graph import Operator, OutputSlot
import httplib
import socket

import pydvid

class OpDvidVolume(Operator):
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass
    
    def __init__(self, hostname, uuid, dataname, transpose_axes, *args, **kwargs):
        super( OpDvidVolume, self ).__init__(*args, **kwargs)
        self._transpose_axes = transpose_axes
        self._volume_client = None
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
            self._connection = httplib.HTTPConnection( self._hostname )
            self._volume_client = pydvid.voxels.VoxelsAccessor( self._connection, self._uuid, self._dataname )
        except pydvid.errors.ErrorResponseException as ex:
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
        shape, dtype, axiskeys = self._volume_client.shape, self._volume_client.dtype, self._volume_client.axiskeys
        if self._transpose_axes:
            shape = tuple(reversed(shape))
            axiskeys = "".join(reversed(axiskeys))

        self.Output.meta.shape = shape
        self.Output.meta.dtype = dtype
        self.Output.meta.axistags = vigra.defaultAxistags( axiskeys ) # FIXME: Also copy resolution, etc.

    def execute(self, slot, subindex, roi, result):
        # TODO: Modify volume client implementation to accept a pre-allocated array.
        if self._transpose_axes:
            roi_start = tuple(reversed(roi.start))
            roi_stop = tuple(reversed(roi.stop))
            result[:] = self._volume_client.get_ndarray(roi_start, roi_stop).transpose()
        else:
            result[:] = self._volume_client.get_ndarray(roi.start, roi.stop)
        return result
    
    def propagateDirty(self, *args):
        pass

