###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Feb 26, 2015 11:47:00 EST$"



import numpy

from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot


class OpFillMaskArray(Operator):
    name = "OpFillMaskArray"
    category = "Pointwise"


    InputArray = InputSlot()
    InputFillValue = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpFillMaskArray, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputArray.meta )
        self.Output.meta.has_mask = False

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        # Get data
        data = self.InputArray[key].wait()
        value = self.InputFillValue.value

        # Copy results
        if slot.name == 'Output':
            if not isinstance(data, numpy.ma.masked_array):
                result[...] = data
            else:
                result[...] = data.filled(value)

    def propagateDirty(self, slot, subindex, roi):
        if (slot.name == "InputArray"):
            slicing = roi.toSlice()
            self.Output.setDirty(slicing)
        elif (slot.name == "InputFillValue"):
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown dirty input slot"
