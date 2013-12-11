import vigra
from lazyflow.graph import Operator, OutputSlot
from dvidclient.volume_client import VolumeClient

class OpDvidVolume(Operator):
    Output = OutputSlot()
    
    def __init__(self, hostname, uuid, dataname, transpose_axes, *args, **kwargs):
        super( OpDvidVolume, self ).__init__(*args, **kwargs)
        self._volume_client = VolumeClient( hostname, uuid, dataname )
        self._transpose_axes = transpose_axes
    
    def setupOutputs(self):
        shape, dtype, axistags = self._volume_client.metainfo
        if self._transpose_axes:
            shape = tuple(reversed(shape))
            axistags = vigra.AxisTags( list(reversed(axistags)) )

        assert 0 <= axistags.index('c') < len(axistags), "Invalid channel index: {}".format( axistags.index('c') )
        assert 0 <= axistags.channelIndex < len(axistags), "Invalid channel index: {}".format( axistags.channelIndex ) 

        self.Output.meta.shape = shape
        self.Output.meta.dtype = dtype
        self.Output.meta.axistags = axistags

    def execute(self, slot, subindex, roi, result):
        # TODO: Modify volume client implementation to accept a pre-allocated array.
        if self._transpose_axes:
            roi_start = tuple(reversed(roi.start))
            roi_stop = tuple(reversed(roi.stop))
            result[:] = self._volume_client.retrieve_subvolume(roi_start, roi_stop).transpose()
        else:
            result[:] = self._volume_client.retrieve_subvolume(roi.start, roi.stop)
        return result
    
    def propagateDirty(self, *args):
        pass

