from ilastik.applets.base.applet import Applet
from ilastik.applets.batchIo.batchIoSerializer import BatchIoSerializer
from opCountingBatchResults import OpCountingBatchResults

from ilastik.utility import OpMultiLaneWrapper

class CountingBatchResultsApplet( Applet ):
    """
    This a specialization of the generic batch results applet that
    provides a special viewer for counting predictions.
    """
    def __init__( self, workflow, title ):
        # Operator is a subclass of the generic batch operator.
        self._topLevelOperator = OpMultiLaneWrapper( OpCountingBatchResults, parent=workflow,
                                     promotedSlotNames=set(['DatasetPath', 'ImageToExport', 'OutputFileNameBase', 'RawImage']) )
        super(CountingBatchResultsApplet, self).__init__(title, syncWithImageIndex=False)

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
            from countingBatchResultsGui import CountingBatchResultsGui
            self._gui = CountingBatchResultsGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )

        return self._gui





