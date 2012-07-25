#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap

from ilastik.ilastikshell.ilastikShell import IlastikShell

from ilastik.applets.seededWatershed import SeededWatershedApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
#from ilastik.applets.featureSelection import FeatureSelectionApplet
from lazyflow.graph import Graph

app = QApplication([])

# Splash Screen
splashImage = QPixmap("../ilastik-splash.png")
splashScreen = QSplashScreen(splashImage)
splashScreen.show()


# Create a graph to be shared among all the applets
graph = Graph()

# Create the applets for our workflow
projectMetadataApplet = ProjectMetadataApplet()
dataSelectionApplet = DataSelectionApplet(graph)
#featureSelectionApplet = FeatureSelectionApplet(graph)
segApplet = SeededWatershedApplet(graph)

# Get handles to each of the applet top-level operators
opData = dataSelectionApplet.topLevelOperator
opSegmentor = segApplet.topLevelOperator

# Connect the operators together
# opFeatures.InputImages.connect( opData.ProcessedImages )
opSegmentor.image.connect( opData.ProcessedImage )

shell = IlastikShell()
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)

shell.addApplet(segApplet)
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

app.exec_()
