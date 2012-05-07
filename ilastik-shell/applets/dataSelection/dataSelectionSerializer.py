from opDataSelection import OpDataSelection
Location = OpDataSelection.DatasetInfo.Location

import vigra
import copy
from utility import SimpleSignal # from the ilastik-shell utility module
from utility import VersionManager

import logging
logger = logging.getLogger(__name__)

class DataSelectionSerializer(object):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    TopGroupName = 'DataSelection'

    # Constants    
    LocationStrings = { Location.FileSystem      : 'FileSystem',
                        Location.ProjectInternal : 'ProjectInternal' }

    def __init__(self, mainOperator):
        self.mainOperator = mainOperator
    
    def serializeToHdf5(self, hdf5File):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return
        
        # If the operator has a some other project file, something's wrong
        if self.mainOperator.ProjectFile.connected():
            assert self.mainOperator.ProjectFile.value == hdf5File
        
        # Access our top group (create it if necessary)
        topGroup = self.getOrCreateGroup(hdf5File, self.TopGroupName)
        
        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self.SerializerVersion)
        else:
            topGroup['StorageVersion'][()] = self.SerializerVersion
        
        # Access the info group
        infoDir = self.getOrCreateGroup(topGroup, 'infos')
        
        # Delete all infos
        for infoName in infoDir.keys():
            del infoDir[infoName]
                
        # Rebuild the list of infos
        for index, slot in enumerate(self.mainOperator.DatasetInfos):
            infoGroup = infoDir.create_group('info{:03d}'.format(index))
            datasetInfo = slot.value
            locationString = self.LocationStrings[datasetInfo.location]
            infoGroup.create_dataset('location', data=locationString)
            infoGroup.create_dataset('filePath', data=datasetInfo.filePath)
            infoGroup.create_dataset('datasetId', data=datasetInfo.datasetId)
            infoGroup.create_dataset('invertColors', data=datasetInfo.invertColors)
            infoGroup.create_dataset('convertToGrayscale', data=datasetInfo.convertToGrayscale)
        
        # Write any missing local datasets to the local_data group
        localDataGroup = self.getOrCreateGroup(topGroup, 'local_data')
        wroteInternalData = False
        for index, slot in enumerate(self.mainOperator.DatasetInfos):
            info = slot.value
            # If this dataset should be stored in the project, but it isn't there yet
            if  info.location == Location.ProjectInternal \
            and info.datasetId not in localDataGroup.keys():
                # Obtain the data from the corresponding output and store it to the project.
                # TODO: Optimize this for large datasets by streaming it chunk-by-chunk.
                dataSlot = self.mainOperator.OutputImages[index]
                data = dataSlot[...].wait()
                vigraData = data.view(vigra.VigraArray)
                vigraData.axistags = dataSlot.meta.axistags
                vigra.impex.writeHDF5(vigraData, localDataGroup, info.datasetId)
                # We also store the original axis ordering
                keys = [tag.key for tag in vigraData.axistags]
                axisorder = '-'.join(keys)
                localDataGroup[info.datasetId].attrs['axisorder'] = axisorder
                wroteInternalData = True

        # Construct a list of all the local dataset ids we want to keep
        localDatasetIds = [ slot.value.datasetId
                             for index, slot 
                             in enumerate(self.mainOperator.DatasetInfos)
                             if slot.value.location == Location.ProjectInternal ]

        # Delete any datasets in the project that aren't needed any more
        for datasetName in localDataGroup.keys():
            if datasetName not in localDatasetIds:
                del localDataGroup[datasetName]

        if wroteInternalData:
            # The operator should use the same project file that we're using
            self.mainOperator.ProjectFile.setValue(hdf5File)
            
            # Force the operator to setupOutputs() again so it gets data from the project, not external files
            # TODO: This will cause a slew of 'dirty' operators for any inputs we saved.
            #       Is that a problem?
            infoCopy = copy.copy(self.mainOperator.DatasetInfos[0].value)
            self.mainOperator.DatasetInfos[0].setValue(infoCopy)

    def deserializeFromHdf5(self, hdf5File):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return

        # Access the top group and the info group
        #  If it doesn't exist we simply return without adding any input to the operator.
        try:
            topGroup = hdf5File[DataSelectionSerializer.TopGroupName]
            infoDir = topGroup['infos']
        except KeyError:
            return

        # Provide the project file to our operator
        self.mainOperator.ProjectFile.setValue(hdf5File)
        
        self.mainOperator.DatasetInfos.resize( len(infoDir) )
        for index, (infoGroupName, infoGroup) in enumerate( sorted(infoDir.items()) ):
            datasetInfo = OpDataSelection.DatasetInfo()

            # Make a reverse-lookup of the location storage strings            
            LocationLookup = { v:k for k,v in self.LocationStrings.items() }
            datasetInfo.location = LocationLookup[ str(infoGroup['location'].value) ]
            
            datasetInfo.invertColors = bool(infoGroup['invertColors'].value)
            datasetInfo.convertToGrayscale = bool(infoGroup['convertToGrayscale'].value)

            # Write to the 'private' members to avoid resetting the dataset id
            datasetInfo._filePath = str(infoGroup['filePath'].value)
            datasetInfo._datasetId = str(infoGroup['datasetId'].value)
            
            # If the data is supposed to be in the project,
            #  check for it now.
            if datasetInfo.location == Location.ProjectInternal:
                assert datasetInfo.datasetId in topGroup['local_data'].keys()
            
            # Give the new info to the operator
            self.mainOperator.DatasetInfos[index].setValue(datasetInfo)

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
        pass

    def getOrCreateGroup(self, parentGroup, groupName):
        try:
            return parentGroup[groupName]
        except KeyError:
            return parentGroup.create_group(groupName)

if __name__ == "__main__":
    import os
    import h5py
    from lazyflow.graph import Graph
    from opDataSelection import OpDataSelection

    # Define the files we'll be making    
    testProjectName = 'test_project.ilp'
    # Clean up: Remove the test data files we created last time (just in case)
    for f in [testProjectName]:
        try:
            os.remove(f)
        except:
            pass

    # Create an empty project
    testProject = h5py.File(testProjectName)
    testProject.create_dataset("ilastikVersion", data=0.6)
    
    ##
    ## Serialization
    ##

    # Create an operator to work with and give it some input
    graph = Graph()
    operatorToSave = OpDataSelection(graph=graph)
    operatorToSave.ProjectFile.setValue(testProject)
    
    info = OpDataSelection.DatasetInfo()
    info.filePath = '5d.npy'
    info.invertColors = False
    info.convertToGrayscale = True
    info.location = Location.ProjectInternal
    
    operatorToSave.DatasetInfos.resize(1)
    operatorToSave.DatasetInfos[0].setValue(info)
    
    # Now serialize!
    serializer = DataSelectionSerializer(operatorToSave)
    serializer.serializeToHdf5(testProject)
    
    # Check for dataset existence
    dataset = vigra.impex.readHDF5(testProject, DataSelectionSerializer.TopGroupName + '/local_data/' + info.datasetId, 'C')
    
    # Debug info...
    logger.debug('dataset.shape =',dataset.shape)
    logger.debug('should be', operatorToSave.OutputImages[0].meta.shape)
    logger.debug('dataset axistags:')
    logger.debug(dataset.axistags)
    logger.debug('should be:')
    logger.debug(operatorToSave.OutputImages[0].meta.axistags)

    originalShape = operatorToSave.OutputImages[0].meta.shape
    originalAxisTags = operatorToSave.OutputImages[0].meta.axistags
    originalAxisOrder = [tag.key for tag in originalAxisTags]

    # The dataset axis ordering may have changed when it was written to disk,
    #  so convert it to the original ordering before we inspect it.
    dataset = dataset.withAxes(*originalAxisOrder)
    
    # Now we can directly compare the shape and axis ordering
    assert dataset.shape == originalShape
    assert dataset.axistags == originalAxisTags
    
    ##
    ## Deserialization
    ##

    # Create an empty operator
    graph = Graph()
    operatorToLoad = OpDataSelection(graph=graph)
    
    deserializer = DataSelectionSerializer(operatorToLoad)
    deserializer.deserializeFromHdf5(testProject)
    
    assert len(operatorToLoad.DatasetInfos) == len(operatorToSave.DatasetInfos)
    assert len(operatorToLoad.OutputImages) == len(operatorToSave.OutputImages)
    
    assert operatorToLoad.OutputImages[0].meta.shape == operatorToSave.OutputImages[0].meta.shape
    assert operatorToLoad.OutputImages[0].meta.axistags == operatorToSave.OutputImages[0].meta.axistags





































