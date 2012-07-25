#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4.QtCore import QTimer

from ilastikshell.ilastikShell import IlastikShell, SideSplitterSizePolicy

from applets.pixelClassification import PixelClassificationApplet
from applets.projectMetadata import ProjectMetadataApplet
from applets.dataSelection import DataSelectionApplet
from applets.featureSelection import FeatureSelectionApplet
from applets.batchIo import BatchIoApplet
from applets.vigraWatershedViewer import VigraWatershedViewerApplet

from applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector, OpMetadataInjector

import ilastik_logging
ilastik_logging.startUpdateInterval(10)

def main():
    app = QApplication([])
    
    # Splash Screen
    splashImage = QPixmap("../ilastik-splash.png")
    splashScreen = QSplashScreen(splashImage)
    splashScreen.show()
    
    # Create a graph to be shared by all operators
    graph = Graph()
    
    ######################
    # Interactive workflow
    ######################
    
    ## Create applets 
    projectMetadataApplet = ProjectMetadataApplet()
    dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
    featureSelectionApplet = FeatureSelectionApplet(graph, "Feature Selection", "FeatureSelections")
    pcApplet = PixelClassificationApplet(graph, "PixelClassification")
    watershedApplet = VigraWatershedViewerApplet(graph, "Watershed", "Watershed")
    
    ## Access applet operators
    opData = dataSelectionApplet.topLevelOperator
    opTrainingFeatures = featureSelectionApplet.topLevelOperator
    opClassify = pcApplet.topLevelOperator
    
    ## Connect operators ##
    
    # Input Image -> Feature Op
    #         and -> Classification Op (for display)
    opTrainingFeatures.InputImage.connect( opData.Image )
    opClassify.InputImages.connect( opData.Image )
    
    # Feature Images -> Classification Op (for training, prediction)
    opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
    opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )
    
    # Training flags -> Classification Op (for GUI restrictions)
    opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )
    
    # Classification predictions -> Watershed input
    watershedApplet.topLevelOperator.InputImage.connect( opClassify.CachedPredictionProbabilities )
    
    ######################
    # Shell
    ######################
    
    # Create the shell
    shell = IlastikShell(sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)
    
    # Add interactive workflow applets
    shell.addApplet(projectMetadataApplet)
    shell.addApplet(dataSelectionApplet)
    shell.addApplet(featureSelectionApplet)
    shell.addApplet(pcApplet)
    shell.addApplet(watershedApplet)
    
    # The shell needs a slot from which he can read the list of image names to switch between.
    # Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
    opSelectFilename = OperatorWrapper( OpAttributeSelector(graph=graph) )
    opSelectFilename.InputObject.connect( opData.Dataset )
    opSelectFilename.AttributeName.setValue( 'filePath' )
    shell.setImageNameListSlot( opSelectFilename.Result )
    
    # Start the shell GUI.
    shell.show()
    
    # Hide the splash screen
    splashScreen.finish(shell)
    
    def test():
        from functools import partial
        
        # Open a test project
        shell.openProjectFile('/tmp/synapse_small.ilp')
        #shell.openProjectFile('/home/bergs/dummy.ilp')
        #shell.openProjectFile('/home/bergs/flyem.ilp')
        
        
        # Select a drawer
        #shell.setSelectedAppletDrawer( 7 )
        
        # Check the 'interactive mode' checkbox.
        #QTimer.singleShot( 2000, partial(pcApplet.centralWidget._labelControlUi.checkInteractive.setChecked, True) )
    
    #timer = QTimer()
    #timer.setInterval(4000)
    #timer.timeout.connect( shell.scrollToTop )
    #timer.start()

    def quit_test():
        shell.onQuitActionTriggered(True)

    # Run a test
    QTimer.singleShot(1, test )

#    QTimer.singleShot(20, quit_test )
    
    app.exec_()
    
if __name__ == '__main__':
    #main()
    import cProfile
    cProfile.run('main()', 'main.profile')

    print "FINISHED"










