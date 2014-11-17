from collections import OrderedDict

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpReorderAxes, OpCompressedCache, \
    OpLabelVolume, OpFilterLabels, OperatorWrapper
from lazyflow.rtype import SubRegion
from lazyflow.stype import Opaque

from opSmoothing import OpSmoothedArgMax, smoothers_available
from opOpenGMFilter import OpOpenGMFilter
from opImplementationChoice import OpImplementationChoice

import vigra
import numpy as np

import logging
logger = logging.getLogger(__name__)


# top level operator of MRIVolFilter applet
# =========================================
#
# There are in total 3 possible starting points for this operator:
#
# (a) Gaussian Smoothing
#                        \
#                         |--> ArgMax
#                        /           \
# (b) Guided Filter -----             \
#                                      |--> Binarize --> Connected Components --> Size Filter --> Revert Binarize --> Cache
#                                     /
# (c) OpenGM -------------------------
#
# We try to keep the code clean by using OpImplementationChoice for
# switching between [(a), (b)] and [(c)].
#
# Why are the operators chained like that?
# ========================================
#
# * The alternatives [(a), (b)] and (c) provide different means for
#   segmentation of prediction data.
# * The segmentation is binarized before connected components analysis
#   to keep small structures inside larger ones from being filtered.
#   Only the foreground channels (as indicated by ActiveChannels) are
#   binarized to 1, the rest is assigned to background.
# * CC is prerequesite for size filter.
# * Size filter filters out unwanted prediction noise.
# * Revert binarize assigns the original class to the objects.
class OpMriVolFilter(Operator):
    name = "MRI Processing"

    RawInput = InputSlot(optional=True)  # Display only
    Input = InputSlot()

    Method = InputSlot(value='gaussian')
    Configuration = InputSlot(value={'sigma': 1.2})

    Threshold = InputSlot(stype='int', value=3000)

    # label detail slots
    ActiveChannels = InputSlot()
    LabelNames = InputSlot()

    # internal output after filtering
    Smoothed = OutputSlot()

    # internal output of CCs
    CCsOutput = OutputSlot()

    # the argmax output (single channel)
    ArgmaxOutput = OutputSlot()

    Output = OutputSlot()
    CachedOutput = OutputSlot() 

    # slots for serialization
    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot()
    OutputHdf5 = OutputSlot()

    # common interface for OpSmoothedArgMax and OpOpenGMFilter
    class _ABC(Operator):
        # shared slots
        Input = InputSlot()
        Configuration = InputSlot()
        Output = OutputSlot()

        # OpSmoothedArgMax
        Method = InputSlot(optional=True)
        Smoothed = OutputSlot()

        # OpOpenGMFilter
        RawInput = InputSlot(optional=True)

    def __init__(self, *args, **kwargs):
        super(OpMriVolFilter, self).__init__(*args, **kwargs)

        self.op = OpImplementationChoice(self._ABC, parent=self)
        d = dict()
        for k in smoothers_available:
            d[k] = OpSmoothedArgMax
        d['opengm'] = OpOpenGMFilter
        self.methods_available = d.keys()
        self.op.implementations = d
        self.op.Implementation.connect(self.Method)
        self.op.Method.connect(self.Method)
        self.op.Input.connect(self.Input)
        self.op.RawInput.connect(self.RawInput)
        self.op.Configuration.connect(self.Configuration)

        self.Smoothed.connect(self.op.Smoothed)
        self.ArgmaxOutput.connect(self.op.Output)

        self.opBinarize = OpMriBinarizeImage(parent=self)
        self.opBinarize.Input.connect(self.op.Output)
        self.opBinarize.ActiveChannels.connect(self.ActiveChannels)

        self.opCC = OpLabelVolume(parent=self)
        self.opCC.Input.connect(self.opBinarize.Output)
        self.CCsOutput.connect(self.opCC.CachedOutput)

        # Filters CCs
        self.opFilter = OpFilterLabels(parent=self)
        self.opFilter.Input.connect(self.opCC.CachedOutput)
        self.opFilter.MinLabelSize.connect(self.Threshold)
        self.opFilter.BinaryOut.setValue(False)

        self.opRevertBinarize = OpMriRevertBinarize(parent=self)
        self.opRevertBinarize.ArgmaxInput.connect(self.op.Output)
        self.opRevertBinarize.CCInput.connect(self.opFilter.Output)

        self.Output.connect(self.opRevertBinarize.Output)

        self._cache = OpCompressedCache(parent=self)
        self._cache.name = "OpMriVol.OutputCache"

        self._cache.Input.connect(self.Output)
        self._cache.InputHdf5.connect(self.InputHdf5)

        self.CleanBlocks.connect(self._cache.CleanBlocks)
        self.OutputHdf5.connect(self._cache.OutputHdf5)
        self.CachedOutput.connect(self._cache.Output)

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        # dirty handling is done by internal operators
        pass

    def setupOutputs(self):
        ts = self.Input.meta.getTaggedShape()

        # set cache chunk shape to the whole spatial volume
        # we need to use a better smoothing operator and lazy labeling if we
        # want to be lazy, probably not woth it
        ts['c'] = 1
        ts['t'] = 1
        blockshape = map(lambda k: ts[k], ts.keys())
        self._cache.BlockShape.setValue(tuple(blockshape))

    def setInSlot(self, slot, subindex, roi, value):
        if slot is not self.InputHdf5:
            raise NotImplementedError("setInSlot not implemented for"
                                      "slot {}".format(slot))


class OpMriBinarizeImage(Operator):
    """
    Takes an input label image and computes a binary image given one or
    more background classes
    all inputs have to be in 'txyzc' order
    """

    name = "MRI Binarize Image"

    Input = InputSlot()
    ActiveChannels = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMriBinarizeImage, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.Input.meta)
        # output is binary image
        self.Output.meta.dtype = np.uint8

    def execute(self, slot, subindex, roi, result):
        # TODO faster computation?
        tmp_data = self.Input.get(roi).wait()
        result[...] = 1

        # if only one channel is present, the active channel list might be
        # interpreted as a single value
        try:
            enum = enumerate(self.ActiveChannels.value)
        except TypeError:
            enum = [(0, self.ActiveChannels.value)]

        for idx, active in enum:
            if active == 0:
                result[tmp_data == idx+1] = 0

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            self.Output.setDirty(roi)
        if inputSlot is self.ActiveChannels:
            self.Output.setDirty(slice(None))


class OpMriRevertBinarize(Operator):
    """
    Reverts the binarize option. All elements that are in a non-zero
    connected component are assigned their original Argmax class.

    all inputs have to be in 'txyzc' order
    """

    # Argmax Input
    ArgmaxInput = InputSlot()
    CCInput = InputSlot()

    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMriRevertBinarize, self).__init__(*args, **kwargs)

    def setupOutputs(self):
        self.Output.meta.assignFrom(self.ArgmaxInput.meta)

    def execute(self, slot, subindex, roi, result):
        tmp_input = self.ArgmaxInput.get(roi).wait()
        tmp_cc = self.CCInput.get(roi).wait()
        result[...] = np.where(tmp_cc, tmp_input, 0)

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.ArgmaxInput:
            self.Output.setDirty(roi)
        if inputSlot is self.CCInput:
            self.Output.setDirty(roi)

