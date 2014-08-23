from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpReorderAxes, OpCompressedCache, \
    OperatorWrapper
from lazyflow.rtype import SubRegion
from lazyflow.stype import Opaque

import vigra
import numpy as np

class OpMriVolPreproc(Operator):
    name = "MRI Preprocessing"

    RawInput = InputSlot(optional=True)  # Display only

    Input = InputSlot()
    # internal output after filtering
    Output = OutputSlot()
    
    # the argmax output (single channel)
    FinalOutput = OutputSlot()

    # argmax output split in separate channels
    FanOutOutput = OutputSlot(level=1)

    Sigma = InputSlot(stype='float', value=1.0)
    Threshold = InputSlot(stype='float', value=0.0)
    
    LabelNames = OutputSlot(stype=Opaque)

    def __init__(self, *args, **kwargs):
        super(OpMriVolPreproc, self).__init__(*args, **kwargs)

        self.opCostVol = OpCostVolumeFilter(parent=self)
        self.opCostVol.Sigma.connect(self.Sigma)

        self.opCostVol.Input.connect(self.Input)
        self.Output.connect(self.opCostVol.Output)

        self.opGlobThres = OpGlobalThreshold(parent=self)
        self.opGlobThres.Threshold.connect(self.Threshold)
        self.opGlobThres.Input.connect(self.opCostVol.Output)

        self.FinalOutput.connect(self.opGlobThres.Output)

        self.opFanOut = OpFanOut(parent=self)
        self.opFanOut.Input.connect(self.opGlobThres.Output)
        self.FanOutOutput.connect(self.opFanOut.Output)

        '''
        def _debugDirty(*args, **kwargs):
            print 'Notify Dirty: ', args, kwargs
        self.FanOutOutput.notifyDirty(_debugDirty)
        '''

    def execute(self, slot, subindex, roi, destination):
        assert False, "Shouldn't get here."
        
    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            self.Output.setDirty(roi)
        if inputSlot is self.Sigma:
            self.Output.setDirty(slice(None))
            self.FanOutOutput.setDirty(slice(None))
        if inputSlot is self.Threshold:
            self.Output.setDirty(slice(None))
            
    def setupOutputs(self):
        ts = self.Input.meta.getTaggedShape()
        self.opFanOut.NumChannels.setValue(ts['c'])
        self.LabelNames.meta.shape = (ts['c'],)
        self.LabelNames.meta.dtype = np.object
        self.LabelNames.setValue(np.asarray( \
    ['Prediction {}'.format(l+1) for l in range(ts['c'])],dtype=np.object))
        

class OpCostVolumeFilter(Operator):
    name = "Cost Volume Filter"

    Input = InputSlot()
    Output = OutputSlot()
    _Output = OutputSlot() # second (private) output

    Sigma = InputSlot(stype='float', value=1.0)
    # rtype = lazyflow.rtype.Opaque e.g. for non array type output

    def __init__(self, *args, **kwargs):
        super(OpCostVolumeFilter, self).__init__(*args, **kwargs)
        # version without cache START
        # self.opIn = OpReorderAxes(parent=self)
        # self.opIn.Input.connect(self.Input)
        # self.opIn.AxisOrder.setValue('txyzc') 
        
        # self.opOut = OpReorderAxes(parent=self)
        # self.Output.connect(self.opOut.Output)
        # self.opOut.Input.connect(self._Output)
        # version without cache END

        self.opIn = OpReorderAxes(parent=self)
        self.opIn.Input.connect(self.Input)
        self.opIn.AxisOrder.setValue('txyzc') 

        self._opCache = OpCompressedCache(parent=self)
        self._opCache.Input.connect(self._Output)

        self.opOut = OpReorderAxes(parent=self)
        self.Output.connect(self.opOut.Output)
        self.opOut.Input.connect(self._opCache.Output)

        # from threading import Lock
        # self.lock= Lock()

    # not necessary for op wrapper that just propagate the output to the 
    # internally connected operator 
    def setupOutputs(self):
        self._Output.meta.assignFrom(self.opIn.Output.meta)
        self._Output.meta.dtype=np.float32
        self.opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

        self._setBlockShape()
        self._opCache.Input.setDirty(slice(None))


    def _setBlockShape(self):
        # Blockshape is the entire spatial block
        tagged_shape = self.opIn.Output.meta.getTaggedShape()
        bsize = 50
        tagged_shape['x'] = bsize
        tagged_shape['y'] = bsize
        tagged_shape['z'] = bsize

        # Blockshape must correspond to cachsetInSlot input order
        blockshape = map(lambda k: tagged_shape[k], 'txyzc')
        self._opCache.BlockShape.setValue(tuple(blockshape)) 

    @staticmethod
    def _costVolumeFilter(vol, filterSize=2.0, normalize=True):
        """
        Cost Volume Filtering: Smoothes the probabilities with a 
        Gaussian of sigma 'size', each label layer separately.
        """
        if filterSize > 0:
            for t in range(vol.shape[0]):
                for c in range(vol.shape[-1]):
                    vol[t,...,c] = vigra.gaussianSmoothing(
                        vol[t,...,c], 
                        float(filterSize))

        if normalize:
            z = np.sum(vol, axis=-1, keepdims=True)
            vol /= z

    def get_tmp_roi(self, roi):
        radius = np.ceil(self.Sigma.value*3)
        tmp_roi = SubRegion(self.opIn.Output, 
                            start = roi.start, 
                            stop = roi.stop) #roi.copy()
        offset = np.array([0, radius, radius, radius, 0], dtype=np.int)
        tmp_roi.setInputShape(self.opIn.Output.meta.shape)
        tmp_roi.expandByShape(offset, 4, 0)
        return tmp_roi

    def execute(self, slot, subindex, roi, result):
        # http://ukoethe.github.io/vigra/doc/vigra/classvigra_1_1Gaussian   
        # required filter radius for a discrete approximation 
        # of the Gaussian
        assert slot == self._Output, 'should work on cache'
        tmp_roi = self.get_tmp_roi(roi)
        tmp_data = self.opIn.Output.get(tmp_roi).wait().astype(np.float32)
        lower_bound = map(lambda x,y: x-y, roi.start, tmp_roi.start)
        upper_bound = map(lambda x,y,z: x+y-z, lower_bound,
                          roi.stop,
                          roi.start)
        # self.OpIn.Output[tmp_roi.toSlice()]
        # self.OpIn.Output(start=tmp_roi.start, stop=tmp_roi.stop)
        # always returns request object -> .wait()

        assert tmp_data.shape[-1] == \
            self.opIn.Output.meta.getTaggedShape()['c'],\
            'Not all channels are used for normalizing'
        self._costVolumeFilter(tmp_data, self.Sigma.value, normalize=True)
        '''
        with self.lock:
            print '##############################'
            print 'tmp', tmp_roi
            print 'roi', roi
            print 'L', lower_bound
            print 'U', upper_bound
            print 'Result', result.shape
            print '##############################'
        '''
        
        slicing = tuple([slice(x,y) for x,y in zip(lower_bound,upper_bound)])
        result[...] = tmp_data[slicing]
    
    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot is self.Input:
            start = np.array([0]*5)
            stop = np.array([1]*5)
            for i,a in enumerate('txyzc'):
                if a in self.Input.meta.getTaggedShape():
                    j = self.Input.meta.axistags.index(a)
                    start[i] = roi.start[j]
                    stop[i] = roi.stop[j]
            new_roi = SubRegion(self._Output, start, stop)
            tmp_roi = self.get_tmp_roi(new_roi)
            self.Output.setDirty(tmp_roi)
        if inputSlot is self.Sigma:
            self.Output.setDirty(slice(None))


class OpGlobalThreshold(Operator):
    """
    Operator that compute argmax across the channels

    TODO Integrate Threshold? (for filtering predition probabilities prior
    to argmax)
    """

    name = "Global Threshold"

    Input = InputSlot()
    Output = OutputSlot()
    
    _Output = OutputSlot() # second (private) output

    Threshold = InputSlot(optional=True, stype='float', value=0.0)

    def __init__(self, *args, **kwargs):
        super(OpGlobalThreshold, self).__init__(*args, **kwargs)
        
        self.opIn = OpReorderAxes(parent=self)
        self.opIn.Input.connect(self.Input)
        self.opIn.AxisOrder.setValue('txyzc') 

        self.opOut = OpReorderAxes(parent=self)
        self.Output.connect(self.opOut.Output)
        self.opOut.Input.connect(self._Output)

    # not necessary for op wrapper that just propagate the output to the 
    # internally connected operator 
    def setupOutputs(self):
        self._Output.meta.assignFrom(self.opIn.Output.meta)
        tagged_shape = self.opIn.Output.meta.getTaggedShape()
        tagged_shape['c'] = 1
        self._Output.meta.shape = tuple(tagged_shape.values())
        
        self.opOut.AxisOrder.setValue(self.Input.meta.getAxisKeys())

    @staticmethod
    def _globalThreshold(vol):
        """
        computes an argmax of the prediction maps (hard segmentation)
        """
        return np.argmax(vol, axis=-1)

    def execute(self, slot, subindex, roi, result):
        tmp_roi = roi.copy()
        tmp_roi.setDim(-1,0,self.opIn.Output.meta.shape[-1])
        tmp_data = self.opIn.Output.get(tmp_roi).wait().astype(np.float32)

        assert tmp_data.shape[-1] == \
            self.Input.meta.getTaggedShape()['c'],\
            'Not all channels are used for argmax'
        result[...,0]  = self._globalThreshold(tmp_data)
        
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
                
