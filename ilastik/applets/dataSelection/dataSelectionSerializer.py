from __future__ import absolute_import

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
from typing import List, Tuple, Callable
from pathlib import Path

from .opDataSelection import OpDataSelection, DatasetInfo
from lazyflow.operators.ioOperators import OpInputDataReader, OpStackLoader, OpH5N5WriterBigDataset
from lazyflow.operators.ioOperators.opTiffReader import OpTiffReader
from lazyflow.operators.ioOperators.opTiffSequenceReader import OpTiffSequenceReader
from lazyflow.operators.ioOperators.opStreamingH5N5SequenceReaderM import (
    OpStreamingH5N5SequenceReaderM
)
from lazyflow.operators.ioOperators.opStreamingH5N5SequenceReaderS import (
    OpStreamingH5N5SequenceReaderS
)
from lazyflow.graph import Graph

import os
import vigra
import numpy
from lazyflow.utility import PathComponents
from lazyflow.utility.timer import timeLogged
from ilastik.utility import bind
from lazyflow.utility.pathHelpers import getPathVariants, isUrl, isRelative, splitPath
import ilastik.utility.globals

from ilastik.applets.base.appletSerializer import \
    AppletSerializer, getOrCreateGroup, deleteIfPresent

import logging
logger = logging.getLogger(__name__)

class DataSelectionSerializer( AppletSerializer ):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    
    The model operator for this serializer is the ``OpMultiLaneDataSelectionGroup``
    """
    # Constants    
    LocationStrings = { None      : u'FileSystem',
                        DatasetInfo.Location.FileSystemRelativePath : u'RelativePath',
                        DatasetInfo.Location.FileSystemAbsolutePath : u'AbsolutePath',
                        DatasetInfo.Location.ProjectInternal : u'ProjectInternal' }

    def __init__(self, topLevelOperator, projectFileGroupName):
        super( DataSelectionSerializer, self ).__init__(projectFileGroupName)
        self.topLevelOperator = topLevelOperator
        self._dirty = False

        self._projectFilePath = None
        
        self.version = '0.2'
        
        def handleDirty():
            if not self.ignoreDirty:
                self._dirty = True

        self.topLevelOperator.ProjectFile.notifyDirty( bind(handleDirty) )
        self.topLevelOperator.ProjectDataGroup.notifyDirty( bind(handleDirty) )
        self.topLevelOperator.WorkingDirectory.notifyDirty( bind(handleDirty) )
        
        def handleNewDataset(slot, roleIndex):
            slot[roleIndex].notifyDirty( bind(handleDirty) )
            slot[roleIndex].notifyDisconnect( bind(handleDirty) )
        def handleNewLane(multislot, laneIndex):
            assert multislot == self.topLevelOperator.DatasetGroup
            multislot[laneIndex].notifyInserted( bind(handleNewDataset) )
            for roleIndex in range( len(multislot[laneIndex]) ):
                handleNewDataset(multislot[laneIndex], roleIndex)
        self.topLevelOperator.DatasetGroup.notifyInserted( bind(handleNewLane) )

        # If a dataset was removed, we need to be reserialized.
        self.topLevelOperator.DatasetGroup.notifyRemoved( bind(handleDirty) )
        
    @timeLogged(logger, logging.DEBUG)
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        # Write any missing local datasets to the local_data group
        localDataGroup = getOrCreateGroup(topGroup, 'local_data')
        wroteInternalData = False

        # Construct a list of all the local dataset ids we want to keep
        localDatasetIds = set()
        for laneIndex, multislot in enumerate(self.topLevelOperator.DatasetGroup):
            for roleIndex, slot in enumerate(multislot):
                if slot.ready() and slot.value.location == DatasetInfo.Location.ProjectInternal:
                    localDatasetIds.add( slot.value.datasetId )
        
        # Delete any datasets in the project that aren't needed any more
        #FIXME": move this logic somewhere close to datasetinfoEditorWdiget or data selection gui
        for datasetName in list(localDataGroup.keys()):
            if datasetName not in localDatasetIds:
                del localDataGroup[datasetName]

        if wroteInternalData:
            # We can only re-configure the operator if we're not saving a snapshot
            # We know we're saving a snapshot if the project file isn't the one we deserialized with.
            if self._projectFilePath is None or self._projectFilePath == projectFilePath:
                # Force the operator to setupOutputs() again so it gets data from the project, not external files
                firstInfo = self.topLevelOperator.DatasetGroup[0][0].value
                self.topLevelOperator.DatasetGroup[0][0].setValue(firstInfo, check_changed=False)

        deleteIfPresent(topGroup, 'Role Names')
        role_names = [name.encode('utf-8') for name in self.topLevelOperator.DatasetRoles.value]
        topGroup.create_dataset('Role Names', data=role_names)

        # Access the info group
        infoDir = getOrCreateGroup(topGroup, 'infos')
        
        # Delete all infos
        for infoName in list(infoDir.keys()):
            del infoDir[infoName]
                
        # Rebuild the list of infos
        roleNames = self.topLevelOperator.DatasetRoles.value
        for laneIndex, multislot in enumerate(self.topLevelOperator.DatasetGroup):
            laneGroupName = 'lane{:04d}'.format(laneIndex)
            laneGroup = infoDir.create_group( laneGroupName )
            
            for roleIndex, slot in enumerate(multislot):
                infoGroup = laneGroup.create_group( roleNames[roleIndex] )
                if slot.ready():
                    datasetInfo = slot.value
                    locationString = self.LocationStrings[datasetInfo.location]
                    infoGroup.create_dataset('location', data=locationString.encode('utf-8'))
                    infoGroup.create_dataset('filePath', data=datasetInfo.filePath.encode('utf-8'))
                    infoGroup.create_dataset('allowLabels', data=datasetInfo.allowLabels)
                    infoGroup.create_dataset('nickname', data=datasetInfo.nickname.encode('utf-8'))
                    infoGroup.create_dataset('display_mode', data=datasetInfo.display_mode.encode('utf-8'))
                    if datasetInfo.drange is not None:
                        infoGroup.create_dataset('drange', data=datasetInfo.drange)

                    # FIXME: grab all of this stuff straight out of datasetinfo
                    # Pull the axistags from the NonTransposedImage, 
                    #  which is what the image looks like before 'forceAxisOrder' is applied, 
                    #  and before 'c' is automatically appended
                    image_group_meta = self.topLevelOperator._NonTransposedImageGroup[laneIndex][roleIndex].meta
                    axistags = image_group_meta.axistags
                    infoGroup.create_dataset('axistags', data=axistags.toJSON().encode('utf-8'))
                    axisorder = "".join(tag.key for tag in axistags).encode('utf-8')
                    infoGroup.create_dataset('axisorder', data=axisorder)
                    # serialize shape/dtype so that we could re-create the metadata
                    # for the raw data in the headless mode -> no need for raw data in headless
                    infoGroup.create_dataset('shape', data=image_group_meta.shape)
                    infoGroup.create_dataset('dtype', data=str(numpy.dtype(image_group_meta.dtype)).encode('utf-8'))
                    if datasetInfo.subvolume_roi is not None:
                        infoGroup.create_dataset('subvolume_roi', data=datasetInfo.subvolume_roi)

        self._dirty = False

    def importStackAsLocalDataset(
        self,
        abs_paths:List[str],
        sequence_axis:str='z',
        progress_signal:Callable[[int], None]=lambda x: None
    ):
        progress_signal(0)
        try:
            colon_paths = os.path.pathsep.join(abs_paths)
            op_reader = OpInputDataReader(graph=Graph(),
                                          FilePath=colon_paths,
                                          SequenceAxis=sequence_axis)
            axistags = op_reader.Output.meta.axistags
            inner_path = (Path(self.topGroupName) / 'local_data' / DatasetInfo.generate_id()).as_posix()
            project_file = self.topLevelOperator.ProjectFile.value
            opWriter = OpH5N5WriterBigDataset(graph=Graph(),
                                              h5N5File=project_file,
                                              h5N5Path=inner_path,
                                              CompressionEnabled=False,
                                              BatchSize=1,
                                              Image=op_reader.Output)
            opWriter.progressSignal.subscribe(progress_signal)
            success = opWriter.WriteImage.value
            for index, tag in enumerate(axistags):
                project_file[inner_path].dims[index].label = tag.key
            project_file[inner_path].attrs['axistags'] = axistags.toJSON()
            return inner_path
        finally:
            progress_signal(100)


    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        """
        Overridden from AppletSerializer.initWithoutTopGroup
        """
        # The 'working directory' for the purpose of constructing absolute 
        #  paths from relative paths is the project file's directory.
        projectDir = os.path.split(projectFilePath)[0]
        self.topLevelOperator.WorkingDirectory.setValue( projectDir )
        self.topLevelOperator.ProjectDataGroup.setValue( self.topGroupName + '/local_data' )
        self.topLevelOperator.ProjectFile.setValue( hdf5File )
        
        self._dirty = False

    @timeLogged(logger, logging.DEBUG)
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless):
        self._projectFilePath = projectFilePath
        self.initWithoutTopGroup(hdf5File, projectFilePath)
        
        # normally the serializer is not dirty after loading a project file
        # however, when the file was corrupted, the user has the possibility
        # to save the fixed file after loading it.
        infoDir = topGroup['infos']
        localDataGroup = topGroup['local_data']
        
        assert self.topLevelOperator.DatasetRoles.ready(), \
            "Expected dataset roles to be hard-coded by the workflow."
        workflow_role_names = self.topLevelOperator.DatasetRoles.value

        # If the project file doesn't provide any role names, then we assume this is an old pixel classification project
        force_dirty = False
        backwards_compatibility_mode = ('Role Names' not in topGroup)
        self.topLevelOperator.DatasetGroup.resize( len(infoDir) )

        # The role names MAY be different than those that we have loaded in the workflow 
        #   because we might be importing from a project file made with a different workflow.
        # Therefore, we don't assert here.
        # assert workflow_role_names == list(topGroup['Role Names'][...])
        
        # Use the WorkingDirectory slot as a 'transaction' guard.
        # To prevent setupOutputs() from being called a LOT of times during this loop,
        # We'll disconnect it so the operator is not 'configured' while we do this work.
        # We'll reconnect it after we're done so the configure step happens all at once.
        working_dir = self.topLevelOperator.WorkingDirectory.value
        self.topLevelOperator.WorkingDirectory.disconnect()
        
        missing_role_warning_issued = False
        for laneIndex, (_, laneGroup) in enumerate( sorted(infoDir.items()) ):
            
            # BACKWARDS COMPATIBILITY:
            # Handle projects that didn't support multiple datasets per lane
            if backwards_compatibility_mode:
                assert 'location' in laneGroup
                datasetInfo, dirty = self._readDatasetInfo(laneGroup, localDataGroup, projectFilePath, headless)
                force_dirty |= dirty

                # Give the new info to the operator
                self.topLevelOperator.DatasetGroup[laneIndex][0].setValue(datasetInfo)
            else:
                for roleName, infoGroup in sorted(laneGroup.items()):
                    datasetInfo, dirty = self._readDatasetInfo(infoGroup, localDataGroup, projectFilePath, headless)
                    force_dirty |= dirty
    
                    # Give the new info to the operator
                    if datasetInfo is not None:
                        try:
                            # Look up the STORED role name in the workflow operator's list of roles. 
                            roleIndex = workflow_role_names.index( roleName )
                        except ValueError:
                            if not missing_role_warning_issued:
                                msg = 'Your project file contains a dataset for "{}", but the current '\
                                      'workflow has no use for it. The stored dataset will be ignored.'\
                                      .format( roleName )
                                logger.error(msg)
                                missing_role_warning_issued = True
                        else:
                            self.topLevelOperator.DatasetGroup[laneIndex][roleIndex].setValue(datasetInfo)

        # Finish the 'transaction' as described above.
        self.topLevelOperator.WorkingDirectory.setValue( working_dir )
        
        self._dirty = force_dirty
    
    def _readDatasetInfo(self, infoGroup, localDataGroup, projectFilePath, headless):
        # Unready datasets are represented with an empty group.
        if len( infoGroup ) == 0:
            return None, False


        info_params = {}

        # Make a reverse-lookup of the location storage strings
        LocationLookup = { v:k for k,v in list(self.LocationStrings.items()) }
        location = LocationLookup[ infoGroup['location'].value.decode('utf-8') ]
        info_params['location'] = location

        if 'allowLabels' in infoGroup:
            info_params['allowLabels'] = infoGroup['allowLabels'].value

        if 'drange' in infoGroup:
           info_params['drange'] = tuple( infoGroup['drange'].value )

        if 'shape' in infoGroup:
            info_params['laneShape'] = tuple(infoGroup['shape'].value)

        if 'dtype' in infoGroup:
            info_params['laneDtype'] = numpy.dtype(infoGroup['dtype'].value.decode('utf-8'))

        if 'display_mode' in infoGroup:
            info_params['display_mode'] = infoGroup['display_mode'].value.decode('utf-8')

        if 'nickname' in infoGroup:
            info_params['nickname'] = infoGroup['nickname'].value.decode('utf-8')

        if 'axistags' in infoGroup:
            tags = vigra.AxisTags.fromJSON( infoGroup['axistags'].value.decode('utf-8') )
            info_params['axistags'] = tags
        elif 'axisorder' in infoGroup:
            # Old projects just have an 'axisorder' field instead of full axistags
            axisorder = infoGroup['axisorder'].value.decode('utf-8')
            info_params['axistags'] = vigra.defaultAxistags(axisorder)

        if 'subvolume_roi' in infoGroup:
            start, stop = list(map( tuple, infoGroup['subvolume_roi'].value ))
            subvolume_roi = (start, stop)

        info_params['project_file'] = infoGroup.file
        dirty = False

        if 'datasetId' in infoGroup:
            dataset_id = infoGroup['datasetId'].value.decode('utf-8')
            filepath = localDataGroup.name + '/' + dataset_id
        else:
            filepath = infoGroup['filePath'].value.decode('utf-8')

        saved_data = localDataGroup.file[filepath].value
        laneShape = saved_data.shape
        laneDtype = saved_data.dtype
        info_params['filepath'] = filepath

        try:
            datasetInfo = DatasetInfo(**info_params)
        except FileNotFoundError as e:
            raise Exception("FXIME: repair file {e.filename}")
#            for missing_path in e.paths_not_found:
#                dirty = True
#                filt = "Image files (" + ' '.join('*.' + x for x in OpDataSelection.SupportedExtensions) + ')'
#                newpath = self.repairFile(path, filt) #FIXME: make repairFile also show interpath-picking dialog

        return datasetInfo, dirty

    def updateWorkingDirectory(self,newpath,oldpath):
        newdir = PathComponents(newpath).externalDirectory
        olddir = PathComponents(oldpath).externalDirectory
        
        if newdir==olddir:
            return
 
        # Disconnect the working directory while we make these changes.
        # All the changes will take effect when we set the new working directory.
        self.topLevelOperator.WorkingDirectory.disconnect()
        
        for laneIndex, multislot in enumerate(self.topLevelOperator.DatasetGroup):
            for roleIndex, slot in enumerate(multislot):
                if not slot.ready():
                    # Skip if there is no dataset in this lane/role combination yet.
                    continue
                datasetInfo = slot.value
                if datasetInfo.location == DatasetInfo.Location.FileSystem:
                    
                    #construct absolute path and recreate relative to the new path
                    fp = PathComponents(datasetInfo.filePath,olddir).totalPath()
                    abspath, relpath = getPathVariants(fp,newdir)
                    
                    # Same convention as in dataSelectionGui:
                    # Relative by default, unless the file is in a totally different tree from the working directory.
                    if relpath is not None and len(os.path.commonprefix([fp, abspath])) > 1:
                        datasetInfo.filePath = relpath
                    else:
                        datasetInfo.filePath = abspath
                    
                    slot.setValue(datasetInfo, check_changed=False)
        
        self.topLevelOperator.WorkingDirectory.setValue(newdir)
        self._projectFilePath = newdir
        
    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return self._dirty

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        self.topLevelOperator.DatasetGroup.resize( 0 )

    @property
    def _shouldRetrain(self):
        """
        Check if '--retrain' flag was passed via workflow command line arguments
        """
        workflow = self.topLevelOperator.parent
        if hasattr(workflow, 'retrain'):
            return workflow.retrain
        else:
            return False


class Ilastik05DataSelectionDeserializer(AppletSerializer):
    """
    Deserializes the user's input data selections from an ilastik v0.5 project file.
    """
    def __init__(self, topLevelOperator):
        super( Ilastik05DataSelectionDeserializer, self ).__init__( '' )
        self.topLevelOperator = topLevelOperator
    
    def serializeToHdf5(self, hdf5File, projectFilePath):
        # This class is for DEserialization only.
        pass

    def deserializeFromHdf5(self, hdf5File, projectFilePath, headless = False):
        #FIXME: convert old file to new schema
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # This is the v0.5 import deserializer.  Don't work with 0.6 projects (or anything else).
        if ilastikVersion != 0.5:
            return

        # The 'working directory' for the purpose of constructing absolute 
        #  paths from relative paths is the project file's directory.
        projectDir = os.path.split(projectFilePath)[0]
        self.topLevelOperator.WorkingDirectory.setValue( projectDir )

        # Access the top group and the info group
        try:
            #dataset = hdf5File["DataSets"]["dataItem00"]["data"]
            dataDir = hdf5File["DataSets"]
        except KeyError:
            # If our group (or subgroup) doesn't exist, then make sure the operator is empty
            self.topLevelOperator.DatasetGroup.resize( 0 )
            return
        
        self.topLevelOperator.DatasetGroup.resize( len(dataDir) )
        for index, (datasetDirName, datasetDir) in enumerate( sorted(dataDir.items()) ):
            datasetInfo = DatasetInfo()

            # We'll set up the link to the dataset in the old project file, 
            #  but we'll set the location to ProjectInternal so that it will 
            #  be copied to the new file when the project is saved.    
            datasetInfo.location = DatasetInfo.Location.ProjectInternal
            
            # Some older versions of ilastik 0.5 stored the data in tzyxc order.
            # Some power-users can enable a command-line flag that tells us to 
            #  transpose the data back to txyzc order when we import the old project.
            default_axis_order = ilastik.utility.globals.ImportOptions.default_axis_order
            if default_axis_order is not None:
                import warnings
                # todo:axisorder: this will apply for other old ilastik projects as well... adapt the formulation.
                warnings.warn( "Using a strange axis order to import ilastik 0.5 projects: {}".format( default_axis_order ) )
                datasetInfo.axistags = vigra.defaultAxistags(default_axis_order)
            
            # Write to the 'private' members to avoid resetting the dataset id
            totalDatasetPath = str(projectFilePath + '/DataSets/' + datasetDirName + '/data' )
            datasetInfo._filePath = totalDatasetPath
            datasetInfo._datasetId = datasetDirName # Use the old dataset name as the new dataset id
            datasetInfo.nickname = "{} (imported from v0.5)".format( datasetDirName )
            
            # Give the new info to the operator
            self.topLevelOperator.DatasetGroup[index][0].setValue(datasetInfo)

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless=False):
        # This deserializer is a special-case.
        # It doesn't make use of the serializer base class, which makes assumptions about the file structure.
        # Instead, if overrides the public serialize/deserialize functions directly
        assert False


    def isDirty(self):
        """ Return true if the current state of this item 
            (in memory) does not match the state of the HDF5 group on disk.
            SerializableItems are responsible for tracking their own dirty/notdirty state."""
        return False

    def unload(self):
        """ Called if either
            (1) the user closed the project or
            (2) the project opening process needs to be aborted for some reason
                (e.g. not all items could be deserialized properly due to a corrupted ilp)
            This way we can avoid invalid state due to a partially loaded project. """ 
        self.topLevelOperator.DatasetGroup.resize( 0 )




















