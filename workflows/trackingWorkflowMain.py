import h5py
import numpy
from abc import ABCMeta

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4.QtCore import QTimer

import ilastik
from ilastik.shell.gui.ilastikShell import IlastikShell, SideSplitterSizePolicy

from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.tracking.trackingApplet import TrackingApplet
from ilastik.applets.objectExtraction.objectExtractionApplet import ObjectExtractionApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10)



from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from ilastik.applets.tracking.opTracking import *
import ctracking
class OpTrackingDataProvider( Operator ):
    Raw = OutputSlot()
    LabelImage = OutputSlot()
    Traxels = OutputSlot( stype=Opaque )

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpTrackingDataProvider, self).__init__(parent=parent, graph=graph,register=register)
        self._traxel_cache = None

        self._rawReader = OpInputDataReader( graph )
        self._rawReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/raw')
        self.Raw.connect( self._rawReader.Output )

        self._labelImageReader = OpInputDataReader( graph )
        self._labelImageReader.FilePath.setValue('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5/objects')
        self.LabelImage.connect( self._labelImageReader.Output )

    def setupOutputs( self ):
        self.Traxels.meta.shape = self.LabelImage.meta.shape
        self.Traxels.meta.dtype = self.LabelImage.meta.dtype

    def execute( self, slot, roi, result ):
        if slot is self.Traxels:
            if self._traxel_cache:
                return self._traxel_cache
            else:
                print "extract traxels"
                self._traxel_cache = ctracking.TraxelStore()
                f = h5py.File("/home/bkausler/src/ilastik/tracking/relabeled-stack/regioncenter.h5", 'r')
                for t in range(15):
                    og = f['samples/'+str(t)+'/objects']
                    traxels = cTraxels_from_objects_group( og, t)
                    self._traxel_cache.add_from_Traxels(traxels)
                    print "-- extracted %d traxels at t %d" % (len(traxels), t)
                f.close()
                return self._traxel_cache




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
# projectMetadataApplet = ProjectMetadataApplet()
dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
# featureSelectionApplet = FeatureSelectionApplet(graph, "Feature Selection", "FeatureSelections")
# pcApplet = PixelClassificationApplet(graph, "PixelClassification")
objectExtractionApplet = ObjectExtractionApplet( graph )
trackingApplet = TrackingApplet( graph )

## Access applet operators
#opData = dataSelectionApplet.topLevelOperator
#opTrainingFeatures = featureSelectionApplet.topLevelOperator
#opClassify = pcApplet.topLevelOperator
opTracking = trackingApplet.topLevelOperator

## Connect operators ##
dataProv = OpTrackingDataProvider( graph=graph )
opTracking.LabelImage.connect( dataProv.LabelImage )
opTracking.RawData.connect( dataProv.Raw )
opTracking.Traxels.connect( dataProv.Traxels )


# Input Image -> Feature Op
#         and -> Classification Op (for display)
#opTrainingFeatures.InputImage.connect( opData.Image )
#opClassify.InputImages.connect( opData.Image )

# Feature Images -> Classification Op (for training, prediction)
#opClassify.FeatureImages.connect( opTrainingFeatures.OutputImage )
#opClassify.CachedFeatureImages.connect( opTrainingFeatures.CachedOutputImage )

# Training flags -> Classification Op (for GUI restrictions)
#opClassify.LabelsAllowedFlags.connect( opData.AllowLabels )



######################
# Shell
######################

# Create the shell
shell = IlastikShell(sideSplitterSizePolicy=SideSplitterSizePolicy.Manual)

# Add interactive workflow applets
#shell.addApplet(projectMetadataApplet)
#shell.addApplet(dataSelectionApplet)
#shell.addApplet(featureSelectionApplet)
#shell.addApplet(pcApplet)
shell.addApplet(objectExtractionApplet)
shell.addApplet(trackingApplet)

# The shell needs a slot from which he can read the list of image names to switch between.
# Use an OpAttributeSelector to create a slot containing just the filename from the OpDataSelection's DatasetInfo slot.
#opSelectFilename = OperatorWrapper( OpAttributeSelector(graph=graph) )
#opSelectFilename.InputObject.connect( opData.Dataset )
#opSelectFilename.AttributeName.setValue( 'filePath' )
#shell.setImageNameListSlot( opSelectFilename.Result )

# Start the shell GUI.
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

app.exec_()
