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
# There are in total 3 possible starting points for this operator:
#
# (a) Gaussian Smoothing
#                        \
#                         |--> ArgMax
#                        /           \
# (b) Guided Filter -----             \
#                                      |--> (PostProcessing) TODO
#                                     /
# (c) OpenGM -------------------------
#
# We try to keep the code clean by using OpImplementationChoice for
# switching between [(a), (b)] and [(c)]. 
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
        self.opRevertBinarize.CCInput.connect(self.opCC.CachedOutput)

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
        if inputSlot in [self.Input, self.RawInput]:
            self.Output.setDirty(roi)
        if inputSlot in [self.Method, self.Configuration]:
            self.Output.setDirty(slice(None))
        if inputSlot is self.Threshold:
            self.Output.setDirty(slice(None))
        if inputSlot is self.ActiveChannels:
            self.Output.setDirty(slice(None))

    def setupOutputs(self):
        ts = self.Input.meta.getTaggedShape()

        ts['c'] = 1
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.shape = tuple(ts.values())
        self.Output.meta.dtype = np.uint32

        # set cache chunk shape to the whole spatial volume
        ts['t'] = 1
        blockshape = map(lambda k: ts[k], ''.join(ts.keys()))
        self._cache.BlockShape.setValue(tuple(blockshape))
        # this is not a good idea!

    def setInSlot(self, slot, subindex, roi, value):
        if slot is not self.InputHdf5:
            raise NotImplementedError("setInSlot not implemented for"
                                      "slot {}".format(slot))


class OpFanOut(Operator):
    """
    takes a label image and splits each label in its own channel
    e.g. a 3D volume (x,y,z) containig the labels [1 2 3] will be a 4D
    (x,y,z,c) data set with c=3 after opFanOut has been applied

    TODO assert that only (u)int/label images are passed to this operator

    """
    name = "Fan Out Operation"

    Input = InputSlot()
    Output = OutputSlot(level=1) # level=1 higher order slot
    _Output = OutputSlot(level=1) # second (private) output

    NumChannels = InputSlot(value=20) # default value

    def __init__(self, *args, **kwargs):
        super(OpFanOut, self).__init__(*args, **kwargs)
        
        self.opIn = OpReorderAxes(parent=self)
        self.opIn.Input.connect(self.Input)
        self.opIn.AxisOrder.setValue('txyzc') 

        self.opOut = OperatorWrapper(OpReorderAxes, parent=self, 
                                     broadcastingSlotNames=['AxisOrder'])
        self.Output.connect(self.opOut.Output)
        self.opOut.Input.connect(self._Output)

    def setupOutputs(self):
        self.opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())
        self._Output.resize( self.NumChannels.value )

        for c in range(self.NumChannels.value):
            self._Output[c].meta.assignFrom(self.opIn.Output.meta)
        
        assert len(self.Output) == self.NumChannels.value


    def execute(self, slot, subindex, roi, result):
        # subindex is a tupel with a single channel for level=1
        tmp_data = self.opIn.Output.get(roi).wait() # TODO .astype(np.uint32)
        result[:]  = tmp_data == subindex[0]
        
    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            for slot in self.Output:
                slot.setDirty(roi)


class OpFanIn(Operator):
    """
    takes level=1 (binary) input images and generates a label image
    """
    name = "Fan In Operation"
    
    Input = InputSlot(level=1)
    Output = OutputSlot()
    _Output = OutputSlot() # second (private) output

    Binaries = InputSlot(optional=True, value = False, stype='bool')

    def __init__(self, *args, **kwargs):
        super(OpFanIn, self).__init__(*args, **kwargs)
        
        self.opIn = OperatorWrapper( OpReorderAxes, parent=self,
                                     broadcastingSlotNames=['AxisOrder'])
        self.opIn.Input.connect(self.Input)
        self.opIn.AxisOrder.setValue('txyzc') 

        self.opOut = OpReorderAxes(parent=self)
        self.opOut.Input.connect(self._Output)
        self.Output.connect(self.opOut.Output)

    def setupOutputs(self):
        expected_shape = self.opIn.Output[0].meta.shape
        for slot in self.opIn.Output:
            assert expected_shape == slot.meta.shape
            
        self._Output.meta.assignFrom(self.opIn.Output[0].meta)
        tagged_shape = self.opIn.Output[0].meta.getTaggedShape()
        tagged_shape['c'] = 1 #len(self.Input)
        self._Output.meta.shape = tuple(tagged_shape.values())
        self._Output.meta.dtype=np.uint32

        self.opOut.AxisOrder.setValue(self.Input[0].meta.getAxisKeys())

    def execute(self, slot, subindex, roi, result):
        bin_out = self.Binaries.value
        result[...] = np.zeros(result.shape, dtype=np.uint32)
        for idx, slot in enumerate(self.opIn.Output):
            tmp_data = slot.get(roi).wait()
            if bin_out:
                np.place(tmp_data,tmp_data,1)
            result[tmp_data==1] = idx+1

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            self.Output.setDirty(roi)


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
        self.Output.meta.dtype = np.uint8
        self.opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

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
    Reverts the binarize option
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
        # output is a label image, therefore uint32
        self.Output.meta.dtype = np.uint32

    def execute(self, slot, subindex, roi, result):
        tmp_input = self.ArgmaxInput.get(roi).wait()
        tmp_cc = self.CCInput.get(roi).wait()
        result[...] = 0
        # all elements that are nonzero and are within a cc
        # are transfered
        # TODO faster computation?
        for cc in np.unique(tmp_cc):
            if cc == 0:
                continue
            # FIXME is this correct??
            result[tmp_cc == cc] = tmp_input[tmp_cc == cc]

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.ArgmaxInput:
            self.Output.setDirty(roi)
        if inputSlot is self.CCInput:
            self.Output.setDirty(roi)

