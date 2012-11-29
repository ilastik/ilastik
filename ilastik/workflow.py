from abc import abstractproperty, abstractmethod

from lazyflow.graph import Operator

class Workflow( Operator ):
    
    @abstractproperty
    def applets(self):
        return []

    @abstractproperty
    def imageNameListSlot(self):
        return None

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
            if a.topLevelOperator is not None:
                a.topLevelOperator.addLane(index)
        
        self.connectLane(index)
    
    def _removeImageLane(self, multislot, index, finalLength):
        for a in self.applets:
            if a.topLevelOperator is not None:
                a.topLevelOperator.removeLane(index, finalLength)

    @abstractmethod
    def connectLane(self):
        raise NotImplementedError

