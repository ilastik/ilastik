from ilastik.utility.simpleSignal import SimpleSignal

from abc import ABCMeta, abstractproperty

class ControlCommand(object):
    # An enum of commands that applets can use to request that other applet GUIs become disabled
    Pop = 0                 # Undo the most recent command that the issuing applet sent
    DisableAll = 1          # Disable all applets in the workflow
    DisableUpstream = 2     # Disable applets that come before the applet that is issuing the command
    DisableDownstream = 3   # Disable applets that come after the applet that is issuing the command
    DisableSelf = 4         # Disable the applet that is issuing the command

class ShellRequest(object):
    # These are the things an applet can ask the shell to do via the shellRequestSignal
    RequestSave = 0

class Applet( object ):
    
    __metaclass__ = ABCMeta # Force subclasses to override abstract methods and properties

    _base_initialized = False
    
    def __init__( self, name ):
        self.name = name

        # Status signal.
        # Shell uses it for the status bar.
        self.statusSignal = SimpleSignal() # Signature: emit(statusText)
        
        # Progress signal.
        # When the applet is doing something time-consuming, this signal tells the shell.
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete, canceled=false)
        
        # GUI control signal
        # When an applet wants other applets in the shell to be disabled, he fires this signal.
        # The applet must fire it again with ControlState.EnableAll as the parameter to re-enable the other applets. 
        self.guiControlSignal = SimpleSignal() # Signature: emit(controlState=ControlState.DisableAll)

        # Shell request signal is used to trigger certain shell requests.
        self.shellRequestSignal = SimpleSignal() # Signature:emit(request)

        self._base_initialized = True

    @abstractproperty
    def topLevelOperator(self):
        """
        Return the applet's Top Level Operator, which is a single operator for all computation performed by the applet.
        Each applet has exactly one top-level operator for performing computations.
        Workflow managers can connect the top-level operator of one applet to others.
        """
        return None

    @abstractproperty
    def gui(self):
        raise NotImplementedError

    @property
    def dataSerializers(self):
        """
        Return a list of dataSerializer objects for loading/saving any project data the applet is responsible for.
        """ 
        return []
    
    @property
    def appletPreferencesManager(self):
        """
        Return the applet's preferences manager (if any).
        
        Applets with preferences or "last state" items that are independent 
        of project saved data may save/load that information via a preferences manager.
        """
        return None

    @property
    def base_initialized(self):
        """
        Do not override this property.
        Used by the shell to ensure that Applet.__init__ was called by your subclass.
        """
        return self._base_initialized








