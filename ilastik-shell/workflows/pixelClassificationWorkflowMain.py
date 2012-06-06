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
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector, OpMetadataInjector

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
dataSelectionApplet = DataSelectionApplet(graph, "Input Data", supportIlastik05Import=True, batchDataGui=False)
featureSelectionApplet = FeatureSelectionApplet(graph)
pcApplet = PixelClassificationApplet(graph)

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

###
#  Test Test Test
###
#from applets.genericViewer import GenericViewerApplet
#from applets.genericViewer.genericViewerGui import LayerType
#genericViewerApplet = GenericViewerApplet(graph)
#opGenericViewer = genericViewerApplet.topLevelOperator
#
## Inject metadata to specify the base data layer name
#opBaseNameInjector = OpMetadataInjector(graph=graph)
#opBaseNameInjector.Metadata.setValue( { 'name' : 'Input Data',
#                                        'layertype' : LayerType.AlphaModulated } )
#opBaseNameInjector.Input.connect( opData.Image )
#opGenericViewer.BaseLayer.connect( opBaseNameInjector.Output )
#
## Inject metadata to specify the feature layer display type
#opFeatureDisplayInjector = OpMetadataInjector(graph=graph)
#opFeatureDisplayInjector.Metadata.setValue( {'layertype' : LayerType.AlphaModulated} )
#opFeatureDisplayInjector.Input.connect( opTrainingFeatures.OutputImage )
#opGenericViewer.ChannelwiseLayers.connect( opFeatureDisplayInjector.Output )

###############
# Threshold test
###############
from applets.threshold import ThresholdApplet
thresholdApplet = ThresholdApplet(graph)
opThresholdViewer = thresholdApplet.topLevelOperator
opThresholdViewer.InputImage.connect( opData.Image )

######################
# Batch workflow
######################

## Create applets
batchInputApplet = DataSelectionApplet(graph, "Batch Inputs", supportIlastik05Import=False, batchDataGui=True)
batchResultsApplet = BatchIoApplet(graph, "Batch Results")

## Access applet operators
opBatchInputs = batchInputApplet.topLevelOperator
opBatchResults = batchResultsApplet.topLevelOperator

## Create additional batch workflow operators
opBatchFeatures = OpFeatureSelection(graph=graph)
opBatchPredictor = OpPredictRandomForest(graph=graph)
opSelectBatchDatasetPath = OperatorWrapper( OpAttributeSelector(graph=graph) )

## Connect Operators ## 

# Provide dataset paths from data selection applet to the batch export applet via an attribute selector
opSelectBatchDatasetPath.InputObject.connect( opBatchInputs.Dataset )
opSelectBatchDatasetPath.AttributeName.setValue( 'filePath' )
opBatchResults.DatasetPath.connect( opSelectBatchDatasetPath.Result )

# Connect (clone) the feature operator inputs from 
#  the interactive workflow's features operator (which gets them from the GUI)
opBatchFeatures.Scales.connect( opTrainingFeatures.Scales )
opBatchFeatures.FeatureIds.connect( opTrainingFeatures.FeatureIds )
opBatchFeatures.SelectionMatrix.connect( opTrainingFeatures.SelectionMatrix )

# Classifier and LabelsCount are provided by the interactive workflow
opBatchPredictor.Classifier.connect( opClassify.Classifier )
opBatchPredictor.LabelsCount.connect( opClassify.MaxLabelValue )

# Connect Image pathway:
# Input Image -> Features Op -> Prediction Op -> Export
opBatchFeatures.InputImage.connect( opBatchInputs.Image )
opBatchPredictor.Image.connect( opBatchFeatures.OutputImage )
opBatchResults.ImageToExport.connect( opBatchPredictor.PMaps )

######################
# Shell
######################

# Create the shell
shell = IlastikShell()

# Add interactive workflow applets
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)
shell.addApplet(featureSelectionApplet)
shell.addApplet(pcApplet)

# Add batch workflow applets
shell.addApplet(batchInputApplet)
shell.addApplet(batchResultsApplet)

# TEST TEST TEST TEST
#shell.addApplet( genericViewerApplet )
shell.addApplet( thresholdApplet )

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
    shell.openProjectFile('/home/bergs/synapse_small.ilp')
    
    # Select a drawer
    #shell.setSelectedAppletDrawer( 7 )
    
    # Check the 'interactive mode' checkbox.
    #QTimer.singleShot( 2000, partial(pcApplet.centralWidget._labelControlUi.checkInteractive.setChecked, True) )


# Run a test
#QTimer.singleShot(1, test )

app.exec_()

