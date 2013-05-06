import os
import sys
import copy

from opBatchIo import ExportFormat

from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot, deleteIfPresent

from ilastik.utility import bind
from ilastik.utility.pathHelpers import PathComponents

# FIXME: re-add logging

class SerialDatasetPath(SerialSlot):
    """Stores the dirty flag so we can restore the previous
    session efficiently.

    """
    def __init__(self, slot, dirtyslot, **kwargs):
        super(SerialDatasetPath, self).__init__(slot, **kwargs)
        self.dirtyslot = dirtyslot

    def _serialize(self, group, name, slot):
        subgroup = group.create_group(name)
        for index in range(len(slot)):
            groupName = self.subname.format(index)
            dataGroup = subgroup.create_group(groupName)
            dataGroup.create_dataset('Dirty', data=self.dirtyslot[index].value)

    def deserialize(self, group):
        # override to ensure nothing happens, since this is not implemented.

        # TODO: Operator needs a way of being told his dirty status
        pass


class BatchIoSerializer(AppletSerializer):
    """
    Serializes the user's input data selections to an ilastik v0.6 project file.
    """
    def __init__(self, operator, projectFileGroupName):
        self.topLevelOperator = operator
        slots = [
            SerialSlot(operator.ExportDirectory, default=''),
            SerialSlot(operator.Format, default=ExportFormat.H5),
            SerialSlot(operator.Suffix, default='_results'),
            SerialDatasetPath(operator.DatasetPath,
                              operator.Dirty,
                              name='datasetInfos',
                              subname='dataset{:>04}',),
        ]

        super(BatchIoSerializer, self).__init__(projectFileGroupName,
                                                slots=slots)

    def initWithoutTopGroup(self, hdf5File, projectFilePath):
        # The 'working directory' for the purpose of constructing absolute 
        #  paths from relative paths is the project file's directory.
        projectDir = os.path.split(projectFilePath)[0]
        self.topLevelOperator.WorkingDirectory.setValue( projectDir )

    def _deserializeFromHdf5(self, topGroup, groupVersion, hdf5File, projectFilePath):
        """
        Additional deserialization.
        Deserialize the slots that weren't listed above and thus weren't deserialized in the base class.
        """
        # The 'working directory' for the purpose of constructing absolute 
        #  paths from relative paths is the project file's directory.
        self.initWithoutTopGroup(hdf5File, projectFilePath)

    def updateWorkingDirectory(self,newpath,oldpath):
        oldpath = PathComponents(oldpath).externalDirectory
        self.topLevelOperator.WorkingDirectory.setValue( oldpath )
