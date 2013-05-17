import os
import platform

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap 
from PyQt4.QtCore import Qt, QTimer, QEvent

# Logging configuration
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

import ilastik.config

import functools

shell = None

def startShellGui(workflow_cmdline_args, *testFuncs):
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
    _applyStyleSheet(app)

    showSplashScreen()
    app.processEvents()
    QTimer.singleShot( 0, functools.partial(launchShell, workflow_cmdline_args, *testFuncs ) )
    QTimer.singleShot( 0, hideSplashScreen)

    return app.exec_()

def _applyStyleSheet(app):
    """
    Apply application-wide style-sheet rules.
    """
    styleSheetPath = os.path.join( os.path.split(__file__)[0], 'ilastik-style.qss' )
    with file( styleSheetPath, 'r' ) as f:
        styleSheetText = f.read()
        app.setStyleSheet(styleSheetText)

splashScreen = None
def showSplashScreen():
    splash_path = os.path.join(os.path.split(ilastik.__file__)[0], 'ilastik-splash.png')
    splashImage = QPixmap(splash_path)
    global splashScreen
    splashScreen = QSplashScreen(splashImage)
    splashScreen.show()

def hideSplashScreen():
    global splashScreen
    global shell
    splashScreen.finish(shell)

def launchShell(workflow_cmdline_args, *testFuncs):
    """
    Start the ilastik shell GUI with the given workflow type.
    Note: A QApplication must already exist, and you must call this function from its event loop.
    """
    # This will import a lot of stuff (essentially the entire program).
    # We use a late import here so the splash screen is shown while this lengthy import happens.
    from ilastik.shell.gui.ilastikShell import IlastikShell
    
    # Create the shell and populate it
    global shell
    shell = IlastikShell(None, workflow_cmdline_args)

    assert QApplication.instance().thread() == shell.thread()

    # Start the shell GUI.
    shell.show()
    if not ilastik.config.cfg.getboolean("ilastik", "debug"):
        shell.showMaximized()
    
    # Run a test (if given)
    for testFunc in testFuncs:
        QTimer.singleShot(0, functools.partial(testFunc, shell) )

    # On Mac, the main window needs to be explicitly raised
    shell.raise_()
    QApplication.instance().processEvents()
    
    return shell