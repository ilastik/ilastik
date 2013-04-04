from opDataSelection import OpDataSelection, DatasetInfo
from lazyflow.operators.ioOperators import OpStackToH5Writer
from lazyflow.operators import OpH5WriterBigDataset

import os
import copy
from ilastik.utility import bind, PathComponents
from ilastik.utility.pathHelpers import areOnSameDrive,getPathVariants
import ilastik.utility.globals

from ilastik.applets.base.appletSerializer import \
    AppletSerializer, getOrCreateGroup, deleteIfPresent

import logging
logger = logging.getLogger(__name__)

class DataSelectionSerializer( AppletSerializer ):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    # Constants    
    LocationStrings = { DatasetInfo.Location.FileSystem      : 'FileSystem',
                        DatasetInfo.Location.ProjectInternal : 'ProjectInternal' }

    def __init__(self, topLevelOperator, projectFileGroupName):
        super( DataSelectionSerializer, self ).__init__(projectFileGroupName)
        self.topLevelOperator = topLevelOperator
        self._dirty = False
        self.caresOfHeadless = True
        
        self._projectFilePath = None
        
        def handleDirty():
            self._dirty = True
        self.topLevelOperator.ProjectFile.notifyDirty( bind(handleDirty) )
        self.topLevelOperator.ProjectDataGroup.notifyDirty( bind(handleDirty) )
        self.topLevelOperator.WorkingDirectory.notifyDirty( bind(handleDirty) )
        
        def handleNewDataset(slot, index):
            slot[index].notifyDirty( bind(handleDirty) )
        # Dataset is a multi-slot, so subscribe to dirty callbacks on each slot as it is added
        self.topLevelOperator.Dataset.notifyInserted( bind(handleNewDataset) )

        # If a dataset was removed, we need to be reserialized.
        self.topLevelOperator.Dataset.notifyRemoved( bind(handleDirty) )
        
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        # Write any missing local datasets to the local_data group
        localDataGroup = getOrCreateGroup(topGroup, 'local_data')
        wroteInternalData = False
        for index, slot in enumerate(self.topLevelOperator.Dataset):
            info = slot.value
            # If this dataset should be stored in the project, but it isn't there yet
            if  info.location == DatasetInfo.Location.ProjectInternal \
            and info.datasetId not in localDataGroup.keys():
                # Obtain the data from the corresponding output and store it to the project.
                dataSlot = self.topLevelOperator.Image[index]

                opWriter = OpH5WriterBigDataset(graph=self.topLevelOperator.graph)
                opWriter.hdf5File.setValue( localDataGroup )
                opWriter.hdf5Path.setValue( info.datasetId )
                opWriter.Image.connect(dataSlot)

                # Trigger the copy
                success = opWriter.WriteImage.value
                assert success

                # Add the axistags attribute to the dataset we just created
                localDataGroup[info.datasetId].attrs['axistags'] = dataSlot.meta.axistags.toJSON()

                # Update the dataset info with no path, just filename base to remind us what this data is
                # (operator will react to the change when we call setValue(), below)
                # Directly set the private member to avoid getting a new datasetid
                info._filePath = PathComponents(info.filePath).filenameBase
                wroteInternalData = True

        # Construct a list of all the local dataset ids we want to keep
        localDatasetIds = [ slot.value.datasetId
                             for index, slot 
                             in enumerate(self.topLevelOperator.Dataset)
                             if slot.value.location == DatasetInfo.Location.ProjectInternal ]

        # Delete any datasets in the project that aren't needed any more
        for datasetName in localDataGroup.keys():
            if datasetName not in localDatasetIds:
                del localDataGroup[datasetName]

        if wroteInternalData:
            # We can only re-configure the operator if we're not saving a snapshot
            # We know we're saving a snapshot if the project file isn't the one we deserialized with.
            if self._projectFilePath is None or self._projectFilePath == projectFilePath:
                # Force the operator to setupOutputs() again so it gets data from the project, not external files
                firstInfo = self.topLevelOperator.Dataset[0].value
                self.topLevelOperator.Dataset[0].setValue(firstInfo, False)

        # Access the info group
        infoDir = getOrCreateGroup(topGroup, 'infos')
        
        # Delete all infos
        for infoName in infoDir.keys():
            del infoDir[infoName]
                
        # Rebuild the list of infos
        for index, slot in enumerate(self.topLevelOperator.Dataset):
            infoGroup = infoDir.create_group('info{:04d}'.format(index))
            datasetInfo = slot.value
            locationString = self.LocationStrings[datasetInfo.location]
            infoGroup.create_dataset('location', data=locationString)
            infoGroup.create_dataset('filePath', data=datasetInfo.filePath)
            infoGroup.create_dataset('datasetId', data=datasetInfo.datasetId)
            infoGroup.create_dataset('allowLabels', data=datasetInfo.allowLabels)
            if datasetInfo.axisorder is not None:
                infoGroup.create_dataset('axisorder', data=datasetInfo.axisorder)
        
        self._dirty = False

    def importStackAsLocalDataset(self, info):
        """
        Add the given stack data to the project file as a local dataset.
        Create a datainfo and append it to our operator.
        """
        try:
            self.progressSignal.emit(0)
            
            projectFileHdf5 = self.topLevelOperator.ProjectFile.value
            topGroup = getOrCreateGroup(projectFileHdf5, self.topGroupName)
            localDataGroup = getOrCreateGroup(topGroup, 'local_data')

            globstring = info.filePath
            info.location = DatasetInfo.Location.ProjectInternal
            
            opWriter = OpStackToH5Writer(graph=self.topLevelOperator.graph)
            opWriter.hdf5Group.setValue(localDataGroup)
            opWriter.hdf5Path.setValue(info.datasetId)
            opWriter.GlobString.setValue(globstring)
                
            # Forward progress from the writer directly to our applet                
            opWriter.progressSignal.subscribe( self.progressSignal.emit )
            
            success = opWriter.WriteImage.value
            
            numDatasets = len(self.topLevelOperator.Dataset)
            self.topLevelOperator.Dataset.resize( numDatasets + 1 )
            self.topLevelOperator.Dataset[numDatasets].setValue(info)
            
        finally:
            self.progressSignal.emit(100)

        return success

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        # The 'working directory' for the purpose of constructing absolute 
        #  paths from relative paths is the project file's directory.
        projectDir = os.path.split(projectFilePath)[0]
        self.topLevelOperator.WorkingDirectory.setValue( projectDir )
        self.topLevelOperator.ProjectDataGroup.setValue( self.topGroupName + '/local_data' )
        self.topLevelOperator.ProjectFile.setValue( hdf5File )
        
        self._dirty = False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath, headless):
        self._projectFilePath = projectFilePath
        self.initWithoutTopGroup(hdf5File, projectFilePath)
        
        # normally the serializer is not dirty after loading a project file
        # however, when the file was corrupted, the user has the possibility
        # to save the fixed file after loading it.
        dirty = False 
        
        infoDir = topGroup['infos']
        
        self.topLevelOperator.Dataset.resize( len(infoDir) )
        for index, (infoGroupName, infoGroup) in enumerate( sorted(infoDir.items()) ):
            datasetInfo = DatasetInfo()

            # Make a reverse-lookup of the location storage strings            
            LocationLookup = { v:k for k,v in self.LocationStrings.items() }
            datasetInfo.location = LocationLookup[ str(infoGroup['location'].value) ]
            
            # Write to the 'private' members to avoid resetting the dataset id
            datasetInfo._filePath = str(infoGroup['filePath'].value)
            datasetInfo._datasetId = str(infoGroup['datasetId'].value)

            # Deserialize the "allow labels" flag
            try:
                datasetInfo.allowLabels = infoGroup['allowLabels'].value
            except KeyError:
                pass

            # Deserialize the axisorder (if present)
            try:
                datasetInfo.axisorder = infoGroup['axisorder'].value
            except KeyError:
                pass
            
            # If the data is supposed to be in the project,
            #  check for it now.
            if datasetInfo.location == DatasetInfo.Location.ProjectInternal:
                if not datasetInfo.datasetId in topGroup['local_data'].keys():
                    raise RuntimeError("Corrupt project file.  Could not find data for " + infoGroupName)

            # If the data is supposed to exist outside the project, make sure it really does.
            if datasetInfo.location == DatasetInfo.Location.FileSystem:
                pathData = PathComponents( datasetInfo.filePath, os.path.split(projectFilePath)[0])
                filePath = pathData.externalPath
                if not os.path.exists(filePath):
                    if headless:
                        raise RuntimeError("Could not find data at " + filePath)
                    filt = "Image files (" + ' '.join('*.' + x for x in OpDataSelection.SupportedExtensions) + ')'
                    newpath = self.repairFile(filePath, filt)
                    newpath = newpath+pathData.internalPath
                    datasetInfo._filePath = getPathVariants(newpath , os.path.split(projectFilePath)[0])[0]
                    
                    dirty = True
                    
            # Give the new info to the operator
            self.topLevelOperator.Dataset[index].setValue(datasetInfo)

        self._dirty = dirty
    
    def updateWorkingDirectory(self,newpath,oldpath):
        
        newpath,oldpath = PathComponents(newpath).externalDirectory,PathComponents(oldpath).externalDirectory
        
        if newpath==oldpath:
            return
        
        for slot in self.topLevelOperator.Dataset:
            datasetInfo = slot.value
            if datasetInfo.location == DatasetInfo.Location.FileSystem:
                
                #construct absolute path and recreate relative to the new path
                fp = PathComponents(datasetInfo.filePath,oldpath).totalPath()
                abspath,relpath = getPathVariants(fp,newpath)
                
                # Same convention as in dataSelectionGui:
                # Relative by default, unless the file is in a totally different tree from the working directory.
                if len(os.path.commonprefix([fp, abspath])) > 1: datasetInfo.filePath = relpath
                else:datasetInfo.filePath = abspath
                
                slot.setValue(datasetInfo)
        
        self.topLevelOperator.WorkingDirectory.setValue(newpath)
        self._projectFilePath = newpath
        
        for slot in self.topLevelOperator.Dataset:
            self.topLevelOperator.applet._gui.updateTableForSlot(slot = slot)
    
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
        self.topLevelOperator.Dataset.resize( 0 )


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
            self.topLevelOperator.Dataset.resize( 0 )
            return
        
        self.topLevelOperator.Dataset.resize( len(dataDir) )
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
                warnings.warn( "Using a strange axis order to import ilastik 0.5 projects: {}".format( default_axis_order ) )
                datasetInfo.axisorder = default_axis_order
            
            # Write to the 'private' members to avoid resetting the dataset id
            totalDatasetPath = projectFilePath + '/DataSets/' + datasetDirName + '/data'
            datasetInfo._filePath = str(totalDatasetPath)
            datasetInfo._datasetId = datasetDirName # Use the old dataset name as the new dataset id
            
            # Give the new info to the operator
            self.topLevelOperator.Dataset[index].setValue(datasetInfo)

    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
        assert False

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
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
        self.topLevelOperator.Dataset.resize( 0 )




















