# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from functools import partial
from ilastik.applets.base.appletSerializer import AppletSerializer, SerialSlot, SerialListSlot

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
        from numpy import uint8, uint16, uint32, uint64, int8, int16, int32, int64, float32, float64
        val = eval(subgroup[()])
        slot.setValue(val)

class DataExportSerializer(AppletSerializer):
    """
    Serializes the user's data export settings to the project file.
    """
    def __init__(self, operator, projectFileGroupName):
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
        