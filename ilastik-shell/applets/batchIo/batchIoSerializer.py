import os
import sys
import copy
from utility import VersionManager

from opBatchIo import ExportFormat

import logging
logger = logging.getLogger(__name__)
logger.setLevel( logging.DEBUG )
logger.addHandler( logging.StreamHandler(sys.stdout) )

class BatchIoSerializer(object):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1
    TopGroupName = 'BatchIo'

    def __init__(self, mainOperator, topGroupName=None):
        self.mainOperator = mainOperator
        if topGroupName is not None:
             self.TopGroupName = topGroupName
    
    def serializeToHdf5(self, hdf5File, projectFilePath):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return
        
        # Access our top group (create it if necessary)
        topGroup = self.getOrCreateGroup(hdf5File, self.TopGroupName)
        
        # Set the version
        if 'StorageVersion' not in topGroup.keys():
            topGroup.create_dataset('StorageVersion', data=self.SerializerVersion)
        else:
            topGroup['StorageVersion'][()] = self.SerializerVersion
        
        # Delete any datasets we're about to write
        self.deleteIfPresent( topGroup, 'ExportDirectory' )
        self.deleteIfPresent( topGroup, 'Format' )
        self.deleteIfPresent( topGroup, 'Suffix' )
        
        # These settings are common to all datasets.  Serialize to top group.
        topGroup.create_dataset( 'ExportDirectory', data=self.mainOperator.ExportDirectory.value )
        topGroup.create_dataset( 'Format', data=self.mainOperator.Format.value )
        topGroup.create_dataset( 'Suffix', data=self.mainOperator.Suffix.value )

        # Delete all previous dataset info
        self.deleteIfPresent(topGroup, 'datasetInfos')
        
        datasetDir = topGroup.create_group('datasetInfos')

        # Create a group for each dataset our operator has
        for index in range( len(self.mainOperator.DatasetPath) ):
            groupName = "dataset{:>04}".format(index)
            dataGroup = datasetDir.create_group( groupName )
            
            # Store the dirty flag so we can restore the previous session efficiently
            dataGroup.create_dataset('Dirty', data=self.mainOperator.Dirty[index])
            
    def deserializeFromHdf5(self, hdf5File, projectFilePath):
        # Check the overall file version
        ilastikVersion = hdf5File["ilastikVersion"].value

        # Make sure we can find our way around the project tree
        if not VersionManager.isProjectFileVersionCompatible(ilastikVersion):
            return
        
        # Get a handle to the top group.
        try:
            topGroup = hdf5File[self.TopGroupName]
        except KeyError:
            # Top group isn't present.  Clear the operator and give up. 
            self.unload()
            return

        try:
            exportDir = topGroup['ExportDirectory'][()]
            format = topGroup['Format'][()]
            suffix = topGroup['Suffix'][()]
            
            datasetDir = topGroup['datasetInfos']
            
            for name, group in sorted(datasetDir.items()):
                # TODO: Operator needs a way of being told his dirty status
                #self.mainOperator.
                pass
        except KeyError:
            self.unload()
        

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
        self.mainOperator.ExportDirectory.setValue( '' )
        self.mainOperator.Format( ExportFormat.H5 )
        self.mainOperator.Suffix( '_results' )
        self.mainOperator.DatasetPath.resize(0)

    def getOrCreateGroup(self, parentGroup, groupName):
        try:
            return parentGroup[groupName]
        except KeyError:
            return parentGroup.create_group(groupName)

    def deleteIfPresent(self, parentGroup, name):
        try:
            del parentGroup[name]
        except KeyError:
            pass


