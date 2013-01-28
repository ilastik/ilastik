import os
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io.blockwiseFileset import BlockwiseFileset

import logging
logger = logging.getLogger(__name__)

class OpBlockwiseFilesetReader(Operator):
    """
    Adapter that provides an operator interface to the BlockwiseFileset class for reading ONLY.
    """
    name = "OpBlockwiseFilesetReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    class MissingDatasetError(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super(OpBlockwiseFilesetReader, self).__init__(*args, **kwargs)
        self._blockwiseFileset = None

    def setupOutputs(self):
        if not os.path.exists(self.DescriptionFilePath.value):
            raise OpBlockwiseFilesetReader.MissingDatasetError("Dataset description not found: {}".format( self.DescriptionFilePath.value ) )
        
        # Load up the class that does the real work
        self._blockwiseFileset = BlockwiseFileset( self.DescriptionFilePath.value )

        # Check for errors in the description file
        descriptionFields = self._blockwiseFileset.description
        axes = descriptionFields.axes
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)

        self.Output.meta.shape = descriptionFields.view_shape
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(descriptionFields.axes)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        try:
            self._blockwiseFileset.readData( (roi.start, roi.stop), result )
        except BlockwiseFileset.BlockNotReadyError:
            # Replace this entire request with a simple pattern to indicate "not available"
            pattern = numpy.indices( roi.stop - roi.start ).sum(0)
            pattern += roi.start.sum()
            pattern = ((pattern / 20) == (pattern + 10) / 20).astype(int)
            # If dtype is a float, use 0/1.
            # If its an int, use 0/255
            if isinstance(self.Output.meta.dtype(), numpy.integer):
                pattern *= 255
        
            result[:] = pattern
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )
        
    def cleanUp(self):
        if self._blockwiseFileset is not None:
            self._blockwiseFileset.close()
        super(OpBlockwiseFilesetReader, self).cleanUp()

