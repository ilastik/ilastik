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
__date__ = "$Nov 12, 2014 15:20:09 EST$"



from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache

import vigra

import nanshe
import nanshe.util.iters


class OpMeanProjection(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpMeanProjection"
    category = "Pointwise"


    Input = InputSlot()

    Axis = InputSlot(value=0, stype="int")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMeanProjection, self ).__init__( *args, **kwargs )

        self._generation = {self.name : 0}

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )

        self.Output.meta.axistags = vigra.AxisTags(
            *list(nanshe.util.iters.iter_with_skip_indices( self.Output.meta.axistags, self.Axis.value))
        )

        self.Output.meta.shape = self.Output.meta.shape[:self.Axis.value] +\
                                 self.Output.meta.shape[self.Axis.value+1:]

        self.Output.meta.generation = self._generation

    def execute(self, slot, subindex, roi, result):
        axis = self.Axis.value

        assert(axis < len(self.Input.meta.shape))

        key = roi.toSlice()
        key = list(key)
        key = key[:axis] + [slice(None)] + key[axis:]
        key[axis] = nanshe.util.iters.reformat_slice(key[axis], self.Input.meta.shape[axis])
        key = tuple(key)

        raw = self.Input[key].wait()

        processed = raw.mean(axis=self.Axis.value)

        if slot.name == 'Output':
            result[...] = processed

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "Input":
            self._generation[self.name] += 1

            axis = self.Axis.value

            slicing = roi.toSlice()
            slicing = list(slicing)
            slicing = slicing[:axis] + slicing[axis+1:]
            slicing = tuple(slicing)

            self.Output.setDirty(slicing)
        elif slot.name == "Axis":
            self._generation[self.name] += 1
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpMeanProjectionCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpMeanProjectionCached"
    category = "Pointwise"


    Input = InputSlot()

    Axis = InputSlot(value=0, stype="int")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpMeanProjectionCached, self ).__init__( *args, **kwargs )

        self.opMeanProjection = OpMeanProjection(parent=self)

        self.opMeanProjection.Axis.connect(self.Axis)


        self.opCache = OpBlockedArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)

        self.opMeanProjection.Input.connect( self.Input )
        self.opCache.Input.connect( self.opMeanProjection.Output )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        block_shape = self.opMeanProjection.Output.meta.shape

        block_shape = list(block_shape)
        for i, each_axistag in enumerate(self.opMeanProjection.Output.meta.axistags):
            if each_axistag.isSpatial():
                block_shape[i] = 256

            block_shape[i] = min(block_shape[i], self.opMeanProjection.Output.meta.shape[i])

        block_shape = tuple(block_shape)

        self.opCache.innerBlockShape.setValue(block_shape)
        self.opCache.outerBlockShape.setValue(block_shape)

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
