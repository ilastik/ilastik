from abc import ABCMeta, abstractmethod

def _has_attribute( cls, attr ):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False

class MultiLaneOperatorABC(object):
    """
    This abstract base class specifies the interface to which all top-level applet operators must adhere.
    The distinguishing characteristic of a top-level operator is the fact that they must be capable of 
    supporting multiple images via multi-slots that are indexed by image lane number.
    
    Image lanes of the top-level operator are added, removed, and accessed via the ``addLane``, ``removeLane``, and ``getLane`` functions.
    
    .. note:: Most applets can simply inherit from the :py:class:`StandardApplet <ilastik.applets.base.standardApplet.StandardApplet>` base class, 
              which will automatically adapt single-lane top-level operators to satisfy this interface. 
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def addLane(self, laneIndex):
        """
        Add an image lane.  Called by the workflow when the user has added a new image to the pipeline.
        
        *Postcondition:* The operator must be fully prepared to accept a new image.
                         All input and output slots that are used by the image lane must be resized.
                         Any internal operators that are part of the lane must be expanded).
        
        .. note:: Multi-slots that are connected together are auto-resized to stay in sync.  
                  To resize a network of connected multi-slots (including OperatorWrapper inputs and 
                  outputs), it is generally sufficient to resize only one of the multi-slots.  
                  The others will auto-resize to adjust.  See lazyflow documentation for details.  
                  If your operator has any slots that are NOT connected to the rest of the inputs or 
                  outputs, then be sure to resize it explicitly in this function.
        """
        raise NotImplementedError

    @abstractmethod
    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane.  Called by the workflow when the user has removed an image from the pipeline.
        
        *Postcondition:* The lane must be removed from all slots that were added in :py:func:`addLane()`
        
        .. note:: See note in :py:func:`addLane()` documentation.
        """
        raise NotImplementedError

    @abstractmethod
    def getLane(self, laneIndex):
        """
        Get an object that exposes the relevant slots for the specific lane.
        The object may be an operator, or may merely be an operator-like "view" object.
        """
        raise NotImplementedError
    
    @classmethod
    def __subclasshook__(cls, C):
        """
        This function allows us to compare objects to the MultiLaneOperator interface
        even if they don't happen to inherit from this base class.
        """
        if cls is MultiLaneOperatorABC:
            retval = True
            retval &= _has_attribute( C, 'addLane' )
            retval &= _has_attribute( C, 'removeLane' )
            retval &= _has_attribute( C, 'getLane' )
            return retval
        return NotImplemented
