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
from ilastik.workflow import Workflow
import ilastik.utility.monkey_patches
from ilastik.shell.headless.startShellHeadless import startShellHeadless
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.applets.batchIo.opBatchIo import ExportFormat
from ilastik.utility import PathComponents
import ilastik.utility.globals

import workflows # Load all known workflow modules

from ilastik.clusterOps import OpClusterize, OpTaskWorker
from lazyflow.graph import OperatorWrapper

logger = logging.getLogger(__name__)

def main(argv):
    logger.info( "Launching with sys.argv: {}".format(sys.argv) )
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
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=True)
    parser.add_argument('--workflow_type', help='The name of the workflow class to load with this project', required=True)
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
    shell, workflow = startShellHeadless( Workflow.getSubclass(args.workflow_type) )
    
    assert workflow.finalOutputSlot is not None
        
    # Attach cluster operators
    resultSlot = None
    finalOutputSlot = workflow.finalOutputSlot
    if args._node_work_:
        # We're doing node work
        opClusterTaskWorker = OperatorWrapper( OpTaskWorker, graph=finalOutputSlot.graph )
        opClusterTaskWorker.ScratchDirectory.setValue( args.scratch_directory )
        opClusterTaskWorker.RoiString.setValue( args._node_work_ )
        opClusterTaskWorker.Input.connect( workflow.finalOutputSlot )
        resultSlot = opClusterTaskWorker.ReturnCode
    else:
        # We're the master
        opClusterizeMaster = OperatorWrapper( OpClusterize, graph=finalOutputSlot.graph )
        opClusterizeMaster.ProjectFilePath.setValue( args.project )
        opClusterizeMaster.WorkflowTypeName.setValue( args.workflow_type )
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

    if False:
        sys.argv += ['--project=/magnetic/synapse_small.ilp', "--_node_work_=ccopy_reg\n_reconstructor\np1\n(clazyflow.rtype\nSubRegion\np2\nc__builtin__\nobject\np3\nNtRp4\n(dp5\nS'slot'\np6\nNsS'start'\np7\ng1\n(clazyflow.roi\nTinyVector\np8\nc__builtin__\nlist\np9\n(lp10\ncnumpy.core.multiarray\nscalar\np11\n(cnumpy\ndtype\np12\n(S'i8'\nI0\nI1\ntRp13\n(I3\nS'<'\nNNNI-1\nI-1\nI0\ntbS'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp14\nag11\n(g13\nS'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp15\nag11\n(g13\nS'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp16\nag11\n(g13\nS'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp17\nag11\n(g13\nS'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp18\natRp19\nsS'stop'\np20\ng1\n(g8\ng9\n(lp21\ng11\n(g13\nS'\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp22\nag11\n(g13\nS'\\x90\\x01\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp23\nag11\n(g13\nS'\\x90\\x01\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp24\nag11\n(g13\nS'2\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp25\nag11\n(g13\nS'\\x02\\x00\\x00\\x00\\x00\\x00\\x00\\x00'\ntRp26\natRp27\nsS'dim'\np28\nI5\nsb.", '--scratch_directory=/magnetic/scratch']
    # MAIN
    sys.exit( main(sys.argv) )







