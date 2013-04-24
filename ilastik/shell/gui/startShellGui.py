import os
import platform 

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4.QtCore import Qt, QTimer
from ilastik.shell.gui.ilastikShell import IlastikShell, SideSplitterSizePolicy

# Logging configuration
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

import ilastik.config

import functools

shell = None

def startShellGui(workflowClass=None,*testFuncs):
    """
    Create an application and launch the shell in it.
    """

    """
    The next two lines fix the following xcb error on Ubuntu by calling X11InitThreads before loading the QApplication:
       [xcb] Unknown request in queue while dequeuing 
       [xcb] Most likely this is a multi-threaded client and XInitThreads has not been called 
       [xcb] Aborting, sorry about that.
       python: ../../src/xcb_io.c:178: dequeue_pending_request: Assertion !xcb_xlib_unknown_req_in_deq failed.
    """
    platform_str = platform.platform().lower() 
    if 'ubuntu' in platform_str or 'fedora' in platform_str:
        QApplication.setAttribute(Qt.AA_X11InitThreads, True)

    if ilastik.config.cfg.getboolean("ilastik", "debug"):
        QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, True)
    
    app = QApplication([])

    QTimer.singleShot( 0, functools.partial(launchShell, workflowClass, *testFuncs ) )
        
    _applyStyleSheet(app)

    return app.exec_()

def _applyStyleSheet(app):
    """
    Apply application-wide style-sheet rules.
    """
    styleSheetPath = os.path.join( os.path.split(ilastik.shell.gui.ilastikShell.__file__)[0], 'ilastik-style.qss' )
    with file( styleSheetPath, 'r' ) as f:
        styleSheetText = f.read()
        app.setStyleSheet(styleSheetText)

def launchShell(workflowClass=None, *testFuncs):
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
    global shell
    shell = IlastikShell(workflowClass=workflowClass, sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)

    assert QApplication.instance().thread() == shell.thread()
    
    # Start the shell GUI.
    shell.show()

    # Hide the splash screen
    splashScreen.finish(shell)

    # Run a test (if given)
    for testFunc in testFuncs:
        QTimer.singleShot(0, functools.partial(testFunc, shell) )
