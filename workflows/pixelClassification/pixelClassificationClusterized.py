#!/usr/bin/env python2.7

# Standard libs
import os
import sys
import argparse
import logging
import traceback
import functools
import subprocess
import threading
import Queue
import shutil

# ilastik
from ilastik.workflow import Workflow
import ilastik.utility.monkey_patches
from ilastik.shell.headless.headlessShell import HeadlessShell
from ilastik.clusterConfig import parseClusterConfigFile

import workflows # Load all known workflow modules

from ilastik.clusterOps import OpClusterize, OpTaskWorker
from lazyflow.graph import OperatorWrapper

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh

logger = logging.getLogger(__name__)

def main(argv):
    logger.debug( "Launching with sys.argv: {}".format(sys.argv) )
    parser = getArgParser()

    ilastik.utility.monkey_patches.extend_arg_parser(parser)
    parsed_args = parser.parse_args(argv[1:])
    ilastik.utility.monkey_patches.apply_setting_dict( parsed_args.__dict__ )

    try:
        runWorkflow(parsed_args)
    except:
        tb = traceback.print_exc()
        logger.error(tb)
        return 1
    
    return 0

def getArgParser():
    parser = argparse.ArgumentParser( description="Pixel Classification Prediction Workflow" )
    parser.add_argument('--process_name', default="MASTER", help='A name for this process (for logging purposes)', required=False)
    parser.add_argument('--option_config_file', help='A json file with various settings', required=True)
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=True)
    parser.add_argument('--output_file', help='The file to create', required=False)
    parser.add_argument('--_node_work_', help='Internal use only', required=False)

    return parser

background_tasks = Queue.Queue()
stop_background_tasks = False
def do_tasks():
    while not stop_background_tasks:
        task = background_tasks.get()
        task()

background_thread = threading.Thread( target=do_tasks )
background_thread.daemon = True
background_thread.start()

def runWorkflow(parsed_args):
    args = parsed_args

    # Read the config file
    configFilePath = args.option_config_file
    config = parseClusterConfigFile( configFilePath )

    # If we've got a process name, re-initialize the logger from scratch
    task_name = "node"
    if args.process_name is not None:
        task_name = args.process_name
        ilastik.ilastik_logging.default_config.init(args.process_name + ' ')

    rootLogHandler = None
    if args._node_work_ is None:
        # This is the master process.
        # Tee the log to a file for future reference.
        logDir = config.output_log_directory
        if not os.path.exists(logDir):
            os.mkdir(logDir)

        # Copy the config we're using to the output directory
        shutil.copy(configFilePath, logDir)
        
        logFile = os.path.join( logDir, "MASTER.log" )
        logFileFormatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
        rootLogHandler = logging.FileHandler(logFile, 'a')
        rootLogHandler.setFormatter(logFileFormatter)
        rootLogger = logging.getLogger()
        rootLogger.addHandler( rootLogHandler )
        logger.info( "Launched with sys.argv: {}".format( sys.argv ) )

    # Update the monkey_patch settings
    ilastik.utility.monkey_patches.apply_setting_dict( config.__dict__ )

    # Make sure project file exists.
    if not os.path.exists(args.project):
        raise RuntimeError("Project file '" + args.project + "' does not exist.")

    # Instantiate 'shell'
    shell = HeadlessShell( functools.partial(Workflow.getSubclass(config.workflow_type), appendBatchOperators=False) )
    
    # Load project (auto-import it if necessary)
    logger.info("Opening project: '" + args.project + "'")
    shell.openProjectPath(args.project)

    workflow = shell.projectManager.workflow
    
    assert workflow.finalOutputSlot is not None
        
    # Attach cluster operators
    resultSlot = None
    finalOutputSlot = workflow.finalOutputSlot
    clusterOperator = None
    try:
        if args._node_work_ is not None:
            # We're doing node work
            opClusterTaskWorker = OperatorWrapper( OpTaskWorker, graph=finalOutputSlot.graph )
            opClusterTaskWorker.Input.connect( workflow.finalOutputSlot )
            opClusterTaskWorker.TaskName.setValue( task_name )
            opClusterTaskWorker.RoiString.setValue( args._node_work_ )
            opClusterTaskWorker.ConfigFilePath.setValue( args.option_config_file )
    
            # If we have a way to report task progress (e.g. by updating the job name),
            #  then subscribe to progress signals
            if config.task_progress_update_command is not None:
                def report_progress( progress ):
                    cmd = config.task_progress_update_command.format( progress=int(progress) )
                    def shell_call(shell_cmd):
                        logger.debug( "Executing progress command: " + cmd )
                        subprocess.call( shell_cmd, shell=True )
                    background_tasks.put( functools.partial( shell_call, cmd ) )
                opClusterTaskWorker.innerOperators[0].progressSignal.subscribe( report_progress )
            
            resultSlot = opClusterTaskWorker.ReturnCode
            clusterOperator = opClusterTaskWorker
        else:
            # We're the master
            opClusterizeMaster = OperatorWrapper( OpClusterize, graph=finalOutputSlot.graph )
            opClusterizeMaster.Input.connect( workflow.finalOutputSlot )
            opClusterizeMaster.ProjectFilePath.setValue( args.project )
            opClusterizeMaster.OutputFilePath.setValue( args.output_file )
            opClusterizeMaster.ConfigFilePath.setValue( args.option_config_file )

            resultSlot = opClusterizeMaster.ReturnCode
            clusterOperator = opClusterizeMaster
        
        # Get the result
        logger.info("Starting task")
        result = resultSlot[0].value
    finally:
        logger.info("Cleaning up")
        global stop_background_tasks
        stop_background_tasks = True
        
        try:
            if clusterOperator is not None:
                clusterOperator.cleanUp()
        except:
            logger.error("Errors during cleanup.")

        try:
            logger.info("Closing project...")
            del shell
        except:
            logger.error("Errors while closing project.")
    
    logger.info("FINISHED with result {}".format(result))
    if not result:
        logger.error( "FAILED TO COMPLETE!" )

    if rootLogHandler is not None:
        rootLogHandler.close()
        
if __name__ == "__main__":

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # DEBUG ARGS
    if True and len(sys.argv) == 1:

        args = []
        args.append( "--process_name=MASTER")
        args.append( "--option_config_file=/groups/flyem/proj/builds/cluster/src/ilastik-HEAD/ilastik/cluster_options.json")

#        # SMALL TEST
#        args.append("--project=/groups/flyem/data/bergs_scratch/project_files/synapse_small.ilp")
#        args.append( "--output_file=/home/bergs/clusterstuff/results/SYNAPSE_SMALL_RESULTS.h5")

        # BIGGER TEST
        args.append( "--project=/groups/flyem/data/bergs_scratch/project_files/gigacube.ilp")
        args.append( "--output_file=/home/bergs/clusterstuff/results/GIGACUBE_RESULTS.h5")

        s = ""
        for arg in args:
            s += arg + " "
        
        sys.argv += args

    # MAIN
    sys.exit( main(sys.argv) )






