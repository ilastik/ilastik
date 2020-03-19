import os
import logging

logger = logging.getLogger(__name__)

import numpy as np
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot

try:
    from quilted.h5blockstore import H5BlockStore
except ImportError:
    logger.debug("Couldn't import quilted")
else:

    class OpH5BlockStoreReader(Operator):
        IndexFilepath = InputSlot()
        Output = OutputSlot()

        SUBSTACK_PADDING = 20  # FIXME: Don't hard-code this!

        _opened_stores_this_process = set([])

        def __init__(self, *args, **kwargs):
            super(OpH5BlockStoreReader, self).__init__(*args, **kwargs)
            self._h5blockstore = None

        def setupOutputs(self):
            index_filepath = self.IndexFilepath.value
            root_dir = os.path.split(index_filepath)[0]

            # To ease debugging and recover from prior crashes, we reset the locks in each blockstore
            # we encounter, but only once, the first time we see it.
            reset_access = not index_filepath in OpH5BlockStoreReader._opened_stores_this_process
            OpH5BlockStoreReader._opened_stores_this_process.add(index_filepath)

            self._h5blockstore = H5BlockStore(root_dir, reset_access=reset_access)

            bounds_list = self._h5blockstore.get_block_bounds_list()
            max_bounds = np.array(bounds_list)[:, 1].max(axis=0)

            for i, axis in enumerate(self._h5blockstore.axes):
                if axis != "c":
                    max_bounds[i] -= self.SUBSTACK_PADDING  # FIXME: Don't hard-code this

            self.Output.meta.shape = tuple(max_bounds)
            self.Output.meta.dtype = self._h5blockstore.dtype.type
            self.Output.meta.axistags = vigra.defaultAxistags(self._h5blockstore.axes)

        def execute(self, slot, subindex, roi, result):
            self._h5blockstore.export_to_array((roi.start, roi.stop), self._remove_block_halo, out=result)

        def propagateDirty(self, slot, subindex, roi):
            assert slot == self.IndexFilepath
            self.Output.setDirty(slice(None))

        def _remove_block_halo(self, block_bounds):
            block_bounds = np.array(block_bounds)
            for i, axis in enumerate(self._h5blockstore.axes):
                if axis != "c":
                    block_bounds[0, i] += self.SUBSTACK_PADDING
                    block_bounds[1, i] -= self.SUBSTACK_PADDING
            return block_bounds
