import os
import math
import numpy
import subprocess
from lazyflow.rtype import Roi, SubRegion
from lazyflow.graph import Operator, InputSlot, OutputSlot, OrderedSignal
import itertools
import h5py
import time
import threading
import collections
from functools import partial
import tempfile
import shutil
import hashlib
import datetime
from ilastik.clusterConfig import parseClusterConfigFile

from lazyflow.operators import OpH5WriterBigDataset, OpSubRegion

import logging
logger = logging.getLogger(__name__)

class Timer(object):
    def __init__(self):
        self.startTime = None
        self.stopTime = None
    
    def __enter__(self):
        self.startTime = datetime.datetime.now()
        return self
    
    def __exit__(self, *args):
        self.stopTime = datetime.datetime.now()
    
    def seconds(self):
        assert self.startTime is not None, "Timer hasn't started yet!"
        if self.stopTime is None:
            return (datetime.datetime.now() - self.startTime).seconds
        else:
            return (self.stopTime - self.startTime).seconds

STATUS_FILE_NAME_FORMAT = "{} status {}.txt"
OUTPUT_FILE_NAME_FORMAT = "{} output {}.h5"

class OpTaskWorker(Operator):
    Input = InputSlot()
    RoiString = InputSlot(stype='string')
    TaskName = InputSlot(stype='string')
    ConfigFilePath = InputSlot(stype='filestring')
    
    ReturnCode = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpTaskWorker, self ).__init__( *args, **kwargs )
        self.progressSignal = OrderedSignal()

    def setupOutputs(self):
        self.ReturnCode.meta.dtype = bool
        self.ReturnCode.meta.shape = (1,)
    
    def execute(self, slot, subindex, roi, result):
        configFilePath = self.ConfigFilePath.value
        config = parseClusterConfigFile( configFilePath )
        
        roiString = self.RoiString.value
        roi = Roi.loads(roiString)
        logger.info( "Executing for roi: {}".format(roi) )
        roituple = ( tuple(roi.start), tuple(roi.stop) )
        statusFileName = STATUS_FILE_NAME_FORMAT.format( self.TaskName.value, str(roituple) )
        outputFileName = OUTPUT_FILE_NAME_FORMAT.format( self.TaskName.value, str(roituple) )

        statusFilePath = os.path.join( config.scratch_directory, statusFileName )
        outputFilePath = os.path.join( config.scratch_directory, outputFileName )

        # By default, write directly to the final output
        scratchOutputPath = outputFilePath
        
        if config.use_node_local_scratch:
            # Create a temporary file to generate the output
            # (Temp directory on a local disk may provide faster access)
            tempDir = tempfile.mkdtemp()
            tmpOutputFilePath = os.path.join(tempDir, roiString + ".h5")
            logger.info("Constructing output in temporary file: {}".format( tmpOutputFilePath ))
            scratchOutputPath = tmpOutputFilePath
        
        # Create the output file in our local scratch area.
        with h5py.File( scratchOutputPath, 'w' ) as outputFile:
            assert self.Input.ready()
    
            # Extract sub-region
            opSubRegion = OpSubRegion(parent=self, graph=self.graph)
            opSubRegion.Input.connect( self.Input )
            opSubRegion.Start.setValue( tuple(roi.start) )
            opSubRegion.Stop.setValue( tuple(roi.stop) )
    
            assert opSubRegion.Output.ready()
    
            # Set up the write operator
            opH5Writer = OpH5WriterBigDataset(parent=self, graph=self.graph)
            opH5Writer.hdf5File.setValue( outputFile )
            opH5Writer.hdf5Path.setValue( 'node_result' )
            opH5Writer.Image.connect( opSubRegion.Output )

            assert opH5Writer.WriteImage.ready()

            # Forward progress from the writer to our own progress signal
            opH5Writer.progressSignal.subscribe( self.progressSignal )

            with Timer() as computeTimer:
                result[0] = opH5Writer.WriteImage.value
                logger.info( "Finished task in {} seconds".format( computeTimer.seconds() ) )
        
        if config.use_node_local_scratch:
            # Copy the temp file to the scratch area to be picked up by the master process
            with Timer() as copyTimer:
                logger.info( "Copying {} to {}...".format(tmpOutputFilePath, outputFilePath) )
                shutil.copyfile(tmpOutputFilePath, outputFilePath)
                logger.info( "Finished copying after {} seconds".format( copyTimer.seconds() ) )
                # Delete the tempfile
                os.remove( tmpOutputFilePath )

        # Now create the status file to show that we're finished.
        statusFile = file(statusFilePath, 'w')
        statusFile.write('Yay!')

        return result

    def propagateDirty(self, slot, subindex, roi):
        self.ReturnCode.setDirty( slice(None) )

class OpClusterize(Operator):
    Input = InputSlot()
    OutputFilePath = InputSlot()
    ProjectFilePath = InputSlot(stype='filestring')
    ConfigFilePath = InputSlot(stype='filestring')
    
    ReturnCode = OutputSlot()

    # Constants
    FINAL_DATASET_NAME = 'cluster_result'

    class TaskInfo():
        taskName = None
        command = None
        statusFilePath = None
        outputFilePath = None
        subregion = None
        
    def setupOutputs(self):
        self.ReturnCode.meta.dtype = bool
        self.ReturnCode.meta.shape = (1,)
    
    def execute(self, slot, subindex, roi, result):
        # We use fabric for executing remote tasks
        import fabric.api as fab

        success = True
        
        configFilePath = self.ConfigFilePath.value
        self._config = parseClusterConfigFile( configFilePath )

        taskInfos = self._prepareTaskInfos()

        @fab.hosts( self._config.task_launch_server )
        def remoteCommand( cmd ):
            with fab.cd( self._config.server_working_directory ):
                fab.run( cmd )

        # Spawn each task
        for taskInfo in taskInfos.values():
            logger.info("Launching node task: " + taskInfo.command )
            fab.execute( remoteCommand, taskInfo.command )            

        # Create the destination file if necessary
        unneeded_rois = self._prepareDestination( taskInfos )
        
        # Remove any tasks that we don't need to compute (they were finished in a previous run)
        for roi in unneeded_rois:
            logger.info( "No need to run task: {} for roi: {}".format( taskInfos[roi].taskName, roi ) )
            del taskInfos[roi]

        timeOut = self._config.task_timeout_secs
        with Timer() as totalTimer:
            # When each task completes, it creates a status file.
            while len(taskInfos) > 0:
                # TODO: Maybe replace this naive polling system with an asynchronous 
                #         file status via select.epoll or something like that.
                if totalTimer.seconds() >= timeOut:
                    logger.error("Timing out after {} seconds, even though {} tasks haven't finished yet.".format( totalTimer.seconds(), len(taskInfos) ) )
                    success = False
                    break
                time.sleep(15.0)
    
                logger.debug("Time: {} seconds. Checking {} remaining tasks....".format(totalTimer.seconds(), len(taskInfos)))
    
                # Figure out which results have finished already and copy their results into the final output file
                finished_rois = self._copyFinishedResults( taskInfos )
    
                # Remove the finished tasks from the list we're polling for
                for roi in finished_rois:
                    del taskInfos[roi]
                
                # Handle failured tasks
                failed_rois = self._checkForFailures( taskInfos )
                if len(failed_rois) > 0:
                    success = False
    
                # Remove the failed tasks from the list we're polling for
                for roi in failed_rois:
                    logger.error( "Giving up on failed task: {} for roi: {}".format( taskInfos[roi].taskName, roi ) )
                    del taskInfos[roi]

        if success:
            logger.info( "SUCCESS after {} seconds.".format( totalTimer.seconds() ) )
        else:
            logger.info( "FAILED after {} seconds.".format( totalTimer.seconds() ) )

        result[0] = success
        return result
    
    def _getRoiList(self):
        inputShape = self.Input.meta.shape
        # Use a dumb means of computing task shapes for now.
        # Find the dimension of the data in xyz, and block it up that way.
        taggedShape = self.Input.meta.getTaggedShape()

        spaceDims = filter( lambda (key, dim): key in 'xyz' and dim > 1, taggedShape.items() ) 
        numJobs = self._config.num_jobs
        numJobsPerSpaceDim = math.pow(numJobs, 1.0/len(spaceDims))
        numJobsPerSpaceDim = int(round(numJobsPerSpaceDim))

        roiShape = []
        for key, dim in taggedShape.items():
            if key in [key for key, value in spaceDims]:
                roiShape.append(dim / numJobsPerSpaceDim)
            else:
                roiShape.append(dim)

        roiShape = numpy.array(roiShape)
        
        rois = []
        for indices in itertools.product( *[ range(0, stop, step) for stop,step in zip(inputShape, roiShape) ] ):
            start=numpy.asarray(indices)
            stop=numpy.minimum( start+roiShape, inputShape )
            rois.append( (start, stop) )

        return rois

    def _prepareTaskInfos(self):
        # Divide up the workload into large pieces
        rois = self._getRoiList()
        logger.info( "Dividing into {} node jobs.".format( len(rois) ) )
                
        taskInfos = collections.OrderedDict()
        for roiIndex, roi in enumerate(rois):
            roi = ( tuple(roi[0]), tuple(roi[1]) )
            taskInfo = OpClusterize.TaskInfo()
            taskInfo.subregion = SubRegion( None, start=roi[0], stop=roi[1] )
            
            taskName = "JOB{:02}".format(roiIndex)
            statusFileName = STATUS_FILE_NAME_FORMAT.format( taskName, str(roi) )
            outputFileName = OUTPUT_FILE_NAME_FORMAT.format( taskName, str(roi) )

            statusFilePath = os.path.join( self._config.scratch_directory, statusFileName )
            outputFilePath = os.path.join( self._config.scratch_directory, outputFileName )

            commandArgs = []
            commandArgs.append( "--option_config_file=" + self.ConfigFilePath.value )
            commandArgs.append( "--project=" + self.ProjectFilePath.value )
            commandArgs.append( "--_node_work_=\"" + Roi.dumps( taskInfo.subregion ) + "\"" )
            commandArgs.append( "--process_name={}".format(taskName)  )

            # Check the command format string: We need to know where to put our args...
            commandFormat = self._config.command_format
            assert commandFormat.find("{task_args}") != -1
            
            allArgs = " " + " ".join(commandArgs) + " "
            taskInfo.taskName = taskName
            taskInfo.command = commandFormat.format( task_args=allArgs, task_name=taskName )
            taskInfo.statusFilePath = statusFilePath
            taskInfo.outputFilePath = outputFilePath
            taskInfos[roi] = taskInfo

            # If files are still hanging around from the last run, delete them.
            if os.path.exists( statusFilePath ):
                os.remove( statusFilePath )
            if os.path.exists( outputFilePath ):
                os.remove( outputFilePath )

        return taskInfos

    def _prepareDestination(self, taskInfos):
        """
        - If the result file doesn't exist yet, create it (and the dataset)
        - If the result file already exists, return a list of the rois that 
        are NOT needed (their data already exists in the final output)
        """
        allRoiStrings = map( lambda taskInfo: Roi.dumps( taskInfo.subregion ), taskInfos.values() )
        allRoiStrings = sorted( allRoiStrings )
        # Create a unique hash for this roi scheme.
        # If it changes, we can't use any previous data.
        sha = hashlib.sha1()
        for roiString in allRoiStrings:
            sha.update(roiString)
        roiSchemeHash = sha.hexdigest()
        
        alreadyFinishedRois = []
        with h5py.File( self.OutputFilePath.value ) as destinationFile:
            if OpClusterize.FINAL_DATASET_NAME not in destinationFile.keys():
                dtypeBytes = self._getDtypeBytes()
    
                taggedShape = self.Input.meta.getTaggedShape()
                numChannels = taggedShape['c']
                cubeDim = math.pow( 300000 / (numChannels * dtypeBytes), (1/3.0) )
                cubeDim = int(cubeDim)
        
                chunkDims = {}
                chunkDims['t'] = 1
                chunkDims['x'] = cubeDim
                chunkDims['y'] = cubeDim
                chunkDims['z'] = cubeDim
                chunkDims['c'] = numChannels
                
                # h5py guide to chunking says chunks of 300k or less "work best"
                assert chunkDims['x'] * chunkDims['y'] * chunkDims['z'] * numChannels * dtypeBytes  <= 300000
        
                chunkShape = map( lambda (key, dim): min(chunkDims[key], dim),
                                  taggedShape.items() )
                chunkShape = tuple(chunkShape)
        
                resultDataset = destinationFile.create_dataset(OpClusterize.FINAL_DATASET_NAME,
                                                               shape=self.Input.meta.shape,
                                                               dtype=self.Input.meta.dtype,
                                                               chunks=chunkShape)

                resultDataset.attrs['missingRois'] = allRoiStrings
                resultDataset.attrs['roiSchemeHash'] = roiSchemeHash
            else:
                # The dataset already exists, so find out which tasks we don't need to run.
                resultDataset = destinationFile[OpClusterize.FINAL_DATASET_NAME]

                assert 'missingRois' in resultDataset.attrs, "Existing output dataset doesn't have expected attribute 'missingRois'."
                assert 'roiSchemeHash' in resultDataset.attrs, "Existing output dataset doesn't have expected attribute 'roiSchemeHash'."
                assert resultDataset.shape == self.Input.meta.shape, "Existing output dataset has wrong shape.  Are you re-using an output file for a new dataset?"
                assert resultDataset.dtype == self.Input.meta.dtype, "Existing output dataset has wrong dtype.  Are you re-using an output file for a new dataset?"

                # It looks like we already started working on this dataset in a previous run.
                # If we used the same roi break-down as before, we can continue where we left off.
                previousRoiSchemeHash = resultDataset.attrs['roiSchemeHash']

                if previousRoiSchemeHash != roiSchemeHash:
                    resultDataset.attrs['missingRois'] = allRoiStrings
                    resultDataset.attrs['roiSchemeHash'] = roiSchemeHash
                else:
                    missingRois = set( resultDataset.attrs['missingRois'] )
                    for roi, taskInfo in taskInfos.items():
                        if Roi.dumps( taskInfo.subregion ) not in missingRois:
                            alreadyFinishedRois.append( roi )
                
            return alreadyFinishedRois

    def _copyFinishedResults(self, taskInfos):
        """
        For each of the taskInfos provided:
        - Check to see if we have a status file for that task
        - If so, copy the the data from the task output file into the final output file
        - Remove the task from final dataset's list of 'missing rois'
        
        Return the list of rois that we processed.
        """
        finished_rois = []
        destinationFile = None
        resultDataset = None
        missingRois = None
        for roi, taskInfo in taskInfos.items():
            # Has the task completed yet?
            #logger.debug( "Checking for file: {}".format( taskInfo.statusFilePath ) )
            if not os.path.exists( taskInfo.statusFilePath ):
                continue

            logger.info( "Found status file: {}".format( taskInfo.statusFilePath ) )
            if not os.path.exists( taskInfo.outputFilePath ):
                raise RuntimeError( "Error: Could not locate output file from spawned task: " + taskInfo.outputFilePath )

            # Open the destination file if necessary
            if destinationFile is None:
                destinationFile = h5py.File( self.OutputFilePath.value )
                resultDataset = destinationFile[OpClusterize.FINAL_DATASET_NAME]
                assert 'missingRois' in resultDataset.attrs
                missingRois = set( resultDataset.attrs['missingRois'] )

            roiString = Roi.dumps( taskInfo.subregion )
            assert roiString in missingRois, "This task didn't need to be executed: it wasn't missing from the result!"
            with Timer() as fileCopyTimer:
                # Copy the scratch file to local scratch area before we open it with h5py
                tempDir = tempfile.mkdtemp()
                roiString = Roi.dumps( taskInfo.subregion )
                tmpOutputFilePath = os.path.join(tempDir, roiString + ".h5")

                logger.info( "Copying {} to {}...".format(taskInfo.outputFilePath, tmpOutputFilePath) )
                shutil.copyfile(taskInfo.outputFilePath, tmpOutputFilePath)
                logger.info( "Finished copying after {} seconds".format( fileCopyTimer.seconds() ) )

            # Open the file
            with h5py.File( tmpOutputFilePath, 'r' ) as f:
                # Check the result
                assert 'node_result' in f.keys()
                assert numpy.all(f['node_result'].shape == numpy.subtract(roi[1], roi[0]))
                assert f['node_result'].dtype == self.Input.meta.dtype
                assert f['node_result'].attrs['axistags'] == self.Input.meta.axistags.toJSON()
    
                shape = f['node_result'][:].shape

                dtypeBytes = self._getDtypeBytes()
                
                # Copy the data into our result (which might be an h5py dataset...)
                key = taskInfo.subregion.toSlice()
    
                with Timer() as copyTimer:
                    resultDataset[key] = f['node_result'][:]
    
                totalBytes = dtypeBytes * numpy.prod(shape)
                totalMB = totalBytes / (1000*1000)
    
                logger.info( "Copying {} MB hdf5 slice took {} seconds".format(totalMB, copyTimer.seconds() ) )
                finished_rois.append(roi)

                # Remove the roi from the list of remaining rois
                roiString = Roi.dumps(taskInfo.subregion)
                missingRois.remove( roiString )

            os.remove(tmpOutputFilePath)

        # For now, we close the file after every pass in case something goes horribly wrong...
        if destinationFile is not None:
            # Update the list of rois that are still missing from the output file.
            resultDataset.attrs['missingRois'] = list(missingRois)
            destinationFile.close()
            destinationFile = None

        return finished_rois

    def _checkForFailures(self, taskInfos):
        return []

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




























