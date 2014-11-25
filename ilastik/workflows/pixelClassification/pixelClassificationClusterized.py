#!/usr/bin/env python2.7

###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################

# Standard libs
import Queue
import argparse
import functools
import logging
import os
import subprocess
import sys
import threading
import datetime

# Start with logging so other import warnings are logged.
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init(output_mode=ilastik.ilastik_logging.default_config.OutputMode.CONSOLE)
ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh
logger = logging.getLogger(__name__)

# HCI
from lazyflow.graph import OperatorWrapper

# ilastik
import ilastik_main
import ilastik.monkey_patches
from lazyflow.utility.timer import timeLogged
from ilastik.clusterConfig import parseClusterConfigFile
from ilastik.clusterOps import OpClusterize, OpTaskWorker
from ilastik.utility import log_exception

import ilastik.workflows # Load all known workflow modules


@timeLogged(logger, logging.INFO)
def main(argv):
    logger.info("Starting at {}".format( datetime.datetime.now() ))
    logger.info( "Launching with sys.argv: {}".format(sys.argv) )
    parser = getArgParser()

    ilastik.monkey_patches.extend_arg_parser(parser)
    parsed_args = parser.parse_args(argv[1:])
    ilastik.monkey_patches.apply_setting_dict( parsed_args.__dict__ )

    try:
        runWorkflow(parsed_args)
    except:
        log_exception( logger )
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
    parser.add_argument('--logfile', help='A filepath to dump all log messages to.', required=False)
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

def runWorkflow(cluster_args):
    ilastik_main_args = ilastik_main.parser.parse_args([])
    # Copy relevant args from cluster cmdline options to ilastik_main cmdline options
    ilastik_main_args.headless = True
    ilastik_main_args.project = cluster_args.project
    ilastik_main_args.process_name = cluster_args.process_name

    # Nodes should not write to a common logfile.
    # Override with /dev/null
    if cluster_args._node_work_ is None:
        ilastik_main_args.logfile = cluster_args.logfile
    else:
        ilastik_main_args.logfile = "/dev/null"
    
    assert cluster_args.project is not None, "Didn't get a project file."
    
    # Read the config file
    configFilePath = cluster_args.option_config_file
    config = parseClusterConfigFile( configFilePath )

    # Update the monkey_patch settings
    ilastik.monkey_patches.apply_setting_dict( config.__dict__ )

    # Configure the thread count.
    # Nowadays, this is done via an environment variable setting for ilastik_main to detect.
    if cluster_args._node_work_ is not None and config.task_threadpool_size is not None:
        os.environ["LAZYFLOW_THREADS"] = str(config.task_threadpool_size)
    
    if cluster_args._node_work_ is not None and config.task_total_ram_mb is not None:
        os.environ["LAZYFLOW_TOTAL_RAM_MB"] = str(config.task_total_ram_mb)

    # Instantiate 'shell' by calling ilastik_main with our 
    shell = ilastik_main.main( ilastik_main_args )
    workflow = shell.projectManager.workflow

    # Attach cluster operators
    resultSlot = None
    finalOutputSlot = workflow.getHeadlessOutputSlot( config.output_slot_id )
    assert finalOutputSlot is not None

    clusterOperator = None
    try:
        if cluster_args._node_work_ is not None:
            clusterOperator, resultSlot = prepare_node_cluster_operator(config, cluster_args, finalOutputSlot)
        else:
            clusterOperator, resultSlot = prepare_master_cluster_operator(cluster_args, finalOutputSlot)
        
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

def prepare_node_cluster_operator(config, cluster_args, finalOutputSlot):
    # We're doing node work
    opClusterTaskWorker = OperatorWrapper( OpTaskWorker, parent=finalOutputSlot.getRealOperator().parent )

    # TODO: Raise an error if finalOutputSlot has len=0.  That means the user didn't load a batch dataset into the project.

    # FIXME: Image index is hard-coded as 0.  We assume we are working with only one (big) dataset in cluster mode.            
    opClusterTaskWorker.Input.connect( finalOutputSlot )
    opClusterTaskWorker.RoiString[0].setValue( cluster_args._node_work_ )
    opClusterTaskWorker.TaskName.setValue( cluster_args.process_name )
    opClusterTaskWorker.ConfigFilePath.setValue( cluster_args.option_config_file )
    opClusterTaskWorker.OutputFilesetDescription.setValue( cluster_args.output_description_file )

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
    return (clusterOperator, resultSlot)

def prepare_master_cluster_operator(cluster_args, finalOutputSlot):
    # We're the master
    opClusterizeMaster = OperatorWrapper( OpClusterize, parent=finalOutputSlot.getRealOperator().parent )

    # TODO: Raise an error if finalOutputSlot has len=0.  That means the user didn't load a batch dataset into the project.

    opClusterizeMaster.Input.connect( finalOutputSlot )
    opClusterizeMaster.ProjectFilePath.setValue( cluster_args.project )
    opClusterizeMaster.OutputDatasetDescription.setValue( cluster_args.output_description_file )
    opClusterizeMaster.ConfigFilePath.setValue( cluster_args.option_config_file )

    resultSlot = opClusterizeMaster.ReturnCode
    clusterOperator = opClusterizeMaster
    return (clusterOperator, resultSlot)

if __name__ == "__main__":

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    debug = None
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

#         # pixel classification
#         args.append( "--option_config_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/example_cluster_options.json")
#         args.append( "--project=/nobackup/bock/ilastik/gamma-alpha/gammaAlphaFanPixelProject.ilp")
#         #args.append( "--output_description_file=/magnetic/bock_pilot/cluster_debug/results_description.json")
#         args.append( "--output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/results_description.json")
#         #args.append( "--sys_tmp_dir=/scratch/bergs")
#         args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 0, 0, 0], [260, 1000, 1000, 3])' )
#         args.append( "--process_name=JOB00" )

        # object classification
        args.append( "--_node_work_=SubRegion:SubRegion(None, [0, 0, 35000, 0, 0], [1, 1000, 36000, 130, 1])" )
        args.append( "--option_config_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/object_cluster_options.json")
        args.append( "--project=/nobackup/bock/ilastik/gamma-alpha/gamma-object-experimental-updated.ilp")
        args.append( "--output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/object_results/object_results_description.json")
        args.append( "--secondary_output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/object_results/region_features_description.json")
        args.append( "--process_name=JOBXX" )

#         args.append( "--option_config_file=/nobackup/bock/ilastik_trials/object_runs/bock11-256_object_cluster_options.json")
#         #args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/MyMutant.ilp")
#         args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/smaller_blockwise_object_test.ilp")
#         args.append( "--output_description_file=/nobackup/bock/ilastik_trials/object_runs/primary_results/object_prediction_description.json")
#         args.append( "--secondary_output_description_file=/nobackup/bock/ilastik_trials/object_runs/secondary_results_features/region_features_description.json")
#         args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 1024, 0, 0, 0], [1, 2048, 1024, 1233, 1])' )
#         #args.append( '--_node_work_=SubRegion:SubRegion(None, [0, 1024, 0, 0, 0], [1, 2048, 1024, 1233, 1])' )
#         args.append("--process_name=JOBXX")
#         args.append( "--sys_tmp_dir=/scratch/bergs")

        sys.argv += args

    # Master debug args
    if debug == 'Master' and len(sys.argv) == 1:
        args = []
        args.append( "--process_name=MASTER")

        ## LOCAL TEST
        #args.append( "--option_config_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/example_cluster_options.json")
        #args.append( "--project=/nobackup/bock/ilastik/gamma-alpha/gammaAlphaFanPixelProject.ilp")
        #args.append( "--output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/results_description.json")

        # REMOTE TEST
        #args.append( "--option_config_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/example_cluster_options.json")
        #args.append( "--project=/nobackup/bock/ilastik/gamma-alpha/gammaAlphaFanPixelProject.ilp")
        #args.append( "--output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/pixel_results_description.json")

        # Object test
        args.append( "--option_config_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/object_cluster_options.json")
        args.append( "--project=/nobackup/bock/ilastik/gamma-alpha/gamma-object-experimental-updated.ilp")
        args.append( "--output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/object_results/object_results_description.json")
        args.append( "--secondary_output_description_file=/nobackup/bock/ilastik/bock-pilot-cluster-options/object_results/region_features_description.json")

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

#         # Synapse Object classification
#         args.append( "--option_config_file=/nobackup/bock/ilastik_trials/object_runs/bock11-256_object_cluster_options.json")
#         args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/MyMutant.ilp")
#         #args.append( "--project=/nobackup/bock/ilastik_trials/object_runs/smaller_blockwise_object_test.ilp")
#         args.append( "--output_description_file=/nobackup/bock/ilastik_trials/object_runs/primary_results/object_prediction_description.json")
#         args.append( "--secondary_output_description_file=/nobackup/bock/ilastik_trials/object_runs/secondary_results_features/region_features_description.json")
#         args.append( "--sys_tmp_dir=/scratch/bergs")

        sys.argv += args

    # MAIN
    sys.exit( main(sys.argv) )






