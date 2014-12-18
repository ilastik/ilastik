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
__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Dec 03, 2014 14:29:15 EST$"



import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache


class OpConvertType(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpConvertType"
    category = "Pointwise"


    InputImage = InputSlot()

    Dtype = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpConvertType, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )

        self.Output.meta.dtype = numpy.dtype(self.Dtype.value).type

    def execute(self, slot, subindex, roi, result):
        dtype = numpy.dtype(self.Dtype.value).type

        key = roi.toSlice()

        raw = self.InputImage[key].wait()

        processed = raw.astype(dtype, copy=False)

        if slot.name == 'Output':
            result[...] = processed

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            slicing = roi.toSlice()

            self.Output.setDirty(slicing)
        elif slot.name == "Dtype":
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
