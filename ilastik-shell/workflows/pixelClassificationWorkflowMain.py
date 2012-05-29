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
from applets.batchIo import BatchIoApplet

from applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

app = QApplication([])

# Splash Screen
splashImage = QPixmap("../ilastik-splash.png")
splashScreen = QSplashScreen(splashImage)
splashScreen.show()

# Create a graph to be shared among all the applets
graph = Graph()

# Create the applets for our workflow
projectMetadataApplet = ProjectMetadataApplet()
dataSelectionApplet = DataSelectionApplet(graph, "Input Data", supportIlastik05Import=True, batchDataGui=False)
featureSelectionApplet = FeatureSelectionApplet(graph)
pcApplet = PixelClassificationApplet(graph)

# Get handles to each of the applet top-level operators
opData = dataSelectionApplet.topLevelOperator
opTrainingFeatures = featureSelectionApplet.topLevelOperator
opClassify = pcApplet.topLevelOperator

# Connect the operators together
opTrainingFeatures.InputImage.connect( opData.Image )
opClassify.InputImages.connect( opData.Image )
opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )
opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )

# Batch prediction has it's own workflow (but no training)
batchInputApplet = DataSelectionApplet(graph, "Batch Inputs", supportIlastik05Import=False, batchDataGui=True)
batchResultsApplet = BatchIoApplet(graph, "Batch Results")

opBatchInputs = batchInputApplet.topLevelOperator
opBatchResults = batchResultsApplet.topLevelOperator
opBatchFeatures = OpFeatureSelection(graph=graph)
opBatchPredictor = OpPredictRandomForest(graph=graph)

# Simply obtain feature settings (scales, matrix, etc.) from the training features operator
opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )

# Batch feature inputs are the batch input data
opBatchFeatures.InputImage.connect( opBatchInputs.Image )

# Obtain the classifier and max label value from the classification applet top-level operator
opBatchPredictor.Classifier.connect( opClassify.Classifier )
opBatchPredictor.LabelsCount.connect( opClassify.MaxLabelValue )

# Input to the predictor are batch input features
opBatchPredictor.Image.connect( opBatchFeatures.OutputImage )

# The results we want to export are the probability maps
opSelectBatchDatasetPath = OperatorWrapper( OpAttributeSelector(graph=graph) )
opSelectBatchDatasetPath.InputObject.connect( opBatchInputs.Dataset )
opSelectBatchDatasetPath.AttributeName.setValue( 'filePath' )
opBatchResults.DatasetPath.connect( opSelectBatchDatasetPath.Result )
opBatchResults.ImageToExport.connect( opBatchPredictor.PMaps )

# Create the shell
shell = IlastikShell()

# Add each applet to the shell
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)
shell.addApplet(featureSelectionApplet)
shell.addApplet(pcApplet)
shell.addApplet(batchInputApplet)
shell.addApplet(batchResultsApplet)

# The shell needs a slot to read the image names from.
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
    shell.openProjectFile('/home/bergs/test_project.ilp')
    
    # Select the labeling drawer
    shell.setSelectedAppletDrawer( 3 )
    
    # Check the 'interactive mode' checkbox.
    QTimer.singleShot( 2000, partial(pcApplet.centralWidget._labelControlUi.checkInteractive.setChecked, True) )


# Run a test
#QTimer.singleShot(1, test )

app.exec_()

