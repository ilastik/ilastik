from ilastik.applets.base.applet import Applet

from opBatchIo import OpBatchIo

from batchIoSerializer import BatchIoSerializer

from lazyflow.graph import OperatorWrapper

class BatchIoApplet( Applet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, title ):
        super(BatchIoApplet, self).__init__(title)

        self._topLevelOperator = OperatorWrapper( OpBatchIo, parent=workflow, promotedSlotNames=set(['DatasetPath', 'ImageToExport']) )
        
        # Ensure the operator has no length yet.
        # FIXME: Why is this necessary??!?! Shouldn't it be zero anyway?
        assert len(self._topLevelOperator.ImageToExport) == 0

        self._serializableItems = [ BatchIoSerializer(self._topLevelOperator, title) ]

        self._gui = None
        self._title = title
        
    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def gui(self):
        if self._gui is None:
            from batchIoGui import BatchIoGui
            self._gui = BatchIoGui( self._topLevelOperator, self.guiControlSignal, self.progressSignal, self._title )
        return self._gui







