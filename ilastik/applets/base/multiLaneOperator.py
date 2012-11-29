from abc import ABCMeta, abstractmethod
from lazyflow.graph import OperatorWrapper
from ilastik.utility.operatorSubView import OperatorSubView

def _has_attribute( cls, attr ):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False

class MultiLaneOperatorABC(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def addLane(self, laneIndex):
        """
        Add an image lane.
        """
        raise NotImplementedError

    @abstractmethod
    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane.
        """
        raise NotImplementedError

    @abstractmethod
    def getLane(self, laneIndex):
        raise NotImplementedError
    
    @classmethod
    def __subclasshook__(cls, C):
        if cls is MultiLaneOperatorABC:
            retval = True
            retval &= _has_attribute( cls, 'addLane' )
            retval &= _has_attribute( cls, 'removeLane' )
            retval &= _has_attribute( cls, 'getLane' )
            return retval
        return NotImplemented

class OpAutoMultiLane( OperatorWrapper ):
    """
    An extension of the OperatorWrapper that provides the functions needed to satisfy MultiLaneOperatorABC.
    """
    
    def addLane(self, laneIndex):
        """
        Add an image lane.
        """
        numLanes = len(self.innerOperators)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self._insertInnerOperator(numLanes, numLanes+1)

    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane.
        """
        numLanes = len(self.innerOperators)
        self._removeInnerOperator(laneIndex, numLanes-1)

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)
