from ilastik.applets.batchProcessing.batchProcessingApplet import BatchProcessingApplet
from ilastik.applets.counting.countingBatchProcessingGui import CountingBatchProcessingGui

class CountingBatchProcessingApplet(BatchProcessingApplet):
    def __init__(self, countingDataExportApplet, *args, **kwargs):
        super( CountingBatchProcessingApplet, self ).__init__( *args, **kwargs )
        self.countingDataExportApplet = countingDataExportApplet
    
    def getMultiLaneGui(self):
        if self._gui is None:
            self._gui = CountingBatchProcessingGui( self )
        return self._gui
