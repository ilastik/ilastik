import os
import sys
import copy

from opBatchIo import ExportFormat

from ilastik.ilastikshell.appletSerializer import AppletSerializer

from ilastik.utility import bind

import logging
logger = logging.getLogger(__name__)
logger.setLevel( logging.DEBUG )
logger.addHandler( logging.StreamHandler(sys.stdout) )

class BatchIoSerializer(AppletSerializer):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    SerializerVersion = 0.1

    def __init__(self, mainOperator, projectFileGroupName):
        super( BatchIoSerializer, self ).__init__( projectFileGroupName, self.SerializerVersion )
        self.mainOperator = mainOperator
        
        self._dirty = False
        
        def handleDirty():
            self._dirty = True
        self.mainOperator.ExportDirectory.notifyDirty( bind(handleDirty) )
        self.mainOperator.Format.notifyDirty( bind(handleDirty) )
        self.mainOperator.Suffix.notifyDirty( bind(handleDirty) )
        
        def handleNewDataset(slot, index):
            slot[index].notifyDirty( bind(handleDirty) )
        # DatasetPath is a multi-slot, so subscribe to dirty callbacks on each slot as it is added
        self.mainOperator.DatasetPath.notifyInserted( bind(handleNewDataset) )
    
    def _serializeToHdf5(self, topGroup, hdf5File, projectFilePath):
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
        self._dirty = False
            
    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
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
        self._dirty = False

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
        self.mainOperator.ExportDirectory.setValue( '' )
        self.mainOperator.Format.setValue( ExportFormat.H5 )
        self.mainOperator.Suffix.setValue( '_results' )
        self.mainOperator.DatasetPath.resize(0)
