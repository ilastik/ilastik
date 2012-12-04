from abc import abstractproperty, abstractmethod
from lazyflow.graph import Operator

class Workflow( Operator ):
    
    def __init__(self, headless, *args, **kwargs):
        super(Workflow, self).__init__(*args, **kwargs)
        self._headless = headless
    
    @abstractproperty
    def applets(self):
        return []

    @abstractproperty
    def imageNameListSlot(self):
        return None

    @abstractmethod
    def connectLane(self):
        raise NotImplementedError

    def _after_init(self):
        """
        Overridden from Operator.
        """
        Operator._after_init(self)

        # When a new image is added to the workflow, each applet should get a new lane.
        self.imageNameListSlot.notifyInserted( self._createNewImageLane )
        self.imageNameListSlot.notifyRemove( self._removeImageLane )
        
    def _createNewImageLane(self, multislot, index, *args):
        for a in self.applets:
            if a.syncWithImageIndex and a.topLevelOperator is not None:
                a.topLevelOperator.addLane(index)
        
        self.connectLane(index)
    
    def _removeImageLane(self, multislot, index, finalLength):
        for a in self.applets:
            if a.syncWithImageIndex and a.topLevelOperator is not None:
                a.topLevelOperator.removeLane(index, finalLength)

    def cleanUp(self):
        if not self._headless:
            # Stop and clean up the GUIs before we invalidate the operators they depend on.
            for a in self.applets:
                a.getMultiLaneGui().stopAndCleanUp()
        
        # Clean up the graph as usual.
        super(Workflow, self).cleanUp()
