from lazyflow.graph import OperatorWrapper
from ilastik.utility import OperatorSubView


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

if __name__ == "__main__":
    from lazyflow.graph import Graph, Operator, InputSlot
    from ilastik.utility import MultiLaneOperatorABC
    
    class Op(Operator):
        Input = InputSlot()
    
    graph = Graph()
    op = OpAutoMultiLane( Op, graph=graph )
    
    assert isinstance( op, MultiLaneOperatorABC )
