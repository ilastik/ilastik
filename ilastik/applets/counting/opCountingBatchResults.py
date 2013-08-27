from lazyflow.graph import InputSlot
from ilastik.applets.dataExport.opDataExport import OpDataExport

class OpCountingBatchResults( OpDataExport ):
    # Add these additional input slots, to be used by the GUI.
    PmapColors = InputSlot()
    LabelNames = InputSlot()
