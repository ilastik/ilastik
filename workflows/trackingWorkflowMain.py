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

import ilastik
from ilastik.ilastikshell.ilastikShell import IlastikShell, SideSplitterSizePolicy

from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.connectedComponents.connectedComponentsApplet import ConnectedComponentsApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10)


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
ccApplet = ConnectedComponentsApplet( graph )

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
# Shell
######################

# Create the shell
shell = IlastikShell(sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)

# Add interactive workflow applets
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)
shell.addApplet(featureSelectionApplet)
shell.addApplet(pcApplet)
shell.addApplet(ccApplet)

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



app.exec_()
