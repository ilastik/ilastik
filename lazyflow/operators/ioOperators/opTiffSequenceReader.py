from builtins import zip
from ilastik.utility.data_url import SimpleDataPath

import os
import glob
from typing import List

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.generic import OpMultiArrayStacker
from lazyflow.operators.ioOperators.opTiffReader import OpTiffReader

import logging

logger = logging.getLogger(__name__)


class OpTiffSequenceReader(Operator):
    """
    Imports a sequence of (possibly ND) tiffs into a single volume (ND+1)

    Note: This operator does NOT cache the images, so direct access
          via the execute() function is very inefficient, especially
          through the Z-axis. Typically, you'll want to connect this
          operator to a cache whose block size is large in the X-Y
          plane.
    """

    DataPaths = InputSlot()  # List[SimpleDataPath]
    SequenceAxis = InputSlot(optional=True)  # The axis to stack across.
    Output = OutputSlot()

    class WrongFileTypeError(Exception):
        def __init__(self, filename):
            self.filename = filename
            self.msg = "File is not a TIFF: {}".format(filename)
            super(OpTiffSequenceReader.WrongFileTypeError, self).__init__(self.msg)

    class FileOpenError(Exception):
        def __init__(self, filename):
            self.filename = filename
            self.msg = "Unable to open file: {}".format(filename)
            super(OpTiffSequenceReader.FileOpenError, self).__init__(self.msg)

    def __init__(self, *args, **kwargs):
        super(OpTiffSequenceReader, self).__init__(*args, **kwargs)
        self._readers = []
        self._opStacker = OpMultiArrayStacker(parent=self)
        self._opStacker.AxisIndex.setValue(0)

    def cleanUp(self):
        self._opStacker.Images.resize(0)
        for opReader in self._readers:
            opReader.cleanUp()
        super(OpTiffSequenceReader, self).cleanUp()

    def setupOutputs(self):
        data_paths: List[SimpleDataPath] = self.DataPaths.value
        for data_path in data_paths:
            if data_path.file_path.suffix.lower() not in OpTiffReader.TIFF_EXTS:
                raise OpTiffSequenceReader.WrongFileTypeError(str(data_path.file_path))

        self.Output.connect(self._opStacker.Output)
        first_data_path = data_paths[0]
        try:
            opFirstImg = OpTiffReader(parent=self)
            opFirstImg.Filepath.setValue(str(first_data_path.file_path))
            slice_axes = opFirstImg.Output.meta.getAxisKeys()
            opFirstImg.cleanUp()
        except RuntimeError as e:
            logger.error(str(e))
            raise OpTiffSequenceReader.FileOpenError(str(first_data_path.file_path))

        if self.SequenceAxis.ready():
            new_axis: str = self.SequenceAxis.value
            assert len(new_axis) == 1
            assert new_axis in "tzyxc"
        else:
            # Try to pick an axis that doesn't already exist in each tiff
            for new_axis in "tzc":
                if new_axis not in slice_axes:
                    break
            else:
                # All axes used already.
                # Stack across first existing axis
                new_axis = slice_axes[0]

        self._opStacker.Images.resize(0)
        self._opStacker.Images.resize(len(data_paths))
        self._opStacker.AxisFlag.setValue(new_axis)

        for opReader in self._readers:
            opReader.cleanUp()

        self._readers = []
        for data_path, stacker_slot in zip(data_paths, self._opStacker.Images):
            file_path = str(data_path.file_path)
            opReader = OpTiffReader(parent=self)
            try:
                opReader.Filepath.setValue(file_path)
            except RuntimeError as e:
                logger.error(str(e))
                raise OpTiffSequenceReader.FileOpenError(file_path)
            else:
                stacker_slot.connect(opReader.Output)
                self._readers.append(opReader)

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DataPaths
        # Any change to the globstring means our entire output is dirty.
        self.Output.setDirty()
