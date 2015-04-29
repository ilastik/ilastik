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
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache


class OpConvertType(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpConvertType"
    category = "Pointwise"


    Input = InputSlot()

    Dtype = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpConvertType, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )

        self.Output.meta.dtype = numpy.dtype(self.Dtype.value).type

    def execute(self, slot, subindex, roi, result):
        dtype = numpy.dtype(self.Dtype.value).type

        key = roi.toSlice()

        raw = self.Input[key].wait()

        processed = raw.astype(dtype, copy=False)

        if slot.name == 'Output':
            result[...] = processed

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "Input":
            slicing = roi.toSlice()

            self.Output.setDirty(slicing)
        elif slot.name == "Dtype":
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpConvertTypeCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpConvertTypeCached"
    category = "Pointwise"


    Input = InputSlot()

    Dtype = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpConvertTypeCached, self ).__init__( *args, **kwargs )

        self.opConvertType = OpConvertType(parent=self)

        self.opConvertType.Dtype.connect(self.Dtype)


        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)

        self.opConvertType.Input.connect( self.Input )
        self.opCache.Input.connect( self.opConvertType.Output )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        block_shape = self.opConvertType.Output.meta.shape

        block_shape = list(block_shape)
        for i, each_axistag in enumerate(self.opConvertType.Output.meta.axistags):
            if each_axistag.isSpatial():
                block_shape[i] = 256

            block_shape[i] = min(block_shape[i], self.opConvertType.Output.meta.shape[i])

        block_shape = tuple(block_shape)

        self.opCache.innerBlockShape.setValue(block_shape)
        self.opCache.outerBlockShape.setValue(block_shape)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
