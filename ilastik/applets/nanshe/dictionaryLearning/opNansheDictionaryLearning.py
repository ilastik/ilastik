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

from ilastik.applets.nanshe.dictionaryLearning.opNansheGenerateDictionary import OpNansheGenerateDictionaryCached
from ilastik.applets.nanshe.dictionaryLearning.opNansheNormalizeData import OpNansheNormalizeData

import numpy

import vigra

import nanshe
import nanshe.nanshe
import nanshe.nanshe.advanced_image_processing
import nanshe.nanshe.additional_generators


class OpNansheDictionaryLearning(Operator):
    """
    Given an input image and max/min bounds,
    masks out (i.e. sets to zero) all pixels that fall outside the bounds.
    """
    name = "OpNansheDictionaryLearning"
    category = "Pointwise"


    InputImage = InputSlot()
    CacheInput = InputSlot(optional=True)


    Ord = InputSlot(value=2.0)

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
        super( OpNansheDictionaryLearning, self ).__init__( *args, **kwargs )

        self.opNansheNormalizeData = OpNansheNormalizeData(parent=self)
        self.opNansheNormalizeData.Ord.connect(self.Ord)


        self.opDictionary = OpNansheGenerateDictionaryCached(parent=self)

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

        self.opDictionary.CacheInput.connect(self.CacheInput)
        self.CleanBlocks.connect(self.opDictionary.CleanBlocks)

        self.opNansheNormalizeData.InputImage.connect( self.InputImage )
        self.opDictionary.InputImage.connect( self.opNansheNormalizeData.Output )
        self.Output.connect( self.opDictionary.Output )

    def setInSlot(self, slot, subindex, key, value):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass
