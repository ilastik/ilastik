import os
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io.blockwiseFileset import BlockwiseFileset
from lazyflow.operators import OpDummyData

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
        self._opDummyData = OpDummyData( parent=self )
        
    def setupOutputs(self):
        if not os.path.exists(self.DescriptionFilePath.value):
            raise OpBlockwiseFilesetReader.MissingDatasetError("Dataset description not found: {}".format( self.DescriptionFilePath.value ) )

        # Load up the class that does the real work
        self._blockwiseFileset = BlockwiseFileset( self.DescriptionFilePath.value )

        # Check for errors in the description file
        descriptionFields = self._blockwiseFileset.description
        axes = descriptionFields.axes
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)

        self.Output.meta.shape = tuple(descriptionFields.view_shape)
        self.Output.meta.dtype = descriptionFields.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(descriptionFields.axes)
        drange = descriptionFields.drange
        if drange is not None:
            self.Output.meta.drange = drange

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        try:
            self._blockwiseFileset.readData( (roi.start, roi.stop), result )
        except BlockwiseFileset.BlockNotReadyError:
            result[:] = self._opDummyData.execute( slot, subindex, roi, result )
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )
        
    def cleanUp(self):
        if self._blockwiseFileset is not None:
            self._blockwiseFileset.close()
        super(OpBlockwiseFilesetReader, self).cleanUp()

