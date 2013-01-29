from lazyflow.graph import InputSlot
from ilastik.applets.batchIo.opBatchIo import OpBatchIo


class OpPixelClassificationBatchResults( OpBatchIo ):
    # Add these additional input slots, to be used by the GUI.
    PmapColors = InputSlot()
    LabelNames = InputSlot()

