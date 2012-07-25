from ilastik.ilastikshell.applet import Applet

from opBatchIo import OpBatchIo

from batchIoSerializer import BatchIoSerializer
from batchIoGui import BatchIoGui

from lazyflow.graph import OperatorWrapper

class BatchIoApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, graph, title ):
        super(BatchIoApplet, self).__init__(title)

        self._topLevelOperator = OperatorWrapper( OpBatchIo(graph=graph), promotedSlotNames=set(['DatasetPath', 'ImageToExport']) )
        
        # Ensure the operator has no length yet.
        # FIXME: Why is this necessary??!?! Shouldn't it be zero anyway?
        self._topLevelOperator.ImageToExport.resize(0)

        self._serializableItems = [ BatchIoSerializer(self._topLevelOperator, title) ]

        self._gui = BatchIoGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, title )
        
    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def gui(self):
        return self._gui







