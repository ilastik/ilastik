import vigra

from dvidclient.volume_client import VolumeClient
from dvidclient.volume_metainfo import MetaInfo

from lazyflow.graph import Operator, InputSlot
from lazyflow.utility import OrderedSignal
from lazyflow.roi import roiFromShape

import logging
logger = logging.getLogger(__name__)

class OpExportDvidVolume(Operator):
    Input = InputSlot()
    NodeDataUrl = InputSlot() # Should be a url of the form http://<hostname>[:<port>]/api/node/<uuid>/<dataname>
    
    def __init__(self, *args, **kwargs):
        super(OpExportDvidVolume, self).__init__(*args, **kwargs)
        self.progressSignal = OrderedSignal()

    # No output slots...
    def setupOutputs(self):
        assert self.Input.meta.axistags.channelIndex == 0, \
            "DVID volumes must be exported in fortran order."
        
    def execute(self, slot, subindex, roi, result): pass 
    def propagateDirty(self, slot, subindex, roi): pass

    def run_export(self):
        self.progressSignal(0)

        url = self.NodeDataUrl.value
        url_path = url.split('://')[1]
        hostname, api, node, uuid, dataname = url_path.split('/')
        assert api == 'api'
        assert node == 'node'
        
        # FIXME: We assume the dataset needs to be created first.
        #        If it already existed, this (presumably) causes an error on the DVID side.
        metainfo = MetaInfo( self.Input.meta.shape,
                             self.Input.meta.dtype,
                             self.Input.meta.axistags )

        self.progressSignal(5)
        VolumeClient.create_volume(hostname, uuid, dataname, metainfo)

        client = VolumeClient( hostname, uuid, dataname )
        
        # For now, we send the whole darn thing at once.
        # TODO: Stream it over in blocks...
        
        # Request the data
        data = vigra.taggedView( self.Input[:].wait(), metainfo.axistags )
        
        # Send it to dvid
        start, stop = roiFromShape(data.shape)
        client.modify_subvolume( start, stop, data )
        
        self.progressSignal(100)
    
        