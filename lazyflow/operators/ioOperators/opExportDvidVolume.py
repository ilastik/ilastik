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
import contextlib

import numpy

from lazyflow.graph import Operator, InputSlot
from lazyflow.utility import OrderedSignal, BigRequestStreamer
from lazyflow.roi import roiFromShape

from libdvid import DVIDException
from libdvid.voxels import VoxelsAccessor, VoxelsMetadata

import logging
logger = logging.getLogger(__name__)

class OpExportDvidVolume(Operator):
    Input = InputSlot()
    NodeDataUrl = InputSlot() # Should be a url of the form http://<hostname>[:<port>]/api/node/<uuid>/<dataname>
    OffsetCoord = InputSlot(optional=True)
    
    def __init__(self, transpose_axes, *args, **kwargs):
        super(OpExportDvidVolume, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()
        self._transpose_axes = transpose_axes

    # No output slots...
    def setupOutputs(self):
        if self._transpose_axes:
            assert self.Input.meta.axistags.channelIndex == len(self.Input.meta.axistags)-1
        else:
            assert self.Input.meta.axistags.channelIndex == 0
                    
    def execute(self, slot, subindex, roi, result): pass 
    def propagateDirty(self, slot, subindex, roi): pass

    def run_export(self):
        self.progressSignal(0)

        url = self.NodeDataUrl.value
        url_path = url.split('://')[1]
        hostname, api, node, uuid, dataname = url_path.split('/')
        assert api == 'api'
        assert node == 'node'
        
        axiskeys = self.Input.meta.getAxisKeys()
        shape = self.Input.meta.shape
        
        if self._transpose_axes:
            axiskeys = reversed(axiskeys)
            shape = tuple(reversed(shape))
        
        axiskeys = "".join( axiskeys )

        if self.OffsetCoord.ready():
            offset_start = self.OffsetCoord.value
        else:
            offset_start = (0,) * len( self.Input.meta.shape )

        self.progressSignal(5)
        
        # Get the dataset details
        try:
            metadata = VoxelsAccessor.get_metadata(hostname, uuid, dataname)
        except VoxelsAccessor.BadRequestError as ex:
            # Dataset doesn't exist yet.  Let's create it.
            metadata = VoxelsMetadata.create_default_metadata( shape, 
                                                               self.Input.meta.dtype, 
                                                               axiskeys, 
                                                               0.0, 
                                                               "" )
            VoxelsAccessor.create_new(hostname, uuid, dataname, metadata)

        # Since this class is generally used to push large blocks of data,
        #  we'll be nice and set throttle=True
        client = VoxelsAccessor( hostname, uuid, dataname, throttle=True )
        
        def handle_block_result(roi, data):
            # Send it to dvid
            roi = numpy.asarray(roi)
            roi += offset_start
            start, stop = roi
            if self._transpose_axes:
                data = data.transpose()
                start = tuple(reversed(start))
                stop = tuple(reversed(stop))
                client.post_ndarray( start, stop, data )
        requester = BigRequestStreamer( self.Input, roiFromShape( self.Input.meta.shape ) )
        requester.resultSignal.subscribe( handle_block_result )
        requester.progressSignal.subscribe( self.progressSignal )
        requester.execute()
        
        self.progressSignal(100)
    
        