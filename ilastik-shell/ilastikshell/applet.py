from PyQt4.QtGui import QLabel, QApplication

class Applet( object ):
    def __init__( self ):
        self.name = None

        # Status signal.
        # Shell uses it for the status bar.
        self.statusSignal = SimpleSignal() # Signature: emit(statusText)
        
        # Progress signal.
        # When the applet is doing something time-consuming, this signal tells the shell.
        self.progressSignal = SimpleSignal() # Signature: emit(percentComplete, canceled=false)

    ###
    ### Outputs provided by the Applet to the Shell or Workflow Manager
    ###

    @property
    def topLevelOperator(self):
        """
        Return the applet's Top Level Operator, which is a single operator for all computation performed by the applet.
        Each applet has exactly one top-level operator for performing computations.
        Workflow managers can connect the top-level operator of one applet to others.
        """
        return None

    @property
    def centralWidget( self ):
        """
        Return the applet's central widget to be displayed on the right side of the window (if any).
        """
        return None

    @property
    def appletDrawers(self):
        """
        Return a list of the control widgets to be displayed in the left-hand side bar for this applet.
        Only one will be open at any particular time.
        """
        return []
    
    @property
    def menuWidget( self ):
        return None

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

    ###
    ### Inputs provided to the Applet from the shell or workflow manager
    ###

    def setShellActions(self, shellActions):
        """
        Accept the given shell actions object and connect callbacks to it as needed.
        
        The shell provides a few actions that applets may choose to react to (load, save, etc.).
        This function is called when the applet is added to the shell.
        Applets can retain access to the shell actions if they need to trigger or respond to them.
        """
        pass
          
    def setVolumeEditor(self, editor):
        """
        Accept the provided volume editor object for display within the applet's central widget (if any).
        Applets may share volume editors.
        The volume editor is instantiated externally by the workflow manager, and passed to the applet via this function.
        Applets may add and remove layers to the editor via the editor's layerstack member.
        """
        pass

def run_applet( applet_type, *args, **kwargs):
    '''Run applet standalone.'''
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    qapp = QApplication([])
    applet = applet_type(*args, **kwargs)
    applet.centralWidget.show()
    applet.controlWidget.show()
    qapp.exec_()

if __name__ == '__main__':
    run_applet(Applet)
