from collections import OrderedDict

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpReorderAxes, OpCompressedCache, \
    OpLabelVolume, OpFilterLabels, OperatorWrapper
from lazyflow.rtype import SubRegion
from lazyflow.stype import Opaque

from opSmoothing import OpSmoothing

import vigra
import numpy as np


class OpMriVolFilter(Operator):
    name = "MRI Processing"

    RawInput = InputSlot(optional=True)  # Display only
    Input = InputSlot()

    SmoothingMethod = InputSlot(value='gaussian')
    Configuration = InputSlot(value={'sigma': 0.0})

    Threshold = InputSlot(stype='int', value=3000)
    ActiveChannels = InputSlot(stype=Opaque)

    # internal output after filtering
    Smoothed = OutputSlot()

    # the argmax output (single channel)
    ArgmaxOutput = OutputSlot()

    Output = OutputSlot()
    CachedOutput = OutputSlot() 

    # TODO introduce InputSlot for LabelNames
    LabelNames = OutputSlot(stype=Opaque)
    ActiveChannelsOut = OutputSlot(stype=Opaque)

    # slots for serialization
    InputHdf5 = InputSlot(optional=True)
    CleanBlocks = OutputSlot()
    OutputHdf5 = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpMriVolFilter, self).__init__(*args, **kwargs)

        self._cache = OpCompressedCache(parent=self)
        self._cache.name = "OpMriVol.OutputCache"

        self.opSmoothing = OpSmoothing(parent=self)
        self.opSmoothing.Configuration.connect(self.Configuration)
        self.opSmoothing.Method.connect(self.SmoothingMethod)
        self.opSmoothing.Input.connect(self.Input)

        self.Smoothed.connect(self.opSmoothing.CachedOutput)

        self.opGlobThres = OpMriArgmax(parent=self)
        self.opGlobThres.Threshold.connect(self.Threshold)
        self.opGlobThres.Input.connect(self.Smoothed)

        self.ArgmaxOutput.connect(self.opGlobThres.Output)

        self.opBinarize = OpMriBinarizeImage(parent=self)
        self.opBinarize.Input.connect(self.opGlobThres.Output)
        self.opBinarize.ActiveChannels.connect(self.ActiveChannels)

        self.opCC = OpLabelVolume(parent=self)
        self.opCC.Input.connect(self.opBinarize.Output)

        # Filters CCs
        self.opFilter = OpFilterLabels(parent=self )
        self.opFilter.Input.connect(self.opCC.CachedOutput )
        self.opFilter.MinLabelSize.connect( self.Threshold )
        self.opFilter.BinaryOut.setValue(False)

        self._cache.Input.connect(self.opFilter.Output) 
        # FIXME shouldn't this be connected to a cached version of self.Output?
        self.CachedOutput.connect(self._cache.Output)
        self._cache.InputHdf5.connect(self.InputHdf5)
        self.CleanBlocks.connect(self._cache.CleanBlocks)
        self.OutputHdf5.connect(self._cache.OutputHdf5)

        self.opRevertBinarize = OpMriRevertBinarize( parent=self)
        self.opRevertBinarize.ArgmaxInput.connect(self.opGlobThres.Output)
        self.opRevertBinarize.CCInput.connect(self.CachedOutput)

        self.Output.connect( self.opRevertBinarize.Output )
        self.ActiveChannelsOut.connect( self.ActiveChannels )

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot in [self.Input, self.RawInput]:
            self.Output.setDirty(roi)
        if inputSlot in [self.SmoothingMethod, self.Configuration]:
            self.Output.setDirty(slice(None))
        if inputSlot is self.Threshold:
            self.Output.setDirty(slice(None))
        if inputSlot is self.ActiveChannels:
            self.Output.setDirty(slice(None))

    def setupOutputs(self):
        ts = self.Input.meta.getTaggedShape()
        self.LabelNames.meta.shape = (ts['c'],)
        self.LabelNames.meta.dtype = np.object
        self.LabelNames.setValue(
            np.asarray(
                ['Prediction {}'.format(l+1) for l in range(ts['c'])],
                dtype=np.object))

        ts['c'] = 1
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.shape = tuple(ts.values())
        self.Output.meta.dtype = np.uint32

        self.ArgmaxOutput.meta.assignFrom(self.Input.meta)
        self.ArgmaxOutput.meta.shape = tuple(ts.values())
        self.ArgmaxOutput.meta.dtype = np.uint32

        # set cache chunk shape to the whole spatial volume
        ts['t'] = 1
        blockshape = map(lambda k: ts[k], ''.join(ts.keys()))
        self._cache.BlockShape.setValue(tuple(blockshape))
        self._cache.Input.setDirty(slice(None))

        self.ActiveChannelsOut.meta.assignFrom(self.ActiveChannels.meta)

    def setInSlot(self, slot, subindex, roi, value):
        if slot is not self.InputHdf5:
            raise NotImplementedError("setInSlot not implemented for"
                                      "slot {}".format(slot))


class OpMriArgmax(Operator):
    """
    Operator that compute argmax across the channels

    TODO Integrate Threshold? (for filtering predition probabilities prior
    to argmax)
    """

    name = "Argmax Operator"

    Input = InputSlot()
    Output = OutputSlot()

    _Output = OutputSlot() # second (private) output

    Threshold = InputSlot(optional=True, stype='float', value=0.0)

    def __init__(self, *args, **kwargs):
        super(OpMriArgmax, self).__init__(*args, **kwargs)

        self.opIn = OpReorderAxes(parent=self)
        self.opIn.Input.connect(self.Input)
        self.opIn.AxisOrder.setValue('txyzc') 

        self.opOut = OpReorderAxes(parent=self)
        self.Output.connect(self.opOut.Output)
        self.opOut.Input.connect(self._Output)

    def setupOutputs(self):
        self._Output.meta.assignFrom(self.opIn.Output.meta)
        tagged_shape = self.opIn.Output.meta.getTaggedShape()
        tagged_shape['c'] = 1
        self._Output.meta.shape = tuple(tagged_shape.values())

        self.opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

    @staticmethod
    def _globalArgmax(vol):
        """
        computes an argmax of the prediction maps (hard segmentation)
        """
        return np.argmax(vol, axis=-1)+1

    def execute(self, slot, subindex, roi, result):
        tmp_roi = roi.copy()
        tmp_roi.setDim(-1,0,self.opIn.Output.meta.shape[-1])
        tmp_data = self.opIn.Output.get(tmp_roi).wait().astype(np.float32)

        assert tmp_data.shape[-1] == \
            self.Input.meta.getTaggedShape()['c'],\
            'Not all channels are used for argmax'
        result[...,0]  = self._globalArgmax(tmp_data)
        
    def propagateDirty(self, inputSlot, subindex, roi):
         if inputSlot is self.Input:
             self.Output.setDirty(roi)
         if inputSlot is self.Threshold:
             self.Output.setDirty(slice(None))


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
    """

    name = "MRI Binarize Image"
    
    Input = InputSlot()
    ActiveChannels = InputSlot(stype=Opaque) # ActiveChannels

    Output = OutputSlot()
    _Output = OutputSlot() # second (private) output

    
    def __init__(self, *args, **kwargs):
        super(OpMriBinarizeImage, self).__init__(*args, **kwargs)
        
        self.opIn = OpReorderAxes(parent=self)
        self.opIn.Input.connect(self.Input)
        self.opIn.AxisOrder.setValue('txyzc') 

        self.opOut = OpReorderAxes(parent=self)
        self.Output.connect(self.opOut.Output)
        self.opOut.Input.connect(self._Output)

    def setupOutputs(self):
        self._Output.meta.assignFrom(self.opIn.Output.meta)
        self._Output.meta.dtype=np.uint32
        self.opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

    def execute(self, slot, subindex, roi, result):
        # TODO faster computation?
        tmp_data = self.opIn.Output.get(roi).wait()
        result[...] = np.ones(result.shape, dtype=np.uint32)
        # result[tmp_data==self.BackgroundChannel.value] = 0
        for idx, active in enumerate(self.ActiveChannels.value):
            if active == 0: # and idx != self.BackgroundChannel.value:
                result[tmp_data==idx+1] = 0

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            self.Output.setDirty(roi)
        if inputSlot is self.ActiveChannels:
            self.Output.setDirty(slice(None))

class OpMriRevertBinarize(Operator):
    """
    Reverts the binarize option
    """
    # Argmax Input
    ArgmaxInput = InputSlot()
    CCInput = InputSlot()

    Output = OutputSlot()
    # second (private) output 
    _Output = OutputSlot()
   
    def __init__(self, *args, **kwargs):
        super(OpMriRevertBinarize, self).__init__(*args, **kwargs)
        
        self.opIn = OpReorderAxes(parent=self)
        self.opIn.Input.connect(self.ArgmaxInput)
        self.opIn.AxisOrder.setValue('txyzc') 

        self.opInCC = OpReorderAxes(parent=self)
        self.opInCC.Input.connect(self.CCInput)
        self.opInCC.AxisOrder.setValue('txyzc') 

        self.opOut = OpReorderAxes(parent=self)
        self.Output.connect(self.opOut.Output)
        self.opOut.Input.connect(self._Output)

    def setupOutputs(self):
        self._Output.meta.assignFrom(self.opIn.Output.meta)
        self._Output.meta.dtype=np.uint32
        self.opOut.AxisOrder.setValue(self.ArgmaxInput.meta.getAxisKeys())

    def execute(self, slot, subindex, roi, result):
        tmp_input = self.opIn.Output.get(roi).wait()
        tmp_cc = self.opInCC.Output.get(roi).wait()
        result[...] = np.zeros(tmp_input.shape, dtype=np.uint32)
        # all elements that are nonzero and are within a cc 
        # are transfered
        # TODO faster computation?
        for cc in np.unique(tmp_cc): 
            if cc == 0:
                continue
            result[tmp_cc==cc] = tmp_input[tmp_cc==cc]

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.ArgmaxInput:
            self.Output.setDirty( roi )
        if inputSlot is self.CCInput:
            self.Output.setDirty( roi )

