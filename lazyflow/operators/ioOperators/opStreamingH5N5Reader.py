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
# 		   http://ilastik.org/license/
###############################################################################
# Python
import logging
import time
import numpy
import vigra
import h5py
import z5py
import json
import os
import numpy as np

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility import Timer
from lazyflow.utility.helpers import get_default_axisordering, bigintprod

logger = logging.getLogger(__name__)


class OpStreamingH5N5Reader(Operator):
    """
    The top-level operator for the data selection applet.
    """

    name = "OpStreamingH5N5Reader"
    category = "Reader"

    # The project hdf5 File object (already opened)
    H5N5File = InputSlot(stype="h5N5File")

    # The internal path for project-local datasets
    InternalPath = InputSlot(stype="string")

    # Output data
    OutputImage = OutputSlot()

    H5EXTS = [".h5", ".hdf5", ".ilp"]
    N5EXTS = [".n5"]

    class DatasetReadError(Exception):
        def __init__(self, internalPath):
            self.internalPath = internalPath
            self.msg = f"Unable to open Hdf5 dataset: {internalPath}"
            super().__init__(self.msg)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h5N5File = None

    def setupOutputs(self):
        # Read the dataset meta-info from the HDF5 dataset
        self._h5N5File = self.H5N5File.value
        internalPath = self.InternalPath.value

        if internalPath not in self._h5N5File:
            raise OpStreamingH5N5Reader.DatasetReadError(internalPath)

        dataset = self._h5N5File[internalPath]

        try:
            # Read the axistags property without actually importing the data
            # Throws KeyError if 'axistags' can't be found
            axistagsJson = self._h5N5File[internalPath].attrs["axistags"]
            axistags = vigra.AxisTags.fromJSON(axistagsJson)
            axisorder = "".join(tag.key for tag in axistags)
            if "?" in axisorder:
                raise KeyError("?")
        except KeyError:
            # No axistags found.
            if "axes" in dataset.attrs:
                axisorder = "".join(dataset.attrs["axes"][::-1]).lower()
            else:
                axisorder = get_default_axisordering(dataset.shape)
            axistags = vigra.defaultAxistags(str(axisorder))

        assert len(axistags) == len(dataset.shape), f"Mismatch between shape {dataset.shape} and axisorder {axisorder}"

        # Configure our slot meta-info
        self.OutputImage.meta.dtype = dataset.dtype.type
        self.OutputImage.meta.shape = dataset.shape
        self.OutputImage.meta.axistags = axistags

        # If the dataset specifies a datarange, add it to the slot metadata
        if "drange" in self._h5N5File[internalPath].attrs:
            self.OutputImage.meta.drange = tuple(self._h5N5File[internalPath].attrs["drange"])

        # Same for display_mode
        if "display_mode" in self._h5N5File[internalPath].attrs:
            self.OutputImage.meta.display_mode = str(self._h5N5File[internalPath].attrs["display_mode"])

        total_volume = bigintprod(self._h5N5File[internalPath].shape)
        chunks = self._h5N5File[internalPath].chunks
        if not chunks and total_volume > 1e8:
            self.OutputImage.meta.inefficient_format = True
            logger.warning(
                f"This dataset ({self._h5N5File.filename}{internalPath}) is NOT chunked. "
                f"Performance for 3D access patterns will be bad!"
            )
        if chunks:
            self.OutputImage.meta.ideal_blockshape = chunks

    def execute(self, slot, subindex, roi, result):
        t = time.time()
        assert self._h5N5File is not None
        # Read the desired data directly from the hdf5File
        key = roi.toSlice()
        h5N5File = self._h5N5File
        internalPath = self.InternalPath.value

        timer = None
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Reading HDF5/N5 block: [{roi.start}, {roi.stop}]")
            timer = Timer()
            timer.unpause()

        if result.flags.c_contiguous:
            h5N5File[internalPath].read_direct(result[...], key)
        else:
            result[...] = h5N5File[internalPath][key]
        if logger.getEffectiveLevel() >= logging.DEBUG:
            t = 1000.0 * (time.time() - t)
            logger.debug("took %f msec." % t)

        if timer:
            timer.pause()
            logger.debug(f"Completed HDF5 read in {timer.seconds()} seconds: [{roi.start}, {roi.stop}]")

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.H5N5File or slot == self.InternalPath:
            self.OutputImage.setDirty(slice(None))

    @staticmethod
    def get_h5_n5_file(filepath, mode="a"):
        """
        returns, depending on the file-extension of filepath, either a hdf5 or a N5 file defined by filepath
        If the file is created when it does not exist depends on mode and on the function z5py.N5File/h5py.File.
        default mode = 'a':  Read/write if exists, create otherwise
        """
        name, ext = os.path.splitext(filepath)
        if ext in OpStreamingH5N5Reader.N5EXTS:
            return z5py.N5File(filepath, mode)
        elif ext in OpStreamingH5N5Reader.H5EXTS:
            return h5py.File(filepath, mode)
