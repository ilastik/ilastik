#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap

from ilastikshell.ilastikShell import IlastikShell
from applets.pixelClassification import PixelClassificationApplet

app = QApplication([])

# Splash Screen
splashImage = QPixmap("ilastik-splash.png")
#painter = QtGui.QPainter()
#painter.begin(splashImage)
#painter.drawText(QtCore.QPointF(270,110), ilastik.core.readInBuildInfo())
#painter.end()

splashScreen = QSplashScreen(splashImage)
splashScreen.show()


#g = Graph()
#pipeline = PixelClassificationPipeline( g )
#pig = PixelClassificationGui( pipeline, graph = g)
#pig.show()

pc = PixelClassificationApplet()

from ilastikshell.applet import Applet
from PyQt4.QtGui import QMenuBar, QMenu
defaultApplet = Applet()

# Normally applets would provide their own menu items,
# but for this test we'll add them here (i.e. from the outside).
defaultApplet._menuWidget = QMenuBar()
defaultApplet._menuWidget.setNativeMenuBar( False ) # Native menus are broken on Ubuntu at the moment
defaultMenu = QMenu("Default Applet", defaultApplet._menuWidget)
defaultMenu.addAction("Default Action 1")
defaultMenu.addAction("Default Action 2")
defaultApplet._menuWidget.addMenu(defaultMenu)
defaultApplet._serializableItems = []

shell = IlastikShell()
shell.addApplet(pc)
shell.addApplet(defaultApplet)
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

app.exec_()
