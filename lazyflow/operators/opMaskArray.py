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
__date__ = "$Feb 06, 2015 13:14:23 EST$"



import numpy

from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot


class OpMaskArray(Operator):
    name = "OpMaskArray"
    category = "Pointwise"


    InputArray = InputSlot(allow_mask=True)
    InputMask = InputSlot()

    Output = OutputSlot(allow_mask=True)

    def __init__(self, *args, **kwargs):
        super( OpMaskArray, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputArray.meta )
        self.Output.meta.has_mask = True

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        if slot.name == 'Output':
            # Write data into result (including a mask if provided)
            self.InputArray[key].writeInto(result).wait()

            # Get the added mask
            mask = self.InputMask[key].wait()

            # Apply the combination of the masks to result.
            result.mask[...] |= mask

    def propagateDirty(self, slot, subindex, roi):
        if (slot.name == "InputArray") or (slot.name == "InputMask"):
            slicing = roi.toSlice()
            self.Output.setDirty(slicing)
        else:
            assert False, "Unknown dirty input slot"
