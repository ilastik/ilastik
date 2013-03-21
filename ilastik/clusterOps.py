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

from ilastik.clusterConfig import parseClusterConfigFile
from ilastik.utility.timer import Timer
from ilastik.utility.pathHelpers import getPathVariants

import logging
logger = logging.getLogger(__name__)

class OpTaskWorker(Operator):
    Input = InputSlot()
    RoiString = InputSlot(stype='string')
    TaskName = InputSlot(stype='string')
    ConfigFilePath = InputSlot(stype='filestring')
    OutputFilesetDescription = InputSlot(stype='filestring')

    SecondaryInputs = InputSlot(level=1, optional=True)
    SecondaryOutputDescriptions = InputSlot(level=1, optional=True)
    
    ReturnCode = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpTaskWorker, self ).__init__( *args, **kwargs )
        self.progressSignal = OrderedSignal()
        self._primaryBlockwiseFileset = None
        self._secondaryBlockwiseFilesets = []

    def setupOutputs(self):
        self.ReturnCode.meta.dtype = bool
        self.ReturnCode.meta.shape = (1,)
        
        self._closeFiles()
        self._primaryBlockwiseFileset = BlockwiseFileset( self.OutputFilesetDescription.value, 'a' )        
        self._secondaryBlockwiseFilesets = []
        for slot in self.SecondaryOutputDescriptions:
            descriptionPath = slot.value
            self._secondaryBlockwiseFilesets.append( BlockwiseFileset( descriptionPath, 'a' ) )
    
    def cleanUp(self):
        self._closeFiles()
        super( OpTaskWorker, self ).cleanUp()

    def _closeFiles(self):
        if self._primaryBlockwiseFileset is not None:
            self._primaryBlockwiseFileset.close()
        for fileset in self._secondaryBlockwiseFilesets:
            fileset.close()
        self._primaryBlockwiseFileset = None
        self._secondaryBlockwiseFilesets = []

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

        # Convert the task subrequest shape dict into a shape for this dataset (and axisordering)
        subrequest_shape = map( lambda tag: config.task_subrequest_shape[tag.key], self.Input.meta.axistags )
        primary_subrequest_shape = self._primaryBlockwiseFileset.description.sub_block_shape
        if primary_subrequest_shape is not None:
            # If the output dataset specified a sub_block_shape, override the cluster config
            subrequest_shape = primary_subrequest_shape

        with Timer() as computeTimer:
            # Stream the data out to disk.
            streamer = BigRequestStreamer(self.Input, (roi.start, roi.stop), subrequest_shape, config.task_parallel_subrequests )
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

        # Get this block's index with respect to the primary dataset
        sub_block_index = roi[0] / self._primaryBlockwiseFileset.description.sub_block_shape
        
        # Now request the secondaries
        for slot, fileset in zip(self.SecondaryInputs, self._secondaryBlockwiseFilesets):
            # Compute the corresponding sub_block in this output dataset
            sub_block_shape = fileset.description.sub_block_shape
            sub_block_start = sub_block_index * sub_block_shape
            sub_block_stop = sub_block_start + sub_block_shape
            sub_block_stop = numpy.minimum( sub_block_stop, fileset.description.shape )
            sub_block_roi = (sub_block_start, sub_block_stop)
            
            secondary_result = slot( *sub_block_roi ).wait()
            fileset.writeData( sub_block_roi, secondary_result )

class OpClusterize(Operator):
    Input = InputSlot()
    OutputDatasetDescription = InputSlot()
    ProjectFilePath = InputSlot(stype='filestring')
    ConfigFilePath = InputSlot(stype='filestring')

    SecondaryInputs = InputSlot(level=1, optional=True)
    SecondaryOutputDescriptions = InputSlot(level=1, optional=True)
    
    ReturnCode = OutputSlot()

    class TaskInfo():
        taskName = None
        command = None
        subregion = None
        
    def setupOutputs(self):
        self.ReturnCode.meta.dtype = bool
        self.ReturnCode.meta.shape = (1,)

        # Check for errors
        primaryOutputDescription = BlockwiseFileset.readDescription(self.OutputDatasetDescription.value)
        primary_block_shape = primaryOutputDescription.block_shape
        primary_sub_block_shape = primaryOutputDescription.sub_block_shape
        assert primary_sub_block_shape is not None, "Primary output description file must specify a sub_block_shape"

        # Ratio of blocks to sub-blocks for all secondaries must match the primary.
        primary_sub_block_factor = (primary_block_shape + primary_sub_block_shape - 1) / primary_sub_block_shape
        
        for i, slot in enumerate( self.SecondaryOutputDescriptions ):
            descriptionPath = slot.value
            secondaryDescription = BlockwiseFileset.readDescription(descriptionPath)
            block_shape = secondaryDescription.block_shape
            sub_block_shape = secondaryDescription.sub_block_shape
            assert sub_block_shape is not None, "Secondary output description #{} doesn't specify a sub_block_shape".format( i )
            
            sub_block_factor = (block_shape + sub_block_shape - 1) / sub_block_shape
            if (tuple(primary_sub_block_factor) != tuple(sub_block_factor)):
                msg = "Error: Ratio of sub_block_shape to block_shape must be the same in the primary output dataset and in all secondary datasets.\n"
                msg += "Secondary dataset {} has a factor of {}, which doesn't match primary factor of {}".format( i, sub_block_factor, primary_sub_block_factor )
                raise RuntimeError(msg)
    
    def _validateConfig(self):
        if not self._config.use_master_local_scratch:
            assert self._config.node_output_compression_cmd is None, "Can't use node dataset compression unless master local scratch is also used."
    
    def execute(self, slot, subindex, roi, result):
        dtypeBytes = self._getDtypeBytes()
        totalBytes = dtypeBytes * numpy.prod(self.Input.meta.shape)
        totalMB = totalBytes / (1000*1000)
        logger.info( "Clusterizing computation of {} MB dataset, outputting according to {}".format(totalMB, self.OutputDatasetDescription.value) )

        configFilePath = self.ConfigFilePath.value
        self._config = parseClusterConfigFile( configFilePath )

        self._validateConfig()

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

            absWorkDir, relWorkDir = getPathVariants(self._config.server_working_directory, os.path.split( configFilePath )[0] )
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
            for slot in self.SecondaryOutputDescriptions:
                commandArgs.append( "--secondary_output_description_file={}".format( slot.value )  )

            # Check the command format string: We need to know where to put our args...
            commandFormat = self._config.command_format
            assert commandFormat.find("{task_args}") != -1

            # Output log directory might be a relative path (relative to config file)
            absLogDir, relLogDir = getPathVariants(self._config.output_log_directory, os.path.split( self.ConfigFilePath.value )[0] )
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




























