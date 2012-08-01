import ilastik.utility.monkey_patches # Must be the first import

# Standard libs
import os
import sys
import argparse
import logging
import traceback

# Third-party
import h5py

# HCI
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackToH5Writer

# ilastik
from ilastik.shell.headless.startShellHeadless import startShellHeadless
from pixelClassificationWorkflow import PixelClassificationWorkflow
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.applets.batchIo.opBatchIo import ExportFormat

logger = logging.getLogger(__name__)

def getArgParser():
    parser = argparse.ArgumentParser(description="Pixel Classification Prediction Workflow")
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=True)
    parser.add_argument('--generate_project_predictions', action='store_true', help="Compute full volume predictions for project data and save to project (otherwise, just export predictions for batch inputs).")
    parser.add_argument('batch_inputs', nargs='*', help='List of input files to process. Supported filenames: .h5, .npy, or globstring for stacks (e.g. *.png)')
    return parser

def runWorkflow(parsed_args):
    args = parsed_args
    
    # Make sure project file exists.
    if not os.path.exists(args.project):
        raise RuntimeError("Project file '" + args.project + "' does not exist.")

    # Make sure batch inputs exist.
    for p in args.batch_inputs:
        error = False
        if not os.path.exists(p):
            logger.error("Batch input file does not exist: " + p)
            error = True
        if error:
            raise RuntimeError("Could not find one or more batch inputs.  See logged errors.")
    
    # Instantiate 'shell'
    shell, workflow = startShellHeadless( PixelClassificationWorkflow )
    
    # Load project (imports it if necessary)
    logger.info("Opening project: '" + args.project + "'")
    shell.openProjectPath(args.project)

    if args.generate_project_predictions:
        generateProjectPredictions(shell, workflow)

    result = True
    if len(args.batch_inputs) > 0:
        result = generateBatchPredictions(workflow, args.batch_inputs)

    if not args.generate_project_predictions and len(args.batch_inputs) == 0:
        logger.error("Arguments didn't specify a workload.")

    logger.info("Closing project...")
    shell.projectManager.closeCurrentProject()
    
    assert result    
    
    logger.info("FINISHED.")
        
def generateProjectPredictions(shell, workflow):
    """
    Compute predictions for all project inputs (not batch inputs), and save them to the project file.
    """
    # Set up progress display handling (just logging for now)        
    currentProgress = [None]
    def handleProgress(percentComplete):
        if currentProgress[0] != percentComplete:
            currentProgress[0] = percentComplete
            logger.info("Project Predictions: {}% complete.".format(percentComplete))
    workflow.pcApplet.progressSignal.connect( handleProgress )
    
    # Enable prediction saving
    workflow.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
    workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = True

    # Save the project (which will request all predictions)
    shell.projectManager.saveProject()
    
    workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = False

def generateBatchPredictions(workflow, batchInputPaths):
    """
    Compute the predictions for each of the specified batch input files,
    and export them to corresponding h5 files.
    """
    batchInputPaths = convertStacksToH5(batchInputPaths)

    batchInputInfos = []
    for p in batchInputPaths:
        info = DatasetInfo()
        info.location = DatasetInfo.Location.FileSystem
        info.filePath = p
        batchInputInfos.append(info)

    # Configure batch input operator
    opBatchInputs = workflow.batchInputApplet.topLevelOperator
    opBatchInputs.Dataset.setValues( batchInputInfos )
    
    # Configure batch export operator
    opBatchResults = workflow.batchResultsApplet.topLevelOperator
    opBatchResults.ExportDirectory.setValue('')
    opBatchResults.Format.setValue(ExportFormat.H5)
    opBatchResults.Suffix.setValue('_predictions')
    
    logger.info( "Exporting data to " + opBatchResults.OutputDataPath[0].value )

    # Set up progress display handling (just logging for now)        
    currentProgress = [None]
    def handleProgress(percentComplete):
        if currentProgress[0] != percentComplete:
            currentProgress[0] = percentComplete
            logger.info("Batch job: {}% complete.".format(percentComplete))
        
    progressSignal = opBatchResults.ProgressSignal[0].value
    progressSignal.subscribe( handleProgress )

    # Make it happen!
    result = opBatchResults.ExportResult[0].value
    return result

def convertStacksToH5(filePaths):
    """
    If any of the files in filePaths appear to be globstrings for a stack,
    convert the given stack to hdf5 format.  
    Return the filePaths list with globstrings replaced by the paths to the new hdf5 volumes.
    """
    filePaths = list(filePaths)
    for i, path in enumerate(filePaths):
        if '*' in path:
            globstring = path
            stackPath = os.path.splitext(globstring)[0]
            stackPath.replace('*', "_VOLUME")
            stackPath += ".h5"
            
            # Overwrite original path
            filePaths[i] = stackPath + "/volume/data"

            # Generate the hdf5 if it doesn't already exist
            if not os.path.exists(stackPath):
                f = h5py.File(stackPath)
    
                # Configure the conversion operator
                opWriter = OpStackToH5Writer( graph=Graph() )
                opWriter.hdf5Group.setValue(f)
                opWriter.hdf5Path.setValue("volume/data")
                opWriter.GlobString.setValue(globstring)
                
                # Initiate the write
                success = opWriter.WriteImage.value
                f.close()
        
    return filePaths

def main():
    parser = getArgParser()
    args = parser.parse_args()

    try:
        runWorkflow(args)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return 1
    
    return 0
    
if __name__ == "__main__":
    if False:
        # DEBUG ARGS
        args = "--project=/home/bergs/synapse_small.ilp --generate_project_predictions /home/bergs/synapse_small.npy"
        sys.argv += args.split()

    # MAIN
    sys.exit( main() )











