from ilastik.utility.simpleSignal import SimpleSignal
from abc import ABCMeta, abstractproperty, abstractmethod
import weakref
import gc

class Applet( object ):
    """
    Base class for all applets.
    """
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties

    _base_initialized = False
    
    def __init__( self, name ):
        """
        Constructor.  Subclasses must call this base implementation in their own __init__ methods.  If they fail to do so, the shell raises an exception.
            
            :param name: The applet's name, which will appear as the applet drawer title. 
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

    @abstractmethod
    def getMultiLaneGui(self):
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


from ilastik.applets.base.multiLaneOperator import MultiLaneOperatorABC, OpAutoMultiLane
class StandardApplet( Applet ):

    def __init__(self, name, workflow=None):
        super(StandardApplet, self).__init__(name)
        self._gui = None
        self.__topLevelOperator = None
        self.__workflow = workflow

    #
    # Top-Level Operator
    #
    # Subclasses have 2 Choices:
    #   - Override topLevelOperator (advanced)
    #   - Override singleLaneOpeartorClass AND broadcastingSlots (easier; uses default topLevelOperator implementation)
    
    @property
    def singleLaneOperatorClass(self):
        """
        Return the operator class which handles a single image.
        Single-lane applets should override this property.
        Multi-lane applets must override topLevelOperator directly.
        """
        return NotImplemented

    @property
    def broadcastingSlots(self):
        """
        Slots that should be connected to all image lanes are referred to as "broadcasting" slots.
        Single-lane applets should override this property to return a list of the broadcasting slots' names.
        Multi-lane applets must override topLevelOperator directly.
        """
        return NotImplemented

    @property
    def topLevelOperator(self):
        """
        Get the top-level (multi-image-lane) operator for the applet.
        Applets that must be multi-image-lane aware must override this property.
        """
        if self.__topLevelOperator is None:
            self.__createTopLevelOperator()
        return self.__topLevelOperator

    #
    # GUI
    #
    # Subclasses have 3 choices:
    # - Override getMultiLaneGui (advanced)
    # - Override createSingleLaneGui (easier: uses default getMultiLaneGui implementation)
    # - Override singleLaneGuiClass (easiest: uses default createSingleLaneGui and getMultiLaneGui implementations)

    @property
    def singleLaneGuiClass(self):
        """
        Return the class that will be instantiated for each image lane the applet needs.
        """
        return NotImplemented

    def createSingleLaneGui(self, imageLaneIndex):
        if self.singleLaneGuiClass is NotImplemented:
            message  = "Cannot create GUI.\n"
            message += "StandardApplet subclasses must implement ONE of the following:\n" 
            message += "singleLaneGuiClass, createSingleLaneGui, or getMultiLaneGui"
            raise NotImplementedError(message)
        singleLaneOperator = self.topLevelOperator.getLane( imageLaneIndex )
        return self.singleLaneGuiClass( singleLaneOperator )

    def getMultiLaneGui(self):
        if self._gui is None:
            assert isinstance(self.topLevelOperator, MultiLaneOperatorABC), "All applet top-level operators must satisfy the Multi-lane interface."
            self._gui = SingleToMultiGuiAdapter( self.createSingleLaneGui, self.topLevelOperator )
        return self._gui

    def __createTopLevelOperator(self):
        assert self.__topLevelOperator is None
        operatorClass = self.singleLaneOperatorClass
        broadcastingSlots = self.broadcastingSlots
        if operatorClass is NotImplemented or broadcastingSlots is NotImplemented:
            message = "Could not create top-level operator for {}\n".format( self.__class__ )
            message += "StandardApplet subclasses must implement the singleLaneOperatorClass and broadcastingSlots"
            message += " members OR override topLevelOperator themselves."
            raise NotImplementedError(message)

        if self.__workflow is None:
            message = "Could not create top-level operator for {}\n".format( self.__class__ )
            message += "Please initialize StandardApplet base class with a workflow object."
            raise NotImplementedError(message)
        
        self.__topLevelOperator = OpAutoMultiLane(self.singleLaneOperatorClass,
                                                  parent=self.__workflow,
                                                  broadcastingSlotNames=self.broadcastingSlots)

def checkCurrentGui(f):
    def _wrapper(self, *args, **kwargs):
        if self.currentGui() is None:
            return None
        else:
            return f(self, *args, **kwargs)
    return _wrapper
    
class SingleToMultiGuiAdapter( object ):
    def __init__(self, singleImageGuiFactory, topLevelOperator):
        self.singleImageGuiFactory = singleImageGuiFactory
        self._imageIndex = None
        self._guis = {}
        self.topLevelOperator = topLevelOperator

    def currentGui(self):
        if self._imageIndex is None:
            return None
        # Create first if necessary
        if self._imageIndex not in self._guis:
            self._guis[self._imageIndex] = self.singleImageGuiFactory( self._imageIndex )
        return self._guis[self._imageIndex]

    def appletDrawer(self):
        if self.currentGui() is not None:
            return self.currentGui().appletDrawer()
        else:
            from PyQt4.QtGui import QWidget
            return QWidget()

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

    def stopAndCleanUp(self):
        for gui in self._guis.values():
            gui.stopAndCleanUp()




















