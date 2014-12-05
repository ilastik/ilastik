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
import os
import copy
import subprocess
import collections
import hashlib
import functools

import numpy

from lazyflow.rtype import Roi, SubRegion
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
from lazyflow.utility import BigRequestStreamer
from lazyflow.utility.io.blockwiseFileset import BlockwiseFileset
from lazyflow.utility.timer import Timer
from lazyflow.utility.pathHelpers import getPathVariants

from ilastik.clusterConfig import parseClusterConfigFile
from ilastik.workflow import Workflow

import logging
logger = logging.getLogger(__name__)

class OpTaskWorker(Operator):
    Input = InputSlot()
    RoiString = InputSlot(stype='string')
    TaskName = InputSlot(stype='string')
    ConfigFilePath = InputSlot(stype='filestring')
    OutputFilesetDescription = InputSlot(stype='filestring')

    ReturnCode = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpTaskWorker, self ).__init__( *args, **kwargs )
        self.progressSignal = OrderedSignal()
        self._primaryBlockwiseFileset = None

    def setupOutputs(self):
        self.ReturnCode.meta.dtype = bool
        self.ReturnCode.meta.shape = (1,)
        
        self._closeFiles()
        self._primaryBlockwiseFileset = BlockwiseFileset( self.OutputFilesetDescription.value, 'a' )        
    
    def cleanUp(self):
        self._closeFiles()
        super( OpTaskWorker, self ).cleanUp()

    def _closeFiles(self):
        if self._primaryBlockwiseFileset is not None:
            self._primaryBlockwiseFileset.close()
        self._primaryBlockwiseFileset = None

    def execute(self, slot, subindex, ignored_roi, result):
        configFilePath = self.ConfigFilePath.value
        config = parseClusterConfigFile( configFilePath )        
        
        blockwiseFileset = self._primaryBlockwiseFileset
        
        # Check axis compatibility
        inputAxes = self.Input.meta.getTaggedShape().keys()
        outputAxes = list(blockwiseFileset.description.axes)
        assert set(inputAxes) == set(outputAxes), \
            "Output dataset has the wrong set of axes.  Input axes: {}, Output axes: {}".format( "".join(inputAxes), "".join(outputAxes) )
        
        roiString = self.RoiString.value
        roi = Roi.loads(roiString)
        if len( roi.start ) != len( self.Input.meta.shape ):
            assert False, "Task roi: {} is not valid for this input.  Did the master launch this task correctly?".format( roiString )

        logger.info( "Executing for roi: {}".format(roi) )

        if config.use_node_local_scratch:
            assert False, "FIXME."

        assert (blockwiseFileset.getEntireBlockRoi( roi.start )[1] == roi.stop).all(), "Each task must execute exactly one full block.  ({},{}) is not a valid block roi.".format( roi.start, roi.stop )
        assert self.Input.ready()

        with Timer() as computeTimer:
            # Stream the data out to disk.
            request_blockshape = self._primaryBlockwiseFileset.description.sub_block_shape # Could be None.  That's okay.
            streamer = BigRequestStreamer(self.Input, (roi.start, roi.stop), request_blockshape )
            streamer.progressSignal.subscribe( self.progressSignal )
            streamer.resultSignal.subscribe( self._handlePrimaryResultBlock )
            streamer.execute()

            # Now the block is ready.  Update the status.
            blockwiseFileset.setBlockStatus( roi.start, BlockwiseFileset.BLOCK_AVAILABLE )

        logger.info( "Finished task in {} seconds".format( computeTimer.seconds() ) )
        result[0] = True
        return result

    def propagateDirty(self, slot, subindex, roi):
        self.ReturnCode.setDirty( slice(None) )
        
    def _handlePrimaryResultBlock(self, roi, result):
        # First write the primary
        self._primaryBlockwiseFileset.writeData(roi, result)

        # Ask the workflow if there is any special post-processing to do...
        self.get_workflow().postprocessClusterSubResult(roi, result, self._primaryBlockwiseFileset)

    def get_workflow(self):
        op = self
        while not isinstance(op, Workflow):
            op = op.parent
        return op

class OpClusterize(Operator):
    Input = InputSlot()
    OutputDatasetDescription = InputSlot()
    ProjectFilePath = InputSlot(stype='filestring')
    ConfigFilePath = InputSlot(stype='filestring')
    
    ReturnCode = OutputSlot()

    class TaskInfo():
        taskName = None
        command = None
        subregion = None
        
    def setupOutputs(self):
        self.ReturnCode.meta.dtype = bool
        self.ReturnCode.meta.shape = (1,)

    def execute(self, slot, subindex, roi, result):
        dtypeBytes = self._getDtypeBytes()
        totalBytes = dtypeBytes * numpy.prod(self.Input.meta.shape)
        totalMB = totalBytes / (1000*1000)
        logger.info( "Clusterizing computation of {} MB dataset, outputting according to {}".format(totalMB, self.OutputDatasetDescription.value) )

        configFilePath = self.ConfigFilePath.value
        self._config = parseClusterConfigFile( configFilePath )

        # Create the destination file if necessary
        blockwiseFileset, taskInfos = self._prepareDestination()

        try:
            # Figure out which work doesn't need to be recomputed (if any)
            unneeded_rois = []
            for roi in taskInfos.keys():
                if blockwiseFileset.getBlockStatus(roi[0]) == BlockwiseFileset.BLOCK_AVAILABLE \
                or blockwiseFileset.isBlockLocked(roi[0]): # We don't attempt to process currently locked blocks.
                    unneeded_rois.append( roi )
    
            # Remove any tasks that we don't need to compute (they were finished in a previous run)
            for roi in unneeded_rois:
                logger.info( "No need to run task: {} for roi: {}".format( taskInfos[roi].taskName, roi ) )
                del taskInfos[roi]

            absWorkDir, _ = getPathVariants(self._config.server_working_directory, os.path.split( configFilePath )[0] )
            if self._config.task_launch_server == "localhost":
                def localCommand( cmd ):
                    cwd = os.getcwd()
                    os.chdir( absWorkDir )
                    subprocess.call( cmd, shell=True )
                    os.chdir( cwd )
                launchFunc = localCommand
            else:
                # We use fabric for executing remote tasks
                # Import it here because it isn't required that the nodes can use it.
                import fabric.api as fab
                @fab.hosts( self._config.task_launch_server )
                def remoteCommand( cmd ):
                    with fab.cd( absWorkDir ):
                        fab.run( cmd )
                launchFunc = functools.partial( fab.execute, remoteCommand )
    
            # Spawn each task
            for taskInfo in taskInfos.values():
                logger.info("Launching node task: " + taskInfo.command )
                launchFunc( taskInfo.command )
        
            # Return immediately.  We do not attempt to monitor the task progress.
            result[0] = True
            return result
        finally:
            blockwiseFileset.close()

    def _prepareTaskInfos(self, roiList):
        # Divide up the workload into large pieces
        logger.info( "Dividing into {} node jobs.".format( len(roiList) ) )

        taskInfos = collections.OrderedDict()
        for roiIndex, roi in enumerate(roiList):
            roi = ( tuple(roi[0]), tuple(roi[1]) )
            taskInfo = OpClusterize.TaskInfo()
            taskInfo.subregion = SubRegion( None, start=roi[0], stop=roi[1] )
            
            taskName = "J{:02}".format(roiIndex)

            commandArgs = []
            commandArgs.append( "--option_config_file=" + self.ConfigFilePath.value )
            commandArgs.append( "--project=" + self.ProjectFilePath.value )
            commandArgs.append( "--_node_work_=\"" + Roi.dumps( taskInfo.subregion ) + "\"" )
            commandArgs.append( "--process_name={}".format(taskName)  )
            commandArgs.append( "--output_description_file={}".format( self.OutputDatasetDescription.value )  )

            # Check the command format string: We need to know where to put our args...
            commandFormat = self._config.command_format
            assert commandFormat.find("{task_args}") != -1

            # Output log directory might be a relative path (relative to config file)
            absLogDir, _ = getPathVariants(self._config.output_log_directory, os.path.split( self.ConfigFilePath.value )[0] )
            if not os.path.exists(absLogDir):
                os.makedirs(absLogDir)
            taskOutputLogFilename = taskName + ".log"
            taskOutputLogPath = os.path.join( absLogDir, taskOutputLogFilename )
            
            allArgs = " " + " ".join(commandArgs) + " "
            taskInfo.taskName = taskName
            taskInfo.command = commandFormat.format( task_args=allArgs, task_name=taskName, task_output_file=taskOutputLogPath )
            taskInfos[roi] = taskInfo

        return taskInfos

    def _prepareDestination(self):
        """
        - If the result file doesn't exist yet, create it (and the dataset)
        - If the result file already exists, return a list of the rois that 
        are NOT needed (their data already exists in the final output)
        """
        originalDescription = BlockwiseFileset.readDescription(self.OutputDatasetDescription.value)
        datasetDescription = copy.deepcopy(originalDescription)

        # Modify description fields as needed
        # -- axes
        datasetDescription.axes = "".join( self.Input.meta.getTaggedShape().keys() )
        assert set(originalDescription.axes) == set( datasetDescription.axes ), \
            "Can't prepare destination dataset: original dataset description listed " \
            "axes as {}, but actual output axes are {}".format( originalDescription.axes, datasetDescription.axes )

        # -- shape
        datasetDescription.view_shape = list(self.Input.meta.shape)
        # -- block_shape
        assert originalDescription.block_shape is not None
        originalBlockDims = collections.OrderedDict( zip( originalDescription.axes, originalDescription.block_shape ) )
        datasetDescription.block_shape = map( lambda a: originalBlockDims[a], datasetDescription.axes )
        datasetDescription.block_shape = map( min, zip( datasetDescription.block_shape, self.Input.meta.shape ) )
        # -- chunks
        if originalDescription.chunks is not None:
            originalChunkDims = collections.OrderedDict( zip( originalDescription.axes, originalDescription.chunks ) )
            datasetDescription.chunks = map( lambda a: originalChunkDims[a], datasetDescription.axes )
            datasetDescription.chunks = map( min, zip( datasetDescription.chunks, self.Input.meta.shape ) )
        # -- dtype
        if datasetDescription.dtype != self.Input.meta.dtype:
            dtype = self.Input.meta.dtype
            if type(dtype) is numpy.dtype:
                dtype = dtype.type
            datasetDescription.dtype = dtype().__class__.__name__

        # Create a unique hash for this blocking scheme.
        # If it changes, we can't use any previous data.
        sha = hashlib.sha1()
        sha.update( str( tuple( datasetDescription.block_shape) ) )
        sha.update( datasetDescription.axes )
        sha.update( datasetDescription.block_file_name_format )

        datasetDescription.hash_id = sha.hexdigest()

        if datasetDescription != originalDescription:
            descriptionFilePath = self.OutputDatasetDescription.value
            logger.info( "Overwriting dataset description: {}".format( descriptionFilePath ) )
            BlockwiseFileset.writeDescription(descriptionFilePath, datasetDescription)
            with open( descriptionFilePath, 'r' ) as f:
                logger.info( f.read() )

        # Now open the dataset
        blockwiseFileset = BlockwiseFileset( self.OutputDatasetDescription.value )
        
        taskInfos = self._prepareTaskInfos( blockwiseFileset.getAllBlockRois() )
        
        if blockwiseFileset.description.hash_id != originalDescription.hash_id:
            # Something about our blocking scheme changed.
            # Make sure all blocks are marked as NOT available.
            # (Just in case some were left over from a previous run.)
            for roi in taskInfos.keys():
                blockwiseFileset.setBlockStatus( roi[0], BlockwiseFileset.BLOCK_NOT_AVAILABLE )

        return blockwiseFileset, taskInfos

    def _determineCompletedBlocks(self, blockwiseFileset, taskInfos):
        finished_rois = []
        for roi in taskInfos.keys():
            if blockwiseFileset.getBlockStatus(roi[0]) == BlockwiseFileset.BLOCK_AVAILABLE:
                finished_rois.append( roi )
        return finished_rois

    def propagateDirty(self, slot, subindex, roi):
        self.ReturnCode.setDirty( slice(None) )


    def _getDtypeBytes(self):
        """
        Return the size of the dataset dtype in bytes.
        """
        dtype = self.Input.meta.dtype
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type
        
        return dtype().nbytes




























