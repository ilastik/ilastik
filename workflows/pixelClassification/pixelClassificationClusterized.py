#!/usr/bin/env python2.7

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
import ilastik.utility.monkey_patches
from ilastik.shell.headless.startShellHeadless import startShellHeadless
from pixelClassificationWorkflow import PixelClassificationWorkflow
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.applets.batchIo.opBatchIo import ExportFormat
from ilastik.utility import PathComponents
import ilastik.utility.globals

from ilastik.clusterOps import OpClusterize, OpTaskWorker
from lazyflow.graph import OperatorWrapper

logger = logging.getLogger(__name__)

def main(argv):
    parser = getArgParser()
    parsed_args = parser.parse_args(argv[1:])

    #ilastik.utility.monkey_patches.init_with_args(parsed_args)

    try:
        runWorkflow(parsed_args)
    except:
        tb = traceback.format_exc()
        logger.error(tb)
        return 1
    
    return 0

def getArgParser():
    parser = argparse.ArgumentParser(description="Pixel Classification Prediction Workflow")
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=False)
    parser.add_argument('--scratch_directory', help='Scratch directory for intermediate files', required=False)
    parser.add_argument('--command_format', help='Format string for spawned tasks.  Replace argument list with a single {}', required=False)
    parser.add_argument('--num_jobs', type=int, help='Number of jobs', required=False)
    parser.add_argument('--output_file', help='The file to create', required=False)
    parser.add_argument('--_node_work_', help='Internal use only', required=False)
    return parser

def runWorkflow(parsed_args):
    args = parsed_args
    
    # Make sure project file exists.
    if not os.path.exists(args.project):
        raise RuntimeError("Project file '" + args.project + "' does not exist.")

    # Instantiate 'shell'
    shell, workflow = startShellHeadless( PixelClassificationWorkflow )
    
    assert workflow.finalOutputSlot is not None
        
    # Attach cluster operators
    resultSlot = None
    finalOutputSlot = workflow.finalOutputSlot
    if args._node_work_:
        # We're doing node work
        opClusterTaskWorker = OperatorWrapper( OpTaskWorker, graph=finalOutputSlot.graph )
        opClusterTaskWorker.ScratchDirectory.setValue( args.scratch_directory )
        opClusterTaskWorker.Input.connect( workflow.finalOutputSlot )
        resultSlot = opClusterTaskWorker.ReturnCode
    else:
        # We're the master
        opClusterizeMaster = OperatorWrapper( OpClusterize, graph=finalOutputSlot.graph )
        opClusterizeMaster.ProjectFilePath.setValue( args.project )
        opClusterizeMaster.ScratchDirectory.setValue( args.scratch_directory )
        opClusterizeMaster.OutputFilePath.setValue( args.output_file )
        opClusterizeMaster.CommandFormat.setValue( args.command_format )
        opClusterizeMaster.NumJobs.setValue( args.num_jobs )
        opClusterizeMaster.Input.connect( workflow.finalOutputSlot )
        resultSlot = opClusterizeMaster.ReturnCode
    
    # Load project (auto-import it if necessary)
    logger.info("Opening project: '" + args.project + "'")
    shell.openProjectPath(args.project)

    # Get the result
    logger.info("Starting task")
    result = resultSlot[0].value

    logger.info("Closing project...")
    shell.projectManager.closeCurrentProject()
    
    assert result    
    
    logger.info("FINISHED with result {}".format(result))
        
if __name__ == "__main__":
    # DEBUG ARGS
    if False:
#        args = ""
#        args += " --project=/home/bergs/tinyfib/boundary_training/pred.ilp"
#        args += " --batch_output_dataset_name=/volume/pred_volume"
#        args += " --batch_export_dir=/home/bergs/tmp"
#        args += " /home/bergs/tinyfib/initial_segmentation/version1.h5/volume/data"

        #args = "--project=/groups/flyem/proj/cluster/tbar_detect_files/best.ilp --batch_export_dir=/home/bergs/tmp /groups/flyem/proj/cluster/tbar_detect_files/grayscale.h5"

        #args += " --project=/home/bergs/Downloads/synapse_detection_training1.ilp"
        #args = " --project=/home/bergs/synapse_small.ilp"
        #args += " --generate_project_predictions"
        #args += " /home/bergs/synapse_small.npy"

#        args = []
#        args.append("--project=/home/bergs/synapse_small.ilp")
#        args.append("--scratch_directory=/magnetic/scratch")
#        args.append("--output_file=/magnetic/CLUSTER_RESULTS.h5")
#        args.append('--command_format="/home/bergs/workspace/applet-workflows/workflows/pixelClassification/pixelClassificationClusterized.py {}"')
#        args.append("--num_jobs=4")

        # --project=/home/bergs/synapse_small.ilp --scratch_directory=/magnetic/scratch --output_file=/magnetic/CLUSTER_RESULTS.h5 --command_format="/home/bergs/workspace/applet-workflows/workflows/pixelClassification/pixelClassificationClusterized.py {}" --num_jobs=4 


        s = ""
        for arg in args:
            s += arg + " "
        
        #print s

#        sys.argv += args

    # MAIN
    sys.exit( main(sys.argv) )







