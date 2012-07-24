import h5py
# Before doing anything else, monkey-patch ndarray to always init with nans.
# (Hopefully this will help us track down a bug...)
import numpy
from abc import ABCMeta
original_ndarray = numpy.ndarray
class nan_ndarray(numpy.ndarray):
    __metaclass__ = ABCMeta
    
    def __init__(self, *args, **kwargs):
        super(nan_ndarray, self).__init__(*args, **kwargs)
        self[...] = numpy.nan
        self.monkeypatched = True

    @classmethod
    def __subclasshook__(cls, C):
        return C is nan_ndarray or C is original_ndarray

numpy.ndarray = nan_ndarray
assert isinstance(numpy.zeros((1,)), numpy.ndarray)

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

from applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

import ilastik_logging
ilastik_logging.startUpdateInterval(10)


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

######################
# Batch workflow
######################

## Create applets
batchInputApplet = DataSelectionApplet(graph, "Batch Inputs", "BatchDataSelection", supportIlastik05Import=False, batchDataGui=True)
batchResultsApplet = BatchIoApplet(graph, "Batch Results")

## Access applet operators
opBatchInputs = batchInputApplet.topLevelOperator
opBatchInputs.name = 'opBatchInputs'
opBatchResults = batchResultsApplet.topLevelOperator

## Create additional batch workflow operators
opBatchFeatures = OperatorWrapper( OpFeatureSelection(graph=graph), promotedSlotNames=['InputImage'] )
opBatchFeatures.name = "opBatchFeatures"
opBatchPredictor = OperatorWrapper( OpPredictRandomForest(graph=graph), promotedSlotNames=['Image'])
opBatchPredictor.name = "opBatchPredictor"
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
shell = IlastikShell(sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)

# Add interactive workflow applets
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)
shell.addApplet(featureSelectionApplet)
shell.addApplet(pcApplet)

# Add batch workflow applets
shell.addApplet(batchInputApplet)
shell.addApplet(batchResultsApplet)

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
    #shell.openProjectFile('/home/bergs/synapse_small.ilp')
    #shell.openProjectFile('/home/bergs/flyem.ilp')
    #shell.openProjectFile('/tmp/synapse_small.ilp')
    #shell.openProjectFile('/home/bergs/dummy.ilp')
    shell.openProjectFile('/tmp/gigafly.ilp')
    
    # Select a drawer
    shell.setSelectedAppletDrawer( 3 )
    
    # Check the 'interactive mode' checkbox.
    #QTimer.singleShot( 2000, partial(pcApplet.centralWidget._labelControlUi.checkInteractive.setChecked, True) )

#timer = QTimer()
#timer.setInterval(4000)
#timer.timeout.connect( shell.scrollToTop )
#timer.start()

# Run a test
#QTimer.singleShot(1, test )

app.exec_()

