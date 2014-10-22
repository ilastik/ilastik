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

import numpy

import vigra

import nanshe
import nanshe.advanced_image_processing
import nanshe.additional_generators


class OpNansheDictionaryLearning(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheDictionaryLearning"
    category = "Pointwise"


    InputImage = InputSlot()

    K = InputSlot(value=100, stype="int")
    Gamma1 = InputSlot(value=0)
    Gamma2 = InputSlot(value=0)
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
        super( OpNansheDictionaryLearning, self ).__init__( *args, **kwargs )

    def setupOutputs(self):
        # Copy the input metadata to both outputs
        self.Output.meta.assignFrom( self.InputImage.meta )
        self.Output.meta.shape = (self.K,) + self.InputImage.meta.shape[1:]

        spatial_dims = sum([_.isSpatial() for _ in self.Output.meta.axistags])

        if spatial_dims == 1:
            self.Output.meta.axistags = vigra.AxisTags(vigra.AxisInfo.c, vigra.AxisInfo.x)
        elif spatial_dims == 2:
            self.Output.meta.axistags = vigra.AxisTags(vigra.AxisInfo.c, vigra.AxisInfo.y,
                                                                         vigra.AxisInfo.x)
        elif spatial_dims == 3:
            self.Output.meta.axistags = vigra.AxisTags(vigra.AxisInfo.c, vigra.AxisInfo.z,
                                                                         vigra.AxisInfo.y,
                                                                         vigra.AxisInfo.x)

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        key = nanshe.additional_generators.reformat_slices(key)
        new_key = list(key)
        time_slice = new_key[0]

        nanshe.additional_generators.len_slice(time_slice)

        time_slice_dist = 10000 if self.InputImage.meta.shape[0] > 10000 else self.InputImage.meta.shape[0]
        time_slice_stop = time_slice.step * time_slice_dist + time_slice.start

        time_slice = slice(0, time_slice_stop, 1)
        new_key[0] = time_slice
        tuple(new_key)

        print("new_key = " + repr(new_key))

        raw = self.InputImage[new_key].wait()
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

        processed = nanshe.advanced_image_processing.generate_dictionary(raw, **{ "spams.trainDL" :
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
        processed = processed[..., None]

        if slot.name == 'Output':
            result[...] = processed

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif (slot.name == "K") or (slot.name == "Gamma1") or (slot.name == "Gamma2") or (slot.name == "NumThreads") or\
                (slot.name == "Batchsize") or (slot.name == "NumIter") or (slot.name == "Lambda1") or\
                (slot.name == "Lambda2") or (slot.name == "PosAlpha") or (slot.name == "PosD") or\
                (slot.name == "Clean") or (slot.name == "Mode") or (slot.name == "ModeD"):
            self.Output.setDirty( slice(None) )
        else:
            assert False, "Unknown dirty input slot"
