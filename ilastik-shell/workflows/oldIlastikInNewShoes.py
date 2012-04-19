#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap

from ilastikshell.ilastikShell import IlastikShell

from applets.pixelClassification import PixelClassificationApplet
from applets.dataImport import InputDataSelectionApplet

app = QApplication([])

# Splash Screen
splashImage = QPixmap("ilastik-splash.png")
splashScreen = QSplashScreen(splashImage)
splashScreen.show()
splashScreen = QSplashScreen(splashImage)
splashScreen.show()
inputDataSelectionApplet = InputDataSelectionApplet()
pc = PixelClassificationApplet()

shell = IlastikShell()
shell.addApplet(inputDataSelectionApplet)
shell.addApplet(pc)
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

app.exec_()
