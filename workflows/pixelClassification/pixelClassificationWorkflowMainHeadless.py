import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.headless.startShellHeadless import startShellHeadless
from pixelClassificationWorkflow import PixelClassificationWorkflow

import h5py

projectFilePath = '/home/bergs/gigacube.ilp'
print "Opening Project: " + projectFilePath

shell, workflow = startShellHeadless( PixelClassificationWorkflow, projectFilePath )

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

opBatchInputs = workflow.batchInputApplet.topLevelOperator
opBatchInputs.Dataset.setValues( [datasetInfo] )

from ilastik.applets.batchIo.opBatchIo import ExportFormat
opBatchResults = workflow.batchResultsApplet.topLevelOperator
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














