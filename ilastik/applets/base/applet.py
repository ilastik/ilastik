from ilastik.utility.simpleSignal import SimpleSignal

from abc import ABCMeta, abstractproperty

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







