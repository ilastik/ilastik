#!/usr/bin/env python2.7

# Standard libs
import Queue
import argparse
import functools
import logging
import os
import shutil
import subprocess
import sys
import threading
import traceback
import datetime

# Start with logging so other import warnings are logged.
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh
logger = logging.getLogger(__name__)

# HCI
import lazyflow.request
from lazyflow.graph import OperatorWrapper

# ilastik
import ilastik.utility.monkey_patches
from ilastik.utility.timer import timeLogged
from ilastik.clusterConfig import parseClusterConfigFile
from ilastik.clusterOps import OpClusterize, OpTaskWorker
from ilastik.shell.headless.headlessShell import HeadlessShell
from ilastik.utility.pathHelpers import getPathVariants
from ilastik.workflow import Workflow

import ilastik.workflows # Load all known workflow modules

@timeLogged(logger, logging.INFO)
def main(argv):
    logger.info("Starting at {}".format( datetime.datetime.now() ))
    logger.info( "Launching with sys.argv: {}".format(sys.argv) )
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
    finally:
        logger.info("Finished at {}".format( datetime.datetime.now() ))
    
    return 0

def getArgParser():
    parser = argparse.ArgumentParser( description="Ilastik Cluster Workload Launcher" )
    parser.add_argument('--process_name', default="MASTER", help='A name for this process (for logging purposes)', required=False)
    parser.add_argument('--option_config_file', help='A json file with various settings', required=True)
    parser.add_argument('--project', help='An .ilp file with feature selections and at least one labeled input image', required=True)
    parser.add_argument('--output_description_file', help='The JSON file that describes the output dataset', required=False)
    parser.add_argument('--secondary_output_description_file', help='A secondary output description file, which will be used if the workflow supports secondary outputs.', required=False, action='append')
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

        # Output log directory might be a relative path (relative to config file)
        absLogDir, relLogDir = getPathVariants(config.output_log_directory, os.path.split( configFilePath )[0] )
        if not os.path.exists(absLogDir):
            os.mkdir(absLogDir)

        # Copy the config we're using to the output directory
        shutil.copy(configFilePath, absLogDir)
        
        logFile = os.path.join( absLogDir, "MASTER.log" )
        logFileFormatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")
        rootLogHandler = logging.FileHandler(logFile, 'a')
        rootLogHandler.setFormatter(logFileFormatter)
        rootLogger = logging.getLogger()
        rootLogger.addHandler( rootLogHandler )
        logger.info( "Launched with sys.argv: {}".format( sys.argv ) )

    # Update the monkey_patch settings
    ilastik.utility.monkey_patches.apply_setting_dict( config.__dict__ )

    # If we're running a node job, set the threadpool size if the user specified one.
    # Note that the main thread does not count toward the threadpool total.
    if args._node_work_ is not None and config.task_threadpool_size is not None:
        lazyflow.request.Request.reset_thread_pool( num_workers = config.task_threadpool_size )

    # Make sure project file exists.
    if not os.path.exists(args.project):
        raise RuntimeError("Project file '" + args.project + "' does not exist.")

    # Instantiate 'shell'
    shell = HeadlessShell( functools.partial(Workflow.getSubclass(config.workflow_type) ) )
    
    # Load project (auto-import it if necessary)
    logger.info("Opening project: '" + args.project + "'")
    shell.openProjectPath(args.project)

    workflow = shell.projectManager.workflow
            
    # Attach cluster operators
    resultSlot = None
    finalOutputSlot = workflow.getHeadlessOutputSlot( config.output_slot_id )
    assert finalOutputSlot is not None

    secondaryOutputSlots = workflow.getSecondaryHeadlessOutputSlots( config.output_slot_id )
    secondaryOutputDescriptions = args.secondary_output_description_file # This is a list (see 'action' above)
    if len(secondaryOutputDescriptions) != len(secondaryOutputSlots):
        raise RuntimeError( "This workflow produces exactly {} SECONDARY outputs.  You provided {}.".format( len(secondaryOutputSlots), len(secondaryOutputDescriptions) ) )
    
    clusterOperator = None
    try:
        if args._node_work_ is not None:
            # We're doing node work
            opClusterTaskWorker = OperatorWrapper( OpTaskWorker, parent=finalOutputSlot.getRealOperator().parent )

            # FIXME: Image index is hard-coded as 0.  We assume we are working with only one (big) dataset in cluster mode.            
            opClusterTaskWorker.Input.connect( finalOutputSlot )
            opClusterTaskWorker.RoiString[0].setValue( args._node_work_ )
            opClusterTaskWorker.TaskName.setValue( task_name )
            opClusterTaskWorker.ConfigFilePath.setValue( args.option_config_file )

            # Configure optional slots first for efficiency (avoid multiple calls to setupOutputs)
            opClusterTaskWorker.SecondaryInputs[0].resize( len( secondaryOutputSlots ) )
            opClusterTaskWorker.SecondaryOutputDescriptions[0].resize( len( secondaryOutputSlots ) )
            for i in range( len(secondaryOutputSlots) ):
                opClusterTaskWorker.SecondaryInputs[0][i].connect( secondaryOutputSlots[i][0] )
                opClusterTaskWorker.SecondaryOutputDescriptions[0][i].setValue( secondaryOutputDescriptions[i] )

            opClusterTaskWorker.OutputFilesetDescription.setValue( args.output_description_file )
    
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
            opClusterizeMaster = OperatorWrapper( OpClusterize, parent=finalOutputSlot.getRealOperator().parent )

            opClusterizeMaster.Input.connect( finalOutputSlot )
            opClusterizeMaster.ProjectFilePath.setValue( args.project )
            opClusterizeMaster.OutputDatasetDescription.setValue( args.output_description_file )

            # Configure optional slots first for efficiency (avoid multiple calls to setupOutputs)
            opClusterizeMaster.SecondaryInputs[0].resize( len( secondaryOutputSlots ) )
            opClusterizeMaster.SecondaryOutputDescriptions[0].resize( len( secondaryOutputSlots ) )
            for i in range( len(secondaryOutputSlots) ):
                opClusterizeMaster.SecondaryInputs[0][i].connect( secondaryOutputSlots[i][0] )
                opClusterizeMaster.SecondaryOutputDescriptions[0][i].setValue( secondaryOutputDescriptions[i] )    

            opClusterizeMaster.ConfigFilePath.setValue( args.option_config_file )

            resultSlot = opClusterizeMaster.ReturnCode
            clusterOperator = opClusterizeMaster
        
        # Get the result
        logger.info("Starting task")
        result = resultSlot[0].value # FIXME: The image index is hard-coded here.
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
            shell.closeCurrentProject()
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

    #debug = None
    debug = 'Master'
    #debug = 'Node'

    # Task debug args
    if debug == 'Node' and len(sys.argv) == 1:
        args = []
        
#        # Object classification
#        args.append( "--option_config_file=/nobackup/bock/ilastik_trials/bock11-256_object_cluster_options.json" )
#        args.append( "--project=/nobackup/bock/ilastik_trials/stuart_object_predictions.ilp" )
#        args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 1024, 0, 0, 0], [1, 2048, 1024, 1233, 1])' )
#        args.append( "--process_name=JOB02" )
#        args.append( "--output_description_file=/nobackup/bock/ilastik_trials/dummy_object_results/results_description.json" )
#        args.append( "--secondary_output_description_file=/nobackup/bock/ilastik_trials/dummy_object_results/debug_feature_output_description.json")
#        args.append( "--sys_tmp_dir=/scratch/bergs")

        # pixel classification
#        args.append( "--option_config_file=/nobackup/bock/ilastik_trials/bock11-256_cluster_options.json")
#        args.append( "--project=/nobackup/bock/ilastik_trials/bock11-256.ilp")
#        args.append( "--output_description_file=/nobackup/bock/ilastik_trials/results/results_description.json")
#        args.append( "--sys_tmp_dir=/scratch/bergs")
#        args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 0, 0, 0], [1233, 1024, 1024, 2])' )
#        args.append( "--process_name=JOB00" )

        args.append( "--option_config_file=/nobackup/bock/ilastik_trials/object_runs/bock11-256_object_cluster_options.json")
        #args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/MyMutant.ilp")
        args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/smaller_blockwise_object_test.ilp")
        args.append( "--output_description_file=/nobackup/bock/ilastik_trials/object_runs/primary_results/object_prediction_description.json")
        args.append( "--secondary_output_description_file=/nobackup/bock/ilastik_trials/object_runs/secondary_results_features/region_features_description.json")
        args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 1024, 0, 0, 0], [1, 2048, 1024, 1233, 1])' )
        #args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 1024, 0, 0, 0], [1, 2048, 1024, 1233, 1])' )
        args.append("--process_name=JOBXX")
        args.append( "--sys_tmp_dir=/scratch/bergs")

        sys.argv += args

    # Master debug args
    if debug == 'Master' and len(sys.argv) == 1:
        args = []
        args.append( "--process_name=MASTER")

#        # SMALL TEST
#        args.append( "--option_config_file=/groups/flyem/data/bergs_scratch/cluster_options.json")
#        args.append("--project=/groups/flyem/data/bergs_scratch/project_files/synapse_small.ilp")
#        args.append( "--output_description_file=/home/bergs/clusterstuff/results/synapse_small_results/dataset_description.json")

#        # BIGGER TEST
#        args.append( "--option_config_file=/groups/flyem/data/bergs_scratch/cluster_options.json")
#        args.append( "--project=/groups/flyem/data/bergs_scratch/project_files/gigacube.ilp")
#        args.append( "--output_description_file=/home/bergs/clusterstuff/results/gigacube_predictions/dataset_description.json")

#        # RESTful TEST
#        args.append( "--option_config_file=/nobackup/bock/ilastik_trials/bock11-256_cluster_options.json")
#        #args.append( "--project=/nobackup/bock/ilastik_trials/bock11-256.ilp")
#        args.append( "--project=/nobackup/bock/ilastik_trials/Training_4_sel_features_bock11.ilp")
#        args.append( "--output_description_file=/nobackup/bock/ilastik_trials/results/results_description.json")
#        args.append( "--sys_tmp_dir=/scratch/bergs")

#        # Synapse Pixel Classification
#        args.append( "--option_config_file=/nobackup/bock/ilastik_trials/bock11-256_pixel_cluster_options.json")
#        args.append( "--project=/nobackup/bock/ilastik_trials/Training_4_sel_features_bock11.ilp")
#        args.append( "--output_description_file=/nobackup/bock/ilastik_trials/pixel_results/results_description.json")
#        args.append( "--sys_tmp_dir=/scratch/bergs")

        # Synapse Object classification
        args.append( "--option_config_file=/nobackup/bock/ilastik_trials/object_runs/bock11-256_object_cluster_options.json")
        args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/MyMutant.ilp")
        #args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/smaller_blockwise_object_test.ilp")
        args.append( "--output_description_file=/nobackup/bock/ilastik_trials/object_runs/primary_results/object_prediction_description.json")
        args.append( "--secondary_output_description_file=/nobackup/bock/ilastik_trials/object_runs/secondary_results_features/region_features_description.json")
        args.append( "--sys_tmp_dir=/scratch/bergs")

        sys.argv += args

    # MAIN
    sys.exit( main(sys.argv) )






