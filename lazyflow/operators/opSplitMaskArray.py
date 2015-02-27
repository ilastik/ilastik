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
__date__ = "$Feb 27, 2015 09:51:01 EST$"



import numpy

from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot


class OpSplitMaskArray(Operator):
    name = "OpSplitMaskArray"
    category = "Pointwise"

    Input = InputSlot()

    OutputArray = OutputSlot()
    OutputMask = OutputSlot()
    OutputFillValue = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpSplitMaskArray, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.OutputArray.meta.assignFrom( self.Input.meta )
        self.OutputArray.meta.has_mask = False

        self.OutputMask.meta.assignFrom( self.Input.meta )
        self.OutputMask.meta.has_mask = False
        self.OutputMask.meta.dtype = numpy.bool8

        self.OutputFillValue.meta.assignFrom( self.Input.meta )
        self.OutputFillValue.meta.has_mask = False
        self.OutputFillValue.meta.shape = tuple()

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        input_subview = self.Input[key].wait()

        if slot.name == 'OutputArray':
            result[...] = input_subview.data
        elif slot.name == 'OutputMask':
            result[...] = input_subview.mask
        elif slot.name == 'OutputFillValue':
            result[...] = input_subview.fill_value

    def propagateDirty(self, slot, subindex, roi):
        if (slot.name == "Input"):
            slicing = roi.toSlice()
            self.OutputArray.setDirty(slicing)
            self.OutputMask.setDirty(slicing)
            self.OutputFillValue.setDirty(Ellipsis)
        else:
            assert False, "Unknown dirty input slot"
