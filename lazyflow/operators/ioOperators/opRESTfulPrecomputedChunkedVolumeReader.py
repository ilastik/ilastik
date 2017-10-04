import os
import copy
import tempfile
import h5py
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io_util.RESTfulPrecomputedChunkedVolume import (
    RESTfulPrecomputedChunkedVolume
)
import lazyflow.roi
import logging

import numpy
logger = logging.getLogger(__name__)


class OpRESTfulPrecomputedChunkedVolumeReader(Operator):
    """
    An operator to retrieve precomputed chunked volumes from a remote server.
    These types of volumes are e.g. used in neuroglancer.
    """
    name = "OpRESTfulPrecomputedChunkedVolumeReader"

    # Base url of the chunked volume
    BaseUrl = InputSlot()

    # There is also the scale to configure
    Scale = InputSlot(optional=True)

    # Available scales of the data
    AvailableScales = OutputSlot()
    # The data itself
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpRESTfulPrecomputedChunkedVolumeReader, self).__init__(*args, **kwargs)
        self._axes = None
        self._volume_object = None

    def setupOutputs(self):
        # Create a RESTfulPrecomputedChunkedVolume object to handle
        if self._volume_object is not None:
            # check if the volume url has changed, to avoid downloading
            # info twice (i.e. setting up the volume twice)
            if self._volume_object.volume_url == self.BaseUrl.value:
                return

        self._volume_object = RESTfulPrecomputedChunkedVolume(self.BaseUrl.value)

        self._axes = self._volume_object.axes

        # scale needs to be defined for the following, so:
        # override whatever was set before to the lowest available scale:
        # is this a good idea? Triggers setupOutputs again
        self.Scale.setValue(self._volume_object._use_scale)
        self.AvailableScales.setValue(self._volume_object.available_scales)

        output_shape = tuple(self._volume_object.get_shape(scale=self.Scale.value))

        self.Output.meta.shape = output_shape
        self.Output.meta.dtype = self._volume_object.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(self._axes)
        self.AvailableScales.setValue(self._volume_object.available_scales)

    def execute(self, slot, subindex, roi, result):
        """
        Args:
            slot (TYPE): Description
            subindex (TYPE): Description
            roi (TYPE): we assume czyx order here
            result (TYPE): Description

        """
        pass

    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(slice(None))


if __name__ == '__main__':
    # assumes there is a server running at localhost
    logging.basicConfig(level=logging.DEBUG)
    volume_url = 'http://localhost:8080/precomputed/cremi'

    from lazyflow import graph
    g = graph.Graph()
    op = OpRESTfulPrecomputedChunkedVolumeReader(graph=g)
    op.BaseUrl.setValue(volume_url)
    print(f'available scales: {op.AvailableScales.value}')
    print(op.Scale.value)
