#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4.QtCore import QTimer

from ilastikshell.ilastikShell import IlastikShell

from applets.pixelClassification import PixelClassificationApplet
from applets.projectMetadata import ProjectMetadataApplet
from applets.dataSelection import DataSelectionApplet
from applets.featureSelection import FeatureSelectionApplet
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
featureSelectionApplet = FeatureSelectionApplet(graph)
pcApplet = PixelClassificationApplet(graph)

# Get handles to each of the applet top-level operators
opData = dataSelectionApplet.topLevelOperator
opFeatures = featureSelectionApplet.topLevelOperator
opClassify = pcApplet.topLevelOperator

# Connect the operators together
opFeatures.InputImages.connect( opData.ProcessedImages )
opClassify.InputImages.connect( opData.ProcessedImages )
opClassify.FeatureImages.connect( opFeatures.OutputImages )
opClassify.CachedFeatureImages.connect( opFeatures.CachedOutputImages )

# Create the shell
shell = IlastikShell()

# Add each applet to the shell
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)
shell.addApplet(featureSelectionApplet)
shell.addApplet(pcApplet)

# Tell the shell where to get the image names
shell.setImageNameListSlot( opData.ImageNames )

# Start the shell GUI.
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

def test():
    from functools import partial
    
    # Open a test project
    shell.openProjectFile('/home/bergs/test_project.ilp')
    
    # Select the labeling drawer
    shell.setSelectedAppletDrawer( 3 )
    
    # Enable interactive mode
    QTimer.singleShot( 1000, partial(pcApplet.centralWidget._labelControlUi.checkInteractive.setChecked, True) )


QTimer.singleShot(1, test )

app.exec_()

