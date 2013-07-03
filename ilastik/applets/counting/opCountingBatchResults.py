from lazyflow.graph import InputSlot
from ilastik.applets.batchIo.opBatchIo import OpBatchIo


class OpCountingBatchResults( OpBatchIo ):
    # Add these additional input slots, to be used by the GUI.
    PmapColors = InputSlot()
    LabelNames = InputSlot()

