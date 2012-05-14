from PyQt4.QtGui import QWidget, QApplication

from utility.simpleSignal import SimpleSignal

class Applet( object ):
    def __init__( self, name ):
        self.name = name

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
    def viewerControlWidget( self ):
        """
        Return the applet's viewer control widget (if any).
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
    
    def setImageIndex(self, imageIndex):
        """
        Change the currently displayed image to the one specified by the given index.
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
