from opPixelClassificationDataExport import OpPixelClassificationDataExport
from ilastik.applets.dataExport.dataExportApplet import DataExportApplet
from ilastik.applets.dataExport.dataExportSerializer import DataExportSerializer

from ilastik.utility import OpMultiLaneWrapper

class PixelClassificationDataExportApplet( DataExportApplet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for pixel classification predictions.
    """
    def __init__( self, workflow, title, isBatch=False ):
        # Our operator is a subclass of the generic data export operator
        self._topLevelOperator = OpMultiLaneWrapper( OpPixelClassificationDataExport, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Input', 'RawDatasetInfo', 'ConstraintDataset']) )
        self._gui = None
        self._title = title
        self._serializers = [ DataExportSerializer(self._topLevelOperator, title) ]

        # Base class init
        super(PixelClassificationDataExportApplet, self).__init__(workflow, title, isBatch)
        
    @property
    def dataSerializers(self):
        return self._serializers

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from pixelClassificationDataExportGui import PixelClassificationDataExportGui
            self._gui = PixelClassificationDataExportGui( self, self.topLevelOperator )
        return self._gui





