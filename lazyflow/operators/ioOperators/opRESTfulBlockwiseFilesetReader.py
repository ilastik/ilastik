import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.utility.io.RESTfulBlockwiseFileset import RESTfulBlockwiseFileset

import logging
logger = logging.getLogger(__name__)

class OpRESTfulBlockwiseFilesetReader(Operator):
    """
    Adapter that provides an operator interface to the BlockwiseFileset class for reading ONLY.
    """
    name = "OpRESTfulBlockwiseFilesetReader"

    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpRESTfulBlockwiseFilesetReader, self).__init__(*args, **kwargs)
        self._blockwiseFileset = None

    def setupOutputs(self):
        # Load up the class that does the real work
        self._blockwiseFileset = RESTfulBlockwiseFileset( self.DescriptionFilePath.value )

        # Check for errors in the description file
        localDescription = self._blockwiseFileset.compositeDescription.local_description
        axes = localDescription.axes
        assert False not in map(lambda a: a in 'txyzc', axes), "Unknown axis type.  Known axes: txyzc  Your axes:".format(axes)

        self.Output.meta.shape = localDescription.view_shape
        self.Output.meta.dtype = localDescription.dtype
        self.Output.meta.axistags = vigra.defaultAxistags(localDescription.axes)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.Output, "Unknown output slot"
        self._blockwiseFileset.readData( (roi.start, roi.stop), result )
        return result

    def propagateDirty(self, slot, subindex, roi):
        assert slot == self.DescriptionFilePath, "Unknown input slot."
        self.Output.setDirty( slice(None) )

