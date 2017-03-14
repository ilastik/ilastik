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
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpInterpMissingData, OpBlockedArrayCache
from lazyflow.stype import Opaque

import logging
loggerName = __name__
logger = logging.getLogger(loggerName)
logger.setLevel(logging.DEBUG)


class OpFillMissingSlicesNoCache(Operator):

    Missing = OutputSlot()
    Input = InputSlot()
    Output = OutputSlot()

    DetectionMethod = InputSlot(value='classic')
    OverloadDetector = InputSlot(value='')
    PatchSize = InputSlot(value=128)
    HaloSize = InputSlot(value=30)

    Detector = OutputSlot(stype=Opaque)

    def __init__(self, *args, **kwargs):
        super(OpFillMissingSlicesNoCache, self).__init__(*args, **kwargs)

        # Set up interpolation
        self._opInterp = OpInterpMissingData(parent=self)
        self._opInterp.InputVolume.connect(self.Input)
        self._opInterp.InputSearchDepth.setValue(100)

        self._opInterp.DetectionMethod.connect(self.DetectionMethod)

        self._opInterp.PatchSize.connect(self.PatchSize)
        self._opInterp.HaloSize.connect(self.HaloSize)

        self._opInterp.OverloadDetector.connect(self.OverloadDetector)

        self.Output.connect(self._opInterp.Output)
        self.Missing.connect(self._opInterp.Missing)
        self.Detector.connect(self._opInterp.Detector)

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here"

    def propagateDirty(self, slot, subindex, roi):
        pass  # Nothing to do here.

    def isDirty(self):
        return self._opInterp.isDirty()

    def resetDirty(self):
        self._opInterp.resetDirty()

    def dumps(self):
        return self._opInterp.dumps()

    def loads(self, s):
        self._opInterp.loads(s)

    def setPrecomputedHistograms(self, histos):
        self._opInterp.detector.TrainingHistograms.setValue(histos)

    def train(self):
        self._opInterp.train()


class OpFillMissingSlices(OpFillMissingSlicesNoCache):
    """
    Extends the cacheless operator above with a cached output.
    Suitable for use in a GUI, but not in a headless workflow.
    """
    CachedOutput = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpFillMissingSlices, self).__init__(*args, **kwargs)

        # The cache serves two purposes:
        # 1) Determine shape of accesses to the interpolation operator
        # 2) Avoid duplicating work
        self._opCache = OpBlockedArrayCache(parent=self)
        self._opCache.Input.connect(self._opInterp.Output)
        self._opCache.fixAtCurrent.setValue(False)

        self.CachedOutput.connect(self._opCache.Output)

    def setupOutputs(self):
        blockdims = {'t': 1, 'x': 256, 'y': 256, 'z': 100, 'c': 1}
        blockshape = map(
            blockdims.get, self.Input.meta.getTaggedShape().keys())
        self._opCache.BlockShape.setValue(tuple(blockshape))

