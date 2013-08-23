from functools import partial
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
        
        # Cmdline configuration functions are taken directly from DataExportApplet
        self.parse_known_cmdline_args = partial(DataExportApplet.parse_known_cmdline_args, self)
        self.configure_operator_with_parsed_args = partial(DataExportApplet.configure_operator_with_parsed_args, self)        
        
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
            self._gui = PixelClassificationDataExportGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )
        return self._gui





