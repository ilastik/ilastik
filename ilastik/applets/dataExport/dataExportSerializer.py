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
from functools import partial
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialListSlot
import numpy


_ALLOWED_TYPES = [
    numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64,
    numpy.int8, numpy.int16, numpy.int32, numpy.int64,
    numpy.float32, numpy.float64
]


class SerialDtypeSlot(SerialSlot):
    
    def __init__(self, slot, *args, **kwargs):
        super(SerialDtypeSlot, self).__init__(slot, *args, **kwargs)
        self._slot = slot

    @staticmethod
    def _saveValue(group, name, value):
        assert isinstance(value, type)
        group.create_dataset(name, data=value.__name__)

    @staticmethod
    def _getValue(subgroup, slot):
        val = numpy.dtype(subgroup[()]).type
        if val not in _ALLOWED_TYPES:
            raise ValueError(f"Datatype {val.name} not allowed!")
        slot.setValue(val)

class DataExportSerializer(AppletSerializer):
    """
    Serializes the user's data export settings to the project file.
    """
    def __init__(self, operator, projectFileGroupName, extraSerialSlots=[]):
        self.topLevelOperator = operator
        SerialRoiSlot = partial( SerialListSlot,
                                 store_transform=lambda x: -1 if x is None else x,
                                 transform=lambda x: None if x == -1 else x,
                                 iterable=tuple )
        slots = [
            SerialRoiSlot(operator.RegionStart),
            SerialRoiSlot(operator.RegionStop),

            SerialSlot(operator.InputMin),
            SerialSlot(operator.InputMax),
            SerialSlot(operator.ExportMin),
            SerialSlot(operator.ExportMax),
            
            SerialDtypeSlot(operator.ExportDtype),
            SerialSlot(operator.OutputAxisOrder),
            
            SerialSlot(operator.OutputFilenameFormat),
            SerialSlot(operator.OutputInternalPath),
            
            SerialSlot(operator.OutputFormat),
        ]
        
        slots += extraSerialSlots

        super(DataExportSerializer, self).__init__(projectFileGroupName,
                                                   slots=slots)

    def deserializeFromHdf5(self, *args):
        """
        Overriden from the base class so we can use the special TransactionSlot to
        speed up the otherwise SLOW process of configuring so many optional slots.
        """
        # Disconnect the transaction slot to prevent setupOutput() calls while we do this.
        self.topLevelOperator.TransactionSlot.disconnect()

        super( DataExportSerializer, self ).deserializeFromHdf5(*args)
        
        # Give the slot a value again to complete the 'transaction' (call setupOutputs)
        self.topLevelOperator.TransactionSlot.setValue(True)
        
