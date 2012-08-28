import zlib
import numpy
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot

def applyToElement(axistags, tagkey, tup, f):
    """
    Axistags utility function.
    Apply f to the element of the tuple/list specified by the given axistags and key.
    """
    index = axistags.index(tagkey)
    if hasattr(f, '__call__'):
        e = f(tup[index])
    else:
        e = f
    return tup[:index] + type(tup)([e]) + tup[index+1:]

def getElement(axistags, tagkey, tup):
    """
    Axistags utility function.
    Get the value from the sequence tup according to the location of tagkey within tags.
    """
    return tup[axistags.index(tagkey)]

class OpColorizeLabels(Operator):
    name = "OpColorizeLabels"
    category = "display adaptor"
    
    Input = InputSlot()
    OverrideColors = InputSlot(stype='object', value={0 : (0,0,0,0)} )  # dict of { label : (R,G,B,A) }
                                                                        # By default, label 0 is black and transparent

    Output = OutputSlot() # 4 channels: RGBA

    @classmethod
    def choose_color(cls, x, channel, overrideColors):
        if x in overrideColors.keys():
            return overrideColors[x][channel]
        else:
            # Use crc32 as a deterministic pseudo-random number generator
            return (zlib.crc32(str(x)) >> (8*channel)) & 0xFF

    def __init__(self, *args, **kwargs):
        super(OpColorizeLabels, self).__init__(*args, **kwargs)
        self.vec_choose = numpy.vectorize(OpColorizeLabels.choose_color, otypes=[numpy.uint8])
        
    def setupOutputs(self):
        inputTags = self.Input.meta.axistags
        inputShape = self.Input.meta.shape
        self.channelIndex = inputTags.index('c')
        assert inputShape[self.channelIndex] == 1, "Input must be a single-channel label image"
                
        self.Output.meta.assignFrom(self.Input.meta)

        applyToChannel = partial(applyToElement, inputTags, 'c')
        self.Output.meta.shape = applyToChannel(inputShape, 4) # RGBA
    
    def execute(self, slot, roi, result):
        fullKey = roi.toSlice()
        
        # Input has only one channel
        thinKey = applyToElement(self.Input.meta.axistags, 'c', fullKey, slice(0,1))
        
        inputData = self.Input[thinKey].wait()

        results = ()
        channelSlice = getElement(self.Input.meta.axistags, 'c', fullKey)
        for ch in range(channelSlice.start, channelSlice.stop):
            results += (self.vec_choose(inputData, ch, self.OverrideColors.value),)

        # Stack the channels together
        output = numpy.concatenate( results, self.channelIndex )
        
        result[...] = output[...]

    def propagateDirty(self, inputSlot, roi):
        if inputSlot == self.Input:
            self.Output.setDirty(roi)
        elif inputSlot == self.OverrideColors:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot"
            
