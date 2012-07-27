import ilastik.utility.monkey_patches # Must be the first import

#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

from ilastik.applets.pixelClassification import PixelClassificationApplet
from ilastik.applets.projectMetadata import ProjectMetadataApplet
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.featureSelection import FeatureSelectionApplet
from ilastik.applets.batchIo import BatchIoApplet

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection

from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators import OpPredictRandomForest, OpAttributeSelector

# Logging configuration
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10)

import logging
logger = logging.getLogger(__name__)

import traceback

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

class HeadlessShell(object):
    def __init__(self):
        self.currentProjectFile = None
        self.currentProjectPath = None
        self._applets = []
        self.currentImageIndex = -1

    def addApplet(self, app):
        self._applets.append(app)

    def openProjectFile(self, projectFilePath):
        logger.info("Opening Project: " + projectFilePath)

        # Open the file as an HDF5 file
        hdf5File = h5py.File(projectFilePath)
        self.loadProject(hdf5File, projectFilePath)

    def loadProject(self, hdf5File, projectFilePath):
        """
        Load the data from the given hdf5File (which should already be open).
        """
        self.closeCurrentProject()

        assert self.currentProjectFile is None

        # Save this as the current project
        self.currentProjectFile = hdf5File
        self.currentProjectPath = projectFilePath
        # Applet serializable items are given the whole file (root group)
        for applet in self._applets:
            for item in applet.dataSerializers:
                assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                item.deserializeFromHdf5(self.currentProjectFile, projectFilePath)

    def saveProject(self):
        logger.debug("Save Project triggered")

        assert self.currentProjectFile != None
        assert self.currentProjectPath != None

        # Applet serializable items are given the whole file (root group) for now
        for applet in self._applets:
            for item in applet.dataSerializers:
                assert item.base_initialized, "AppletSerializer subclasses must call AppletSerializer.__init__ upon construction."
                if item.isDirty():
                    item.serializeToHdf5(self.currentProjectFile, self.currentProjectPath)

        # Flush any changes we made to disk, but don't close the file.
        self.currentProjectFile.flush()

    def closeCurrentProject(self):
        self.unloadAllApplets()
        if self.currentProjectFile is not None:
            self.currentProjectFile.close()
            self.currentProjectFile = None

    def unloadAllApplets(self):
        """
        Unload all applets into a blank state.
        """
        for applet in self._applets:
            # Unload the project data
            for item in applet.dataSerializers:
                item.unload()

    def changeCurrentInputImageIndex(self, newImageIndex):
        if newImageIndex != self.currentImageIndex:
            # Alert each central widget and viewer control widget that the image selection changed
            for i in range( len(self._applets) ):
                self._applets[i].gui.setImageIndex(newImageIndex)
                
            self.currentImageIndex = newImageIndex

shell = HeadlessShell()

# Add interactive workflow applets
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)
shell.addApplet(featureSelectionApplet)
shell.addApplet(pcApplet)

# Add batch workflow applets
shell.addApplet(batchInputApplet)
shell.addApplet(batchResultsApplet)

import h5py

projectFilePath = '/tmp/gigafly.ilp'
print "Opening Project: " + projectFilePath
shell.openProjectFile(projectFilePath)

## Enable prediction saving
#pcApplet.topLevelOperator.FreezePredictions.setValue(False)
#pcApplet.dataSerializers[0].predictionStorageEnabled = True
#
## Save the project (which will request all predictions)
#shell.saveProject()
#
#pcApplet.dataSerializers[0].predictionStorageEnabled = False

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
datasetInfo = DatasetInfo()
datasetInfo.location = DatasetInfo.Location.FileSystem
datasetInfo.filePath = "/home/bergs/synapse_small.h5/volume/data"
datasetInfo.allowLabels = False

opBatchInputs.Dataset.setValues( [datasetInfo] )

from ilastik.applets.batchIo.opBatchIo import ExportFormat
opBatchResults.ExportDirectory.setValue('')
opBatchResults.Format.setValue(ExportFormat.H5)
opBatchResults.Suffix.setValue('_predictions')

print "Exporting data to " + opBatchResults.OutputDataPath[0].value

currentProgress = [None]
def handleProgress(percentComplete):
    if currentProgress[0] != percentComplete:
        currentProgress[0] = percentComplete
        print "{}% complete.".format(percentComplete)
    
progressSignal = opBatchResults.ProgressSignal[0].value
progressSignal.subscribe( handleProgress )

result = opBatchResults.ExportResult[0].value

print "Closing project..."
shell.closeCurrentProject()
assert result

print "FINISHED."














