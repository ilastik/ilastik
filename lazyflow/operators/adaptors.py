'''Input and output from and to other libraries resp. formats.

Volumina works with 5d array-like objects assuming the coordinate
system (time, x, y, z, channel). This module provides methods to convert other
data types to this expected format.
'''
import os
import os.path as path
import numpy as np
from lazyflow.utility.slicingtools import sl, slicing2shape
import numpy

_has_vigra = True
try:
    import vigra
except ImportError:
    _has_vigra = False


###
### lazyflow input
###
_has_lazyflow = True
try:
    from lazyflow.graph import Operator, InputSlot, OutputSlot
    from lazyflow.roi import TinyVector
except ImportError:
    _has_lazyflow = False

if _has_lazyflow and _has_vigra:

    class Op5ifyer(Operator):
        name = "Op5ifyer"
        inputSlots = [InputSlot("input"), InputSlot("order", stype='string', optional=True)]
        outputSlots = [OutputSlot("output")]

        def __init__(self, *args, **kwargs):
            super(Op5ifyer, self).__init__(*args, **kwargs)
            
            # By default, use volumina axis order
            self._axisorder = 'txyzc'
                    
        def setupOutputs(self):
            inputAxistags = self.inputs["input"].meta.axistags
            inputShape = list(self.inputs["input"].meta.shape)
            self.resSl = [slice(0,stop,None) for stop in list(self.inputs["input"].meta.shape)]
            
            if self.order.ready():
                self._axisorder = self.order.value

            outputTags = vigra.defaultAxistags( self._axisorder )
            
            inputKeys = set(tag.key for tag in inputAxistags)
            for outputTag in outputTags:
                if outputTag.key not in inputKeys:
                    #inputAxistags.insert(outputTags.index(tag.key),tag)
                    #inputShape.insert(outputTags.index(tag.key),1)
                    self.resSl.insert(outputTags.index(outputTag.key),0)
            
            outputShape = []
            for tag in outputTags:
                if tag in inputAxistags:
                    outputShape += [ inputShape[ inputAxistags.index(tag.key) ] ]
                else:
                    outputShape += [1]                
            
            self.outputs["output"].meta.dtype = self.inputs["input"].meta.dtype
            self.outputs["output"].meta.shape = tuple(outputShape)
            self.outputs["output"].meta.axistags = outputTags
            
        def execute(self, slot, subindex, roi, result):
            sl = [slice(0,roi.stop[i]-roi.start[i],None) if sl != 0\
                  else slice(0,1) for i,sl in enumerate(self.resSl)]
            
            inputTags = self.input.meta.axistags
            
            # Convert the requested slice into a slice for our input
            outSlice = roi.toSlice()
            inSlice = [None] * len(inputTags)
            for i, s in enumerate(outSlice):
                tagKey = self.output.meta.axistags[i].key
                inputAxisIndex = inputTags.index(tagKey)
                if inputAxisIndex < len(inputTags):
                    inSlice[inputAxisIndex] = s

            tmpres = self.inputs["input"][inSlice].wait()
            
            # Re-order the axis the way volumina expects them
            v = tmpres.view(vigra.VigraArray)
            v.axistags = inputTags
            result[sl] = v.withAxes(*list( self._axisorder ))
        
        def propagateDirty(self, inputSlot, subindex, roi):
            key = roi.toSlice()
            if inputSlot.name == 'input':
                # Convert the key into an output key
                inputTags = [tag.key for tag in self.input.meta.axistags]
                taggedKey = {k:v for (k,v) in zip(inputTags, key) }

                outKey = []
                outputTags = [tag.key for tag in self.output.meta.axistags]
                for tag in outputTags:
                    if tag in taggedKey.keys():
                        outKey += [taggedKey[tag]]
                    else:
                        outKey += [slice(None)]
                
                self.output.setDirty(outKey)                
            elif inputSlot.name == 'order':
                self.output.setDirty(slice(None))
            else:
                assert False, "Unknown input"

class Array5d( object ):
    '''Embed a array with dim = 3 into the volumina coordinate system.'''
    def __init__( self, array, dtype=np.uint8):
        assert(len(array.shape) == 3)
        self.a = array
        self.dtype=dtype
        
    def __getitem__( self, slicing ):
        sl3d = (slicing[1], slicing[2], slicing[3])
        ret = np.zeros(slicing2shape(slicing), dtype=self.dtype)
        ret[0,:,:,:,0] = self.a[tuple(sl3d)]
        return ret
    @property
    def shape( self ):
        return (1,) + self.a.shape + (1,)

    def astype( self, dtype):
        return Array5d( self.a, dtype )

if __name__ == "__main__":
    pass
