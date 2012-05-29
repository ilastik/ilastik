from ilastikshell.applet import Applet

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
        self._topLevelOperator.ImageToExport.resize(0)

        self._serializableItems = [ BatchIoSerializer(self._topLevelOperator, title) ]

        # Instantiate the main GUI, which creates the applet drawers
        self._centralWidget = BatchIoGui( self._topLevelOperator )
        self._menuWidget = self._centralWidget.menuBar
        
        # The central widget owns the applet drawer gui
        self._drawers = [ (title, self._centralWidget.drawer) ]
        
        # No preferences manager
        self._preferencesManager = None
    
    @property
    def centralWidget( self ):
        return self._centralWidget

    @property
    def appletDrawers(self):
        return self._drawers
    
    @property
    def menuWidget( self ):
        return self._menuWidget

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
         return self._preferencesManager
