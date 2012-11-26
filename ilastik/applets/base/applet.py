from ilastik.utility.simpleSignal import SimpleSignal
from ilastik.utility.operatorSubView import OperatorSubView

from abc import ABCMeta, abstractproperty, abstractmethod

class Applet( object ):
    """
    Base class for all applets.
    """
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties

    _base_initialized = False
    
    def __init__( self, name ):
        """
        Constructor.  Subclasses must call this base implementation in their own __init__ methods.  If they fail to do so, the shell raises an exception.
            
            *name*: The applet's name, used for debugging purposes. 
        """
        self.name = name

        #: Progress signal.
        #: When the applet is doing something time-consuming, this signal tells the shell to show a progress bar.
        #: Signature: ``emit(percentComplete, canceled=false)``
        self.progressSignal = SimpleSignal()
        
        #: GUI control signal
        #: See the ControlCommand class (below) for an enumerated list of the commands supported by this signal)
        #: Signature: ``emit(command=ControlCommand.DisableAll)`` 
        self.guiControlSignal = SimpleSignal()

        #: Shell request signal is used to trigger certain shell actions.
        #: Signature: ``emit(request)``
        #: where``request`` is an integer corresponding to the action the shell should take.  The allowable actions are enumerated in the ShellRequest class (see below).
        #: Example: self.shellRequest(ShellRequest.RequestSave)
        self.shellRequestSignal = SimpleSignal()

        self._base_initialized = True

    @abstractproperty
    def topLevelOperator(self):
        """
        Abstract property.
        The applet's Top Level Operator, which is a single operator for all computation performed by the applet.
        Each applet has exactly one top-level operator for performing computations.
        Workflow managers can connect the top-level operator of one applet to others.
        """
        return None

    def topLevelOperatorForLane(self, laneIndex):
        """
        Return a view of the top-level operator for the given lane.
        """
        return OperatorSubView(self.topLevelOperator, laneIndex)

    @abstractmethod
    def addLane(self, laneIndex):
        """
        Add an image processing lane to the top-level operator.
        """
        raise NotImplementedError

    @abstractmethod
    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image processing lane from the top-level operator.
        """
        raise NotImplementedError

    @abstractproperty
    def gui(self):
        """
        Abstract property.
        Provides the applet's GUI, which must be an instance of AppletGuiInterface.
        """
        raise NotImplementedError

    @property
    def dataSerializers(self):
        """
        A list of dataSerializer objects for loading/saving any project data the applet is responsible for.
        Subclasses should override this property.  By default, returns [].
        """ 
        return []
    
    @property
    def base_initialized(self):
        # Do not override this property.
        # Used by the shell to ensure that Applet.__init__ was called by your subclass.
        return self._base_initialized

class ControlCommand(object):
    """
    This class enumerates the GUI control commands that applets can ask the shell to perform via the guiControlSignal.
    Gui control commands are used to prevent the user from altering upstream or downstream applet settings while an applet is performing some long-running task.
    """
    Pop = 0                 #: Undo the most recent command that the issuing applet sent
    DisableAll = 1          #: Disable all applets in the workflow
    DisableUpstream = 2     #: Disable applets that come before the applet that is issuing the command
    DisableDownstream = 3   #: Disable applets that come after the applet that is issuing the command
    DisableSelf = 4         #: Disable the applet that is issuing the command

class ShellRequest(object):
    """
    This class enumerates the actions that applets can ask the shell to perform via the shellRequest signal.
    At the moment, there is only one supported action (save).
    """
    RequestSave = 0 #: Request that the shell perform a "save project" action.


from lazyflow.graph import OperatorWrapper
class SingleToMultiAppletAdapter( Applet ):

    def __init__(self, name, workflow):
        super(SingleToMultiAppletAdapter, self).__init__(name)
        self._topLevelOperator = OperatorWrapper(self.operatorClass, parent=workflow)
        self._gui = None

    @abstractproperty
    def operatorClass(self):
        raise NotImplementedError

    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    def topLevelOperatorForLane(self, laneIndex):
        return OperatorSubView(self.topLevelOperator, laneIndex)

    def addLane(self, laneIndex):
        """
        Add an image lane to the top-level operator.
        Since the top-level operator is just an OperatorWrapper, this is simple.
        """
        numLanes = len(self.topLevelOperator.innerOperators)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.topLevelOperator._insertInnerOperator(numLanes, numLanes+1)
        
    def removeLane(self, laneIndex, finalLength):
        """
        Remove an image lane from the top-level operator.
        Since the top-level operator is just an OperatorWrapper, this is simple.
        """
        numLanes = len(self.topLevelOperator.innerOperators)
        self.topLevelOperator._removeInnerOperator(laneIndex, numLanes-1)

    @property
    def gui(self):
        if self._gui is None:
            self._gui = SingleToMultiGuiAdapter( self.guiClass, self._topLevelOperator )
        return self._gui

def checkCurrentGui(f):
    def _wrapper(self, *args, **kwargs):
        if self.currentGui() is None:
            return None
        else:
            return f(self, *args, **kwargs)
    return _wrapper
    
class SingleToMultiGuiAdapter( object ):
    def __init__(self, singleImageGuiClass, topLevelOperator):
        self._singleImageGuiClass = singleImageGuiClass
        self._imageIndex = None
        self._guis = {}
        self.topLevelOperator = topLevelOperator

    def currentGui(self):
        if self._imageIndex is None:
            return None
        # Create first if necessary
        if self._imageIndex not in self._guis:
            self._guis[self._imageIndex] = self._singleImageGuiClass( self.topLevelOperator.innerOperators[self._imageIndex] )
        return self._guis[self._imageIndex]

    def appletDrawers(self):
        if self.currentGui() is not None:
            return self.currentGui().appletDrawers()
        else:
            return self._singleImageGuiClass.defaultAppletDrawers()

    @checkCurrentGui
    def centralWidget( self ):
        return self.currentGui().centralWidget()

    @checkCurrentGui
    def menus(self):
        return self.currentGui().menus()
    
    @checkCurrentGui
    def viewerControlWidget(self):
        return self.currentGui().viewerControlWidget()
    
    def setImageIndex(self, imageIndex):
        self._imageIndex = imageIndex

    def reset(self):
        for gui in self._guis.values():
            gui.reset()


