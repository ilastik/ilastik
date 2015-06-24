import os
import glob

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

    :param globstring: A glob string as defined by the glob module. We
        also support the following special extension to globstring
        syntax: A single string can hold a *list* of globstrings. 
        The delimiter that separates the globstrings in the list is 
        OS-specific via os.path.pathsep.
        
        For example, on Linux the pathsep is':', so

            '/a/b/c.txt:/d/e/f.txt:../g/i/h.txt'

        is parsed as

            ['/a/b/c.txt', '/d/e/f.txt', '../g/i/h.txt']

    """
    GlobString = InputSlot()
    SequenceAxis = InputSlot(optional=True) # The axis to stack across.
    Output = OutputSlot()

    class WrongFileTypeError( Exception ):
        def __init__(self, filename):
            self.filename = filename
            self.msg = "File is not a TIFF: {}".format(filename)
            super(OpTiffSequenceReader.WrongFileTypeError, self).__init__( self.msg )    

    class FileOpenError( Exception ):
        def __init__(self, filename):
            self.filename = filename
            self.msg = "Unable to open file: {}".format(filename)
            super(OpTiffSequenceReader.FileOpenError, self).__init__( self.msg )    

    def __init__(self, *args, **kwargs):
        super( OpTiffSequenceReader, self ).__init__( *args, **kwargs )
        self._readers = []
        self._opStacker = OpMultiArrayStacker( parent=self )
        self._opStacker.AxisIndex.setValue(0)
        self.Output.connect( self._opStacker.Output )
    
    def cleanUp(self):
        self._opStacker.Images.resize(0)
        for opReader in self._readers:
            opReader.cleanUp()
        super( OpTiffSequenceReader, self ).cleanUp()
    
    def setupOutputs(self):
        file_paths = self.expandGlobStrings(self.GlobString.value)
        for filename in file_paths:
            if os.path.splitext(filename)[1] not in OpTiffReader.TIFF_EXTS:
                raise OpTiffSequenceReader.WrongFileTypeError(filename)

        num_files = len(file_paths)
        if num_files == 0:
            self.stack.meta.NOTREADY = True
            return

        try:
            opFirstImg = OpTiffReader(parent=self)
            opFirstImg.Filepath.setValue( file_paths[0] )
            slice_axes = opFirstImg.Output.meta.getAxisKeys()
            opFirstImg.cleanUp()
        except RuntimeError as e:
            logger.error(str(e))
            raise OpTiffSequenceReader.FileOpenError(file_paths[0])

        if self.SequenceAxis.ready():
            new_axis = self.SequenceAxis.value
            assert len(new_axis) == 1
            assert new_axis in 'tzyxc'
        else:
            # Try to pick an axis that doesn't already exist in each tiff
            for new_axis in 'tzc0':
                if new_axis not in slice_axes:
                    break
    
            if new_axis == '0':
                # All axes used already.
                # Stack across first existing axis
                new_axis = slice_axes[0]            

        self._opStacker.Images.resize(0)
        self._opStacker.Images.resize(num_files)
        self._opStacker.AxisFlag.setValue(new_axis)
        
        for opReader in self._readers:
            opReader.cleanUp()

        self._readers = []
        for filename, stacker_slot in zip(file_paths, self._opStacker.Images):
            opReader = OpTiffReader( parent=self )
            try:
                opReader.Filepath.setValue( filename )
            except RuntimeError as e:
                logger.error(str(e))
                raise OpTiffSequenceReader.FileOpenError(file_paths[0])
            else:
                stacker_slot.connect( opReader.Output )
                self._readers.append( opReader )            

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.GlobString
        # Any change to the globstring means our entire output is dirty.
        self.Output.setDirty()

    @staticmethod
    def expandGlobStrings(globStrings):
        ret = []
        # Parse list into separate globstrings and combine them
        for globString in globStrings.split(os.path.pathsep):
            s = globString.strip()
            ret += sorted(glob.glob(s))
        return ret
