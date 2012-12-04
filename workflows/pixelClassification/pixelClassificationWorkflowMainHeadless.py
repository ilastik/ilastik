#!/usr/bin/env python2.7

# Standard libs
import os
import sys
import argparse
import logging
import traceback
import hashlib
import glob
import pickle

# Third-party
import h5py

# HCI
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpStackToH5Writer

# ilastik
import ilastik.utility.monkey_patches
from ilastik.shell.headless.headlessShell import HeadlessShell
from pixelClassificationWorkflow import PixelClassificationWorkflow
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.applets.batchIo.opBatchIo import ExportFormat
from ilastik.utility import PathComponents
import ilastik.utility.globals

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

logger = logging.getLogger(__name__)

def main(argv):
    parser = getArgParser()
    parsed_args = parser.parse_args(argv[1:])

    ilastik.utility.monkey_patches.init_with_args(parsed_args)

    try:
        runWorkflow(parsed_args)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return 1
    
    return 0

def getArgParser():
    parser = argparse.ArgumentParser(description="Pixel Classification Prediction Workflow")
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=True)
    parser.add_argument('--generate_project_predictions', action='store_true', help="Compute full volume predictions for project data and save to project (otherwise, just export predictions for batch inputs).")
    parser.add_argument('--batch_export_dir', default='', help='A directory to save batch outputs. (Default saves with input files)')
    parser.add_argument('--batch_output_suffix', default='_prediction', help='Suffix for batch output filenames (before extension).')
    parser.add_argument('--batch_output_dataset_name', default='/volume/prediction', help='HDF5 internal dataset path')
    parser.add_argument('--sys_tmp_dir', help='Override the default directory for temporary file storage.')
    parser.add_argument('--assume_old_ilp_axes', action='store_true', help='When importing 0.5 project files, assume axes are in the wrong order and need to be transposed.')
    parser.add_argument('--stack_volume_cache_dir', default='/tmp', help='The preprocessing step converts image stacks to hdf5 volumes.  The volumes will be saved to this directory.')
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
        p = PathComponents(p).externalPath
        if '*' in p:
            if len(glob.glob(p)) == 0:
                logger.error("Could not find any files for globstring: {}".format(p))
                logger.error("Check your quotes!")
                error = True
        elif not os.path.exists(p):
            logger.error("Batch input file does not exist: " + p)
            error = True
        if error:
            raise RuntimeError("Could not find one or more batch inputs.  See logged errors.")

    # Instantiate 'shell'
    shell = HeadlessShell( PixelClassificationWorkflow )
    
    if args.assume_old_ilp_axes:
        # Special hack for Janelia: 
        # In some old versions of 0.5, the data was stored in tyxzc order.
        # We have no way of inspecting the data to determine this, so we allow 
        #  users to specify that their ilp is very old using the 
        #  assume_old_ilp_axes command-line flag
        ilastik.utility.globals.ImportOptions.default_axis_order = 'tyxzc'

    # Load project (auto-import it if necessary)
    logger.info("Opening project: '" + args.project + "'")
    shell.openProjectPath(args.project)

    try:
        if not args.generate_project_predictions and len(args.batch_inputs) == 0:
            logger.error("Command-line arguments didn't specify any classification jobs.")
        else:
            # Predictions for project input datasets
            if args.generate_project_predictions:
                generateProjectPredictions(shell)
        
            # Predictions for other datasets ('batch datasets')
            result = True
            if len(args.batch_inputs) > 0:
                result = generateBatchPredictions(shell.workflow,
                                                  args.batch_inputs,
                                                  args.batch_export_dir,
                                                  args.batch_output_suffix,
                                                  args.batch_output_dataset_name,
                                                  args.stack_volume_cache_dir)
                assert result
    finally:
        logger.info("Closing project...")
        del shell

    logger.info("FINISHED.")
        
def generateProjectPredictions(shell):
    """
    Compute predictions for all project inputs (not batch inputs), and save them to the project file.
    """
    # Set up progress display handling (just logging for now)        
    currentProgress = [None]
    def handleProgress(percentComplete):
        if currentProgress[0] != percentComplete:
            currentProgress[0] = percentComplete
            logger.info("Project Predictions: {}% complete.".format(percentComplete))
    shell.workflow.pcApplet.progressSignal.connect( handleProgress )
    
    # Enable prediction saving
    shell.workflow.pcApplet.topLevelOperator.FreezePredictions.setValue(False)
    shell.workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = True

    # Save the project (which will request all predictions)
    shell.projectManager.saveProject()
    
    shell.workflow.pcApplet.dataSerializers[0].predictionStorageEnabled = False

def generateBatchPredictions(workflow, batchInputPaths, batchExportDir, batchOutputSuffix, exportedDatasetName, stackVolumeCacheDir):
    """
    Compute the predictions for each of the specified batch input files,
    and export them to corresponding h5 files.
    """
    originalBatchInputPaths = list(batchInputPaths)
    batchInputPaths = convertStacksToH5(batchInputPaths, stackVolumeCacheDir)

    batchInputInfos = []
    for p in batchInputPaths:
        info = DatasetInfo()
        info.location = DatasetInfo.Location.FileSystem

        # Convert all paths to absolute 
        # (otherwise they are relative to the project file, which probably isn't what the user meant)        
        comp = PathComponents(p)
        comp.externalPath = os.path.abspath(comp.externalPath)
        
        info.filePath = comp.totalPath()        
        batchInputInfos.append(info)

    # Configure batch input operator
    opBatchInputs = workflow.batchInputApplet.topLevelOperator
    opBatchInputs.Dataset.setValues( batchInputInfos )
    
    # Configure batch export operator
    opBatchResults = workflow.batchResultsApplet.topLevelOperator

    # By default, the output files from the batch export operator
    #  are named using the input file name.
    # If we converted any stacks to hdf5, then the user won't recognize the input file name.
    # Let's override the output file name using the *original* input file names.
    outputFileNameBases = []
    for origPath in originalBatchInputPaths:
        outputFileNameBases.append( origPath.replace('*', 'STACKED') )

    opBatchResults.OutputFileNameBase.setValues( outputFileNameBases )    
    opBatchResults.ExportDirectory.setValue(batchExportDir)
    opBatchResults.Format.setValue(ExportFormat.H5)
    opBatchResults.Suffix.setValue(batchOutputSuffix)
    opBatchResults.InternalPath.setValue(exportedDatasetName)
    
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

def convertStacksToH5(filePaths, stackVolumeCacheDir):
    """
    If any of the files in filePaths appear to be globstrings for a stack,
    convert the given stack to hdf5 format.  
    Return the filePaths list with globstrings replaced by the paths to the new hdf5 volumes.
    """
    filePaths = list(filePaths)
    for i, path in enumerate(filePaths):
        if '*' in path:
            globstring = path

            # Embrace paranoia:
            # We want to make sure we never re-use a stale cache file for a new dataset,
            #  even if the dataset is located in the same location as a previous one and has the same globstring!
            # Create a sha-1 of the file name and modification date.
            sha = hashlib.sha1()
            files = glob.glob( path )
            for f in files:
                sha.update(f)
                sha.update(pickle.dumps(os.stat(f).st_mtime))
            stackFile = sha.hexdigest() + '.h5'
            stackPath = os.path.join( stackVolumeCacheDir, stackFile )
            
            # Overwrite original path
            filePaths[i] = stackPath + "/volume/data"

            # Generate the hdf5 if it doesn't already exist
            if os.path.exists(stackPath):
                logger.info( "Using previously generated hdf5 volume for stack {}".format(path) )
                logger.info( "Volume path: {}".format(filePaths[i]) )
            else:
                logger.info( "Generating hdf5 volume for stack {}".format(path) )
                logger.info( "Volume path: {}".format(filePaths[i]) )

                if not os.path.exists( stackVolumeCacheDir ):
                    os.makedirs( stackVolumeCacheDir )
                
                with h5py.File(stackPath) as f:
                    # Configure the conversion operator
                    opWriter = OpStackToH5Writer( graph=Graph() )
                    opWriter.hdf5Group.setValue(f)
                    opWriter.hdf5Path.setValue("volume/data")
                    opWriter.GlobString.setValue(globstring)
                    
                    # Initiate the write
                    success = opWriter.WriteImage.value
        
    return filePaths

if __name__ == "__main__":
    # DEBUG ARGS
    if False:
        args = ""
        #args += " --project=/home/bergs/tinyfib/boundary_training/pred.ilp"
        args += " --project=/home/bergs/tinyfib/boundary_training/pred_imported.ilp"
        args += " --batch_output_dataset_name=/volume/pred_volume"
        args += " --batch_export_dir=/home/bergs/tmp"
#        args += " /home/bergs/tinyfib/initial_segmentation/version1.h5/volume/data"
        args += " /magnetic/small_seq/111211_subset_PSC_final_export_scaled_1k_00*.png"

        #args = "--project=/groups/flyem/proj/cluster/tbar_detect_files/best.ilp --batch_export_dir=/home/bergs/tmp /groups/flyem/proj/cluster/tbar_detect_files/grayscale.h5"
        #args = "--project=/groups/flyem/proj/cluster/tbar_detect_files/best.ilp" # --batch_export_dir=/home/bergs/tmp /groups/flyem/proj/cluster/tbar_detect_files/grayscale.h5"

        print args

        #args += " --project=/home/bergs/Downloads/synapse_detection_training1.ilp"
        #args = " --project=/home/bergs/synapse_small.ilp"
        #args += " --generate_project_predictions"
        #args += " /home/bergs/synapse_small.npy"

        sys.argv += args.split()

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # MAIN
    sys.exit( main(sys.argv) )











