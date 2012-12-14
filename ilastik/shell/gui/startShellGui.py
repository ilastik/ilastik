import os

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4.QtCore import QTimer
from ilastik.shell.gui.ilastikShell import IlastikShell, SideSplitterSizePolicy

# Logging configuration
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

import functools

def startShellGui(workflowClass, testFunc = None):
    """
    Create an application and launch the shell in it.
    """
    app = QApplication([])
    QTimer.singleShot( 0, functools.partial(launchShell, workflowClass, testFunc ) )
    
    _applyStyleSheet(app)

    app.exec_()

def _applyStyleSheet(app):
    """
    Apply application-wide style-sheet rules.
    """
    styleSheetPath = os.path.join( os.path.split(ilastik.shell.gui.ilastikShell.__file__)[0], 'ilastik-style.qss' )
    with file( styleSheetPath, 'r' ) as f:
        styleSheetText = f.read()
        app.setStyleSheet(styleSheetText)

def launchShell(workflowClass, testFunc = None):
    """
    Start the ilastik shell GUI with the given workflow type.
    Note: A QApplication must already exist, and you must call this function from its event loop.
    
    workflowClass - the type of workflow to instantiate for the shell.    
    """
    # Splash Screen
    splashImage = QPixmap("../ilastik-splash.png")
    splashScreen = QSplashScreen(splashImage)
    splashScreen.show()
    
    # Create the shell and populate it
    shell = IlastikShell(workflowClass=workflowClass, sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)
    
    # Start the shell GUI.
    shell.show()

    # Hide the splash screen
    splashScreen.finish(shell)

    # Run a test (if given)
    if testFunc:
        QTimer.singleShot(0, functools.partial(testFunc, shell) )
