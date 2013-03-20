from ilastik.utility.simpleSignal import SimpleSignal
from abc import ABCMeta, abstractproperty, abstractmethod

class Applet( object ):
    """
    Base class for all applets.  The shell and workflow depend on this interface only.
    Applets can subclass from this class directly, but in most cases it is easier to 
    subclass :py:class:`StandardApplet<ilastik.applets.base.standardApplet.StandardApplet>`.
    """
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties

    _base_initialized = False
    
    def __init__( self, name, syncWithImageIndex=True ):
        """
        Constructor.
        Subclasses must call this base implementation in their own ``__init__`` methods.
        If they fail to do so, the shell raises an exception.
            
        :param name: The applet's name, which will appear as the applet drawer title.
        :param syncWithImageIndex: If True, the shell/workflow will add an image lane to this applet for each image in the interactive workflow. 
        """
        self.name = name
        self.syncWithImageIndex = syncWithImageIndex

        #: Progress signal.
        #: When the applet is doing something time-consuming, this signal tells the shell to show a progress bar.
        #: Signature: ``emit(percentComplete, canceled=false)``
        #: 
        #: .. note:: To update the progress bar correctly, the shell expects that progress updates always 
        #:           begin with at least one zero update and end with at least one 100 update.
        #:           That is: 
        #:           ``self.progressSignal.emit(0)`` ... more updates ... ``self.progressSignal.emit(100)``
        self.progressSignal = SimpleSignal()
        
        #: GUI control signal
        #: See the ControlCommand class (below) for an enumerated list of the commands supported by this signal)
        #: Signature: ``emit(command=ControlCommand.DisableAll)`` 
        self.guiControlSignal = SimpleSignal()

        #: Shell request signal is used to trigger certain shell actions.
        #: Signature: ``emit(request)``
        #: where ``request`` is an integer corresponding to the action the shell should take.  The allowable actions are enumerated in the :py:class:`ShellRequest` class.
        #: Example invocation: ``self.shellRequest.emit(ShellRequest.RequestSave)``
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
        Abstract method.
        Provides the applet's GUI, which must be an instance of :py:class:`AppletGuiInterface<ilastik.applets.base.appletGuiInterface.AppletGuiInterface>`.
        """
        raise NotImplementedError

    @property
    def dataSerializers(self):
        """
        A list of dataSerializer objects for loading/saving any project data the applet is responsible for.
        Each serializer must be an instance of :py:class:`AppletSerializer<ilastik.applets.base.appletSerializer.AppletSerializer>`
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
    This class enumerates the GUI control commands that applets can ask the shell to perform via :py:attr:`Applet.guiControlSignal`.
    Gui control commands are used to prevent the user from altering upstream or downstream applet settings while an applet is performing some long-running task.
    """
    #: Undo the most recent command that the issuing applet sent
    Pop = 0

    #: Disable all applets in the workflow
    DisableAll = 1
    
    #: Disable applets that come before the applet that is issuing the command
    DisableUpstream = 2
    
    #: Disable applets that come after the applet that is issuing the command
    DisableDownstream = 3
    
    #: Disable the applet that is issuing the command
    DisableSelf = 4

class ShellRequest(object):
    """
    This class enumerates the actions that applets can ask the shell to perform via :py:attr:`Applet.shellRequestSignal`.
    At the moment, there is only one supported action.
    """
    #: Request that the shell perform a "save project" action.
    RequestSave = 0






















