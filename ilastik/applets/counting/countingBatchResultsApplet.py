from opCountingBatchResults import OpCountingBatchResults
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.dataExport.dataExportSerializer import DataExportSerializer

from ilastik.utility import OpMultiLaneWrapper

class CountingBatchResultsApplet( DataExportApplet ):
    """
    This a specialization of the generic batch results applet that
    provides a special viewer for counting predictions.
    """
    def __init__( self, workflow, title, isBatch=True):
        # Our operator is a subclass of the generic data export operator
        self._topLevelOperator = OpMultiLaneWrapper( OpCountingBatchResults, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Input', 'RawDatasetInfo']) )
        self._gui = None
        self._title = title
        self._serializers = [ DataExportSerializer(self._topLevelOperator, title) ]

        # Base class init
        super(CountingBatchResultsApplet, self).__init__(workflow, title, isBatch)
        
    @property
    def dataSerializers(self):
        return self._serializers

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from countingBatchResultsGui import CountingBatchResultsGui
            self._gui = CountingBatchResultsGui( self, self.topLevelOperator )
        return self._gui





