from ilastik.applets.base.applet import Applet
from opDataExport import OpDataExport
from dataExportSerializer import DataExportSerializer
from ilastik.utility import OpMultiLaneWrapper

class DataExportApplet( Applet ):
    """
    
    """
    def __init__( self, workflow, title, isBatch=False ):
        self._topLevelOperator = OpMultiLaneWrapper( OpDataExport, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Input', 'RawDatasetInfo']) )
        # Users can temporarily disconnect the 'transaction' 
        #  slot to force all slots to be applied atomically.
        self._topLevelOperator.TransactionSlot.setValue(True)
        super(DataExportApplet, self).__init__(title, syncWithImageIndex=not isBatch)

        self._gui = None
        self._title = title
        self._serializers = [ DataExportSerializer(self._topLevelOperator, title) ]

        # This flag is set by the gui and checked by the workflow        
        self.busy = False
        
    @property
    def dataSerializers(self):
        return self._serializers

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            from dataExportGui import DataExportGui
            self._gui = DataExportGui( self, self._topLevelOperator )
        return self._gui
