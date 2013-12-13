import vigra
from lazyflow.graph import Operator, OutputSlot
from dvidclient.volume_client import VolumeClient
import httplib

class OpDvidVolume(Operator):
    Output = OutputSlot()

    class DatasetReadError(Exception):
        pass
    
    def __init__(self, transpose_axes, *args, **kwargs):
        super( OpDvidVolume, self ).__init__(*args, **kwargs)
        self._transpose_axes = transpose_axes
        self._volume_client = None

    def init_client(self, hostname, uuid, dataname):
        """
        Ideally, this would be run within the __init__ function,
        but operators should never raise non-fatal exceptions within Operator.__init__()
        (See OperatorMetaClass.__call__)
        This serves as an alternative init function, from which we are allowed to raise exceptions.
        """
        try:
            self._volume_client = VolumeClient( hostname, uuid, dataname )
        except VolumeClient.ErrorResponseException as ex:
            if ex.status_code == httplib.NOT_FOUND:
                raise OpDvidVolume.DatasetReadError()
            else:
                raise
    
    
    def setupOutputs(self):
        shape, dtype, axistags = self._volume_client.metainfo
        if self._transpose_axes:
            shape = tuple(reversed(shape))
            axistags = vigra.AxisTags( list(reversed(axistags)) )

        assert 0 <= axistags.index('c') == axistags.channelIndex < len(axistags), \
            "Invalid channel index: {}".format( axistags.channelIndex )

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

