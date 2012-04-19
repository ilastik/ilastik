#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap

from ilastikshell.ilastikShell import IlastikShell

from applets.pixelClassification import PixelClassificationApplet
from applets.dataImport import InputDataSelectionApplet

from lazyflow.graph import Graph

app = QApplication([])

# Splash Screen
splashImage = QPixmap("ilastik-splash.png")
splashScreen = QSplashScreen(splashImage)
splashScreen.show()

inputDataSelectionApplet = InputDataSelectionApplet()

# Create a graph to be shared among all the applets
graph = Graph()
pcApplet = PixelClassificationApplet(graph)

shell = IlastikShell()
shell.addApplet(inputDataSelectionApplet)
shell.addApplet(pcApplet)
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

app.exec_()
