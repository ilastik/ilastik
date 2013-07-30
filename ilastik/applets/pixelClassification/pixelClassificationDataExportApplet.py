from ilastik.applets.base.applet import Applet
from opPixelClassificationDataExport import OpPixelClassificationDataExport

from ilastik.utility import OpMultiLaneWrapper

class PixelClassificationDataExportApplet( Applet ):
    """
    This a specialization of the generic data export applet that
    provides a special viewer for pixel classification predictions.
    """
    def __init__( self, workflow, title, isBatch=False ):
        # Our operator is a subclass of the generic data export operator
        self._topLevelOperator = OpMultiLaneWrapper( OpPixelClassificationDataExport, parent=workflow,
                                     promotedSlotNames=set(['RawData', 'Input', 'RawDatasetInfo']) )
        # Users can temporarily disconnect the 'transaction' 
        #  slot to force all slots to be applied atomically.
        self._topLevelOperator.TransactionSlot.setValue(True)

        super(PixelClassificationDataExportApplet, self).__init__(title, syncWithImageIndex=not isBatch)

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
            # Gui is a special subclass of the generic gui
            from pixelClassificationDataExportGui import PixelClassificationDataExportGui
            self._gui = PixelClassificationDataExportGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )
        return self._gui





