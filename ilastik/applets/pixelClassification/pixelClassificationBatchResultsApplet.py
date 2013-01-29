from ilastik.applets.base.applet import Applet
from ilastik.applets.batchIo.batchIoSerializer import BatchIoSerializer
from opPixelClassificationBatchResults import OpPixelClassificationBatchResults

from ilastik.utility import OpMultiLaneWrapper

class PixelClassificationBatchResultsApplet( Applet ):
    """
    This a specialization of the generic batch results applet that
    provides a special viewer for pixel classification predictions.
    """
    def __init__( self, workflow, title ):
        # Operator is a subclass of the generic batch operator.
        self._topLevelOperator = OpMultiLaneWrapper( OpPixelClassificationBatchResults, parent=workflow, promotedSlotNames=set(['DatasetPath', 'ImageToExport', 'OutputFileNameBase']) )
        super(PixelClassificationBatchResultsApplet, self).__init__(title, syncWithImageIndex=False)

        # Serializer is the same as the batch io
        self._serializableItems = [ BatchIoSerializer(self._topLevelOperator, title) ]

        self._gui = None
        self._title = title
        
    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def getMultiLaneGui(self):
        if self._gui is None:
            # Gui is a special subclass of the generic gui
            from pixelClassificationBatchResultsGui import PixelClassificationBatchResultsGui
            self._gui = PixelClassificationBatchResultsGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )

        return self._gui





