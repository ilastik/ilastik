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
from lazyflow.utility.jsonConfig import JsonConfigParser, AutoEval, FormattedField

#: Schema for all cluster config options
#: (Doesn't specify which are required and which aren't.)
ClusterConfigFields = \
{
    "_schema_name" : "cluster-execution-configuration",
    "_schema_version" : 1.0,

    "workflow_type" : str,
    "output_slot_id" : str,

    "sys_tmp_dir" : str,
    "task_threadpool_size" : AutoEval(int),
    "task_total_ram_mb" : AutoEval(int),
    "task_timeout_secs" : AutoEval(int),
    "use_node_local_scratch" : bool,
    "use_master_local_scratch" : bool,
    "node_output_compression_cmd" :   FormattedField( requiredFields=["compressed_file", "uncompressed_file"]),
    "node_output_decompression_cmd" : FormattedField( requiredFields=["compressed_file", "uncompressed_file"]),
    "task_progress_update_command" : FormattedField( requiredFields=["progress"] ),
    "task_launch_server" : str,
    "output_log_directory" : str,
    "server_working_directory" : str,
    "command_format" : FormattedField( requiredFields=["task_args"], optionalFields=["task_name"] ),
    "debug_option_use_previous_node_files" : bool
}

def parseClusterConfigFile( configFilePath ):
    """
    Convenience function for parsing cluster configs.
    Returns a Namespace object.
    (Similar to the behavior of argparse.ArgumentParser.parse_args() )
    """
    schema = JsonConfigParser( ClusterConfigFields )
    return schema.parseConfigFile( configFilePath )

if __name__ == "__main__":
    testConfig = """
{
    "_schema_name" : "cluster-execution-configuration",
    "_schema_version" : 1.0,

    "workflow_type" : "PixelClassificationWorkflow",
    "sys_tmp_dir" : "/scratch/bergs",
    "num_jobs" : "2**3",
    "task_timeout_secs" : "20*60",
    "use_node_local_scratch" : true,
    "use_master_local_scratch" : true,
    "output_log_directory" : "/home/bergs/tmp/trial42",
    "task_progress_update_command" : "./update_job_name {progress}",
    "command_format" : "qsub -pe batch 4 -l short=true -N {task_name} -j y -b y -cwd -V '/groups/flyem/proj/builds/cluster/src/ilastik-HEAD/ilastik_clusterized {task_args}'"
}
"""
    # Create a temporary file
    import tempfile
    fname = tempfile.mktemp()
    with file(fname, 'w') as f:
        f.write(testConfig)
    
    config = parseClusterConfigFile(fname)
    assert config.workflow_type == "PixelClassificationWorkflow"
    assert isinstance(config.workflow_type, str)
    assert config.use_node_local_scratch is True
    assert config.task_timeout_secs == 20*60

    print config.output_log_directory
    
    