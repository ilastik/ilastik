from ilastik.applets.base.applet import Applet
from opDataExport import OpDataExport
from ilastik.utility import OpMultiLaneWrapper

class DataExportApplet( Applet ):
    """
    
    """
    def __init__( self, workflow, title, isBatch=False ):
        self._topLevelOperator = OpMultiLaneWrapper( OpDataExport, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Input', 'RawDatasetInfo']) )
        super(DataExportApplet, self).__init__(title, syncWithImageIndex=not isBatch)

        self._gui = None
        self._title = title
        
    @property
    def dataSerializers(self):
        return []

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            from dataExportGui import DataExportGui
            self._gui = DataExportGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )
        return self._gui
