import zlib
import copy
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
    
    def __init__(self, *args, **kwargs):
        super(OpColorizeLabels, self).__init__(*args, **kwargs)

        self.overrideColors = {}        

        # Pre-generate the table of data
        self.colortable = self.generateColortable(2**18)
        
    def setupOutputs(self):
        inputTags = self.Input.meta.axistags
        inputShape = self.Input.meta.shape
        self.channelIndex = inputTags.index('c')
        assert inputShape[self.channelIndex] == 1, "Input must be a single-channel label image"
                
        self.Output.meta.assignFrom(self.Input.meta)

        applyToChannel = partial(applyToElement, inputTags, 'c')
        self.Output.meta.shape = applyToChannel(inputShape, 4) # RGBA
        self.Output.meta.dtype = numpy.uint8

        newOverrideColors = self.OverrideColors.value
        if newOverrideColors != self.overrideColors:
            # Add new overrides
            for label, color in newOverrideColors.items():
                if label not in self.overrideColors:
                    self.colortable[label] = color
            # Replace removed overrides with their original random values
            for label, color in self.overrideColors.items():
                if label not in newOverrideColors:
                    self.colortable[label] = self.getRandomColor(label)

        self.overrideColors = newOverrideColors
    
    def execute(self, slot, subindex, roi, result):
        fullKey = roi.toSlice()
        resultKey = copy.copy(roi).setStartToZero().toSlice()
        
        # Input has only one channel
        thinKey = applyToElement(self.Input.meta.axistags, 'c', fullKey, slice(0,1))
        inputData = self.Input[thinKey].wait()
        dropChannelKey = applyToElement(self.Input.meta.axistags, 'c', resultKey, 0)
        channellessInput = inputData[dropChannelKey]

        # Advanced indexing with colortable applies the relabeling from labels to colors.
        # If we get an error here, we may need to expand the colortable (currently supports only 2**18 labels.)
        channelSlice = getElement(self.Input.meta.axistags, 'c', fullKey)
        return self.colortable[:, channelSlice][channellessInput]

    def generateColortable(self, size):
        table = numpy.zeros((size,4), dtype=numpy.uint8)
        for index in range( size ):
            table[index] = self.getRandomColor(index)
        return table

    def getRandomColor(self, label):
        color = numpy.zeros(4, dtype=numpy.uint8)
        # RGB
        for channel in range(3):
            color[channel] = (zlib.crc32(str(label)) >> (8*channel)) & 0xFF
        color[3] = 255 # Alpha            
        return color

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input:
            self.Output.setDirty(roi)
        elif inputSlot == self.OverrideColors:
            self.Output.setDirty(slice(None))
        else:
            assert False, "Unknown input slot"
            
