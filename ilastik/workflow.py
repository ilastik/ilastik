from abc import abstractproperty, abstractmethod
from lazyflow.graph import Operator

class Workflow( Operator ):
    """
    Base class for all workflows.
    """
    name = "Workflow (base class)"
    
    ###############################
    # Abstract methods/properties #
    ###############################
    
    @abstractproperty
    def applets(self):
        """
        Abstract property. Return the list of applets that are owned by this workflow.
        """
        return []

    @abstractproperty
    def imageNameListSlot(self):
        """
        Abstract property.  Return the "image name list" slot, which lists the names of 
        all image lanes (i.e. files) currently loaded by the workflow.
        This slot is typically provided by the DataSelection applet via its ImageName slot.
        """
        return None

    @abstractmethod
    def connectLane(self, laneIndex):
        """
        When a new image lane has been added to the workflow, this workflow base class does the following:
        
        1) Create room for the new image lane by adding a lane to each applet's topLevelOperator
        2) Ask the subclass to hook up the new image lane by calling this function.
        """
        raise NotImplementedError

    ##################
    # Public methods #
    ##################

    def __init__(self, headless, *args, **kwargs):
        """
        Constructor.  Subclasses MUST call this in their own ``__init__`` functions.
        The args and kwargs parameters will be passed directly to the Operator base class.
        The graph argument should be included.
        
        :param headless: Set to True if this workflow is being instantiated by a "headless" script, 
                         in which case the workflow should not attempt to access applet GUIs.
        """
        super(Workflow, self).__init__(*args, **kwargs)
        self._headless = headless

    def cleanUp(self):
        """
        The user closed the project, so this workflow is being destroyed.  
        Tell the applet GUIs to stop processing data, and free any resources that are owned by this workflow or its applets.
        """
        if not self._headless:
            # Stop and clean up the GUIs before we invalidate the operators they depend on.
            for a in self.applets:
                a.getMultiLaneGui().stopAndCleanUp()
        
        # Clean up the graph as usual.
        super(Workflow, self).cleanUp()

    ###################
    # Private methods #
    ###################

    def _after_init(self):
        """
        Overridden from Operator.
        """
        Operator._after_init(self)

        # When a new image is added to the workflow, each applet should get a new lane.
        self.imageNameListSlot.notifyInserted( self._createNewImageLane )
        self.imageNameListSlot.notifyRemove( self._removeImageLane )
        
    def _createNewImageLane(self, multislot, index, *args):
        """
        A new image lane is being added to the workflow.  Add a new lane to each applet and hook it up.
        """
        for a in self.applets:
            if a.syncWithImageIndex and a.topLevelOperator is not None:
                a.topLevelOperator.addLane(index)
        
        self.connectLane(index)

        if not self._headless:
            for a in self.applets:
                a.getMultiLaneGui().imageLaneAdded(index)
    
    def _removeImageLane(self, multislot, index, finalLength):
        """
        An image lane is being removed from the workflow.  Remove it from each of the applets.
        """
        if not self._headless:
            for a in self.applets:
                a.getMultiLaneGui().imageLaneRemoved(index, finalLength)

        for a in self.applets:
            if a.syncWithImageIndex and a.topLevelOperator is not None:
                a.topLevelOperator.removeLane(index, finalLength)
