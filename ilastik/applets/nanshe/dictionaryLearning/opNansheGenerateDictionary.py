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
__date__ = "$Oct 17, 2014 13:07:51 EDT$"



from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpArrayCache

from ilastik.applets.base.applet import DatasetConstraintError

import numpy

import vigra

import nanshe
import nanshe.imp.segment
import nanshe.util.iters


class OpNansheGenerateDictionary(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheGenerateDictionary"
    category = "Pointwise"


    Input = InputSlot()

    K = InputSlot(value=100, stype="int")
    Gamma1 = InputSlot(value=0.0)
    Gamma2 = InputSlot(value=0.0)
    NumThreads = InputSlot(value=1)
    Batchsize = InputSlot(value=256)
    NumIter = InputSlot(value=100, stype="int")
    Lambda1 = InputSlot(value=0.2)
    Lambda2 = InputSlot(value=0.0)
    PosAlpha = InputSlot(value=True)
    PosD = InputSlot(value=True)
    Clean = InputSlot(value=True)
    Mode = InputSlot(value=2, stype="int")
    ModeD = InputSlot(value=0, stype="int")

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheGenerateDictionary, self ).__init__( *args, **kwargs )

        self.Input.notifyReady( self._checkConstraints )

    def _checkConstraints(self, *args):
        slot = self.Input

        sh = slot.meta.shape
        ax = slot.meta.axistags
        if (len(slot.meta.shape) != 4) and (len(slot.meta.shape) != 5):
            # Raise a regular exception.  This error is for developers, not users.
            raise RuntimeError("was expecting a 4D or 5D dataset, got shape=%r" % (sh,))

        if "t" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input must have time.")

        if "y" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input must have space dim y.")

        if "x" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input must have space dim x.")

        if "c" not in slot.meta.getTaggedShape():
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input must have channel.")

        numChannels = slot.meta.getTaggedShape()["c"]
        if numChannels != 1:
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input image must have exactly one channel.  " +
                "You attempted to add a dataset with {} channels".format( numChannels ) )

        if not ax[0].isTemporal():
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input image must have time first." )

        if not ax[-1].isChannel():
            raise DatasetConstraintError(
                "GenerateDictionary",
                "Input image must have channel last." )

        for i in range(1, len(ax) - 1):
            if not ax[i].isSpatial():
                # This is for developers.  Don't need a user-friendly error.
                raise RuntimeError("%d-th axis %r is not spatial" % (i, ax[i]))

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = numpy.float64

        spatial_dims = [_ for _ in self.Output.meta.axistags if _.isSpatial()]

        self.Output.meta.axistags = vigra.AxisTags(vigra.AxisInfo.c, *spatial_dims)

        self.Output.meta.shape = (self.K.value,) + self.Input.meta.shape[1:-1]

    def execute(self, slot, subindex, roi, result):
        output_key = roi.toSlice()

        output_key = nanshe.util.iters.reformat_slices(output_key)

        input_key = list(output_key)

        input_key[0] = slice(0, self.Input.meta.shape[0], 1)
        input_key.append(slice(0, 1, 1))

        input_key = tuple(input_key)


        output_key = list(output_key)

        for i in xrange(1, len(output_key)):
            output_key[i] = slice(0, output_key[i].stop - output_key[i].start, output_key[i].step)

        output_key = tuple(output_key)

        raw = self.Input[input_key].wait()
        raw = raw[..., 0]

        K = self.K.value
        gamma1 = self.Gamma1.value
        gamma2 = self.Gamma2.value
        numThreads = self.NumThreads.value
        batchsize = self.Batchsize.value
        numIter = self.NumIter.value
        lambda1 = self.Lambda1.value
        lambda2 = self.Lambda2.value
        posAlpha = self.PosAlpha.value
        posD = self.PosD.value
        clean = self.Clean.value
        mode = self.Mode.value
        modeD = self.ModeD.value

        processed = nanshe.imp.segment.generate_dictionary(raw,
                                                           **{ "spams.trainDL" :
                                                                   {
                                                                       "K" : K,
                                                                       "gamma1" : gamma1,
                                                                       "gamma2" : gamma2,
                                                                       "numThreads" : numThreads,
                                                                       "batchsize" : batchsize,
                                                                       "iter" : numIter,
                                                                       "lambda1" : lambda1,
                                                                       "lambda2" : lambda2,
                                                                       "posAlpha" : posAlpha,
                                                                       "posD" : posD,
                                                                       "clean" : clean,
                                                                       "mode" : mode,
                                                                       "modeD" : modeD
                                                                   }
                                                               }
        )

        if slot.name == 'Output':
            result[...] = processed[output_key]

    def setInSlot(self, slot, subindex, roi, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        if (slot.name == "Input") or (slot.name == "K") or (slot.name == "Gamma1") or (slot.name == "Gamma2") or\
            (slot.name == "NumThreads") or (slot.name == "Batchsize") or (slot.name == "NumIter") or\
            (slot.name == "Lambda1") or (slot.name == "Lambda2") or (slot.name == "PosAlpha") or\
            (slot.name == "PosD") or (slot.name == "Clean") or (slot.name == "Mode") or (slot.name == "ModeD"):
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"


class OpNansheGenerateDictionaryCached(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheGenerateDictionaryCached"
    category = "Pointwise"


    Input = InputSlot()
    CacheInput = InputSlot(optional=True)

    K = InputSlot(value=100, stype="int")
    Gamma1 = InputSlot(value=0.0)
    Gamma2 = InputSlot(value=0.0)
    NumThreads = InputSlot(value=1)
    Batchsize = InputSlot(value=256)
    NumIter = InputSlot(value=100, stype="int")
    Lambda1 = InputSlot(value=0.2)
    Lambda2 = InputSlot(value=0.0)
    PosAlpha = InputSlot(value=True)
    PosD = InputSlot(value=True)
    Clean = InputSlot(value=True)
    Mode = InputSlot(value=2, stype="int")
    ModeD = InputSlot(value=0, stype="int")

    CleanBlocks = OutputSlot()
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpNansheGenerateDictionaryCached, self ).__init__( *args, **kwargs )

        self.opDictionary = OpNansheGenerateDictionary(parent=self)

        self.opDictionary.K.connect(self.K)
        self.opDictionary.Gamma1.connect(self.Gamma1)
        self.opDictionary.Gamma2.connect(self.Gamma2)
        self.opDictionary.NumThreads.connect(self.NumThreads)
        self.opDictionary.Batchsize.connect(self.Batchsize)
        self.opDictionary.NumIter.connect(self.NumIter)
        self.opDictionary.Lambda1.connect(self.Lambda1)
        self.opDictionary.Lambda2.connect(self.Lambda2)
        self.opDictionary.PosAlpha.connect(self.PosAlpha)
        self.opDictionary.PosD.connect(self.PosD)
        self.opDictionary.Clean.connect(self.Clean)
        self.opDictionary.Mode.connect(self.Mode)
        self.opDictionary.ModeD.connect(self.ModeD)


        self.opCache = OpArrayCache(parent=self)
        self.opCache.fixAtCurrent.setValue(False)

        self.opDictionary.Input.connect( self.Input )
        self.opCache.Input.connect( self.opDictionary.Output )
        self.CleanBlocks.connect( self.opCache.CleanBlocks )
        self.Output.connect( self.opCache.Output )

    def setupOutputs(self):
        self.opCache.blockShape.setValue( self.opCache.Output.meta.shape )

    def setInSlot(self, slot, subindex, key, value):
        assert slot == self.CacheInput

        self.opCache.setInSlot(self.opCache.Input, subindex, key, value)

    def propagateDirty(self, slot, subindex, roi):
        pass
