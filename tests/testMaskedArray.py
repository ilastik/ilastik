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
__date__ = "$Feb 02, 2015 21:38:31 EST$"



import numpy

import vigra

from lazyflow.graph import Graph
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot


class OpMaskArrayIdentity(Operator):
    name = "OpMaskArrayIdentity"
    category = "Pointwise"


    Input = InputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMaskArrayIdentity, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        # Get data
        data = self.Input[key].wait()

        # Copy results
        if slot.name == 'Output':
            result[...] = data

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "Input":
            slicing = roi.toSlice()
            self.Output.setDirty(slicing)
        else:
            assert False, "Unknown dirty input slot"
