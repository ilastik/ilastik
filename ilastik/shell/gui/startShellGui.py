#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from ilastik.shell.gui.ilastikShell import IlastikShell, SideSplitterSizePolicy

# Logging configuration
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

def startShellGui(workflowClass):
    """
    Start the ilastik shell GUI with the given workflow type.
    
    workflowClass - the type of workflow to instantiate for the shell.    
    """
    application = QApplication([])
    
    # Splash Screen
    splashImage = QPixmap("../ilastik-splash.png")
    splashScreen = QSplashScreen(splashImage)
    splashScreen.show()
    
    # Create workflow
    workflow = workflowClass()
    
    # Create the shell and populate it
    shell = IlastikShell(sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)
    for app in workflow.applets:
        shell.addApplet(app)
    shell.setImageNameListSlot( workflow.imageNameListSlot )
    
    # Start the shell GUI.
    shell.show()
    
    # Hide the splash screen
    splashScreen.finish(shell)

    application.exec_()
