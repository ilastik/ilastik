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
##############################################################################

import numpy as np
import vigra

from opObjectsSegment import OpObjectsSegment

from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.operators.valueProviders import OpArrayCache
from lazyflow.operator import Operator
from lazyflow.rtype import SubRegion


class OpGraphCutSegmentation(Operator):
    RawInput = InputSlot()  # FIXME is this neccessary?
    InputImage = InputSlot()
    LabelImage = InputSlot()
    Beta = InputSlot(value=.2)
    Channel = InputSlot(value=0)

    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpGraphCutSegmentation, self).__init__(*args, **kwargs)

        op = OpObjectsSegment(parent=self)

        op.Prediction.connect(self.InputImage)
        op.LabelImage.connect(self.LabelImage)
        op.Beta.connect(self.Beta)
        op.Channel.connect(self.Channel)

        self.CachedOutput.connect(op.CachedOutput)

        self._op = op

        self._filled = False

    def setupOutputs(self):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass  # Nothing to do

    def execute(self, slot, subindex, roi, result):
        assert False, "Shuld not get here"
