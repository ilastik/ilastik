import os
import sys
import copy

from opBatchIo import ExportFormat

from ilastik.applets.base.appletSerializer import \
    AppletSerializer, SerialSlot, deleteIfPresent

from ilastik.utility import bind

# FIXME: re-add logging

class SerialDatasetPath(SerialSlot):
    """Stores the dirty flag so we can restore the previous
    session efficiently.

    """
    def __init__(self, slot, dirtyslot, *args, **kwargs):
        super(SerialDatasetPath, self).__init__(slot, *args, **kwargs)
        self.dirtyslot = dirtyslot

    def _serialize(self, group):
        subgroup = group.create_group(self.name)
        for index in range(len(self.slot)):
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
        slots = [
            SerialSlot(operator.ExportDirectory, default=''),
            SerialSlot(operator.Format, default=ExportFormat.H5),
            SerialSlot(operator.Suffix, default='_results'),
            SerialDatasetPath(operator.DatasetPath,
                              operator.Dirty,
                              name=('datasetInfos', 'dataset{:>04}')),
        ]

        super(BatchIoSerializer, self).__init__(projectFileGroupName,
                                                slots=slots)
