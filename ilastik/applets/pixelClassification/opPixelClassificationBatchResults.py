from lazyflow.graph import InputSlot
from ilastik.applets.batchIo.opBatchIo import OpBatchIo


class OpPixelClassificationBatchResults( OpBatchIo ):
    
    # Add three additional input slots, to be used by the GUI.
    LabelColors = InputSlot()
    PmapColors = InputSlot()
    LabelNames = InputSlot()

