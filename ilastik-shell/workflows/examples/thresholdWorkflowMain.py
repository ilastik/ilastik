from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap

import lazyflow
from ilastikshell import IlastikShell, SideSplitterSizePolicy
from applets.dataSelection import DataSelectionApplet
from applets.thresholdMasking import ThresholdMaskingApplet

def createShell():
    # This Graph is shared by all applets and operators
    graph = lazyflow.graph.Graph()
    
    # Create applets 
    dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
    thresholdMaskingApplet = ThresholdMaskingApplet(graph, "Thresholding", "Thresholding Stage 1")
    
    # Connect top-level operators
    thresholdMaskingApplet.topLevelOperator.InputImage.connect( dataSelectionApplet.topLevelOperator.Image )
    
    # Create the shell and add the applets
    shell = IlastikShell(sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)    
    shell.addApplet(dataSelectionApplet)
    shell.addApplet( thresholdMaskingApplet )

    # The shell populates his "current view" image list combo using a slot of image names from the data selection applet.    
    shell.setImageNameListSlot( dataSelectionApplet.topLevelOperator.ImageName )

    return shell    

if __name__ == "__main__":
    app = QApplication([])
    
    # Splash Screen
    splashImage = QPixmap("../ilastik-splash.png")
    splashScreen = QSplashScreen(splashImage)
    splashScreen.show()

    # Create workflow and add it to the shell    
    shell = createShell()
    
    # Start the shell GUI.
    shell.show()

    # Hide the splash screen
    splashScreen.finish(shell)
    
    app.exec_()
    
