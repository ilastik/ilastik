from lazyflow.graph import Operator, InputSlot, OutputSlot

import numpy
from functools import partial
import random

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
    Output = OutputSlot()

    generator = random.Random()
    
    @classmethod
    def choose_color(cls, x, channel):
        # Seed a random number generator with the value.
        # This will produce a deterministic sequence of random-looking colors
        
        # TODO: This assumes that seeding the generator is cheap.  Is that true?
        # If not, replace with a faster hash algorithm of some sort (e.g. something like a prbs or pyfasthash)
        cls.generator.seed(x)
        return (cls.generator.randint(0, 1 << 24) >> (8*channel)) & 0xFF

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
        self.Output.meta.shape = applyToChannel(inputShape, 3)
    
    def execute(self, slot, roi, result):
        fullKey = roi.toSlice()
        
        # Input has only one channel
        thinKey = applyToElement(self.Input.meta.axistags, 'c', fullKey, slice(0,1))
        
        input = self.Input[thinKey].wait()

        results = ()
        channelSlice = getElement(self.Input.meta.axistags, 'c', fullKey)
        for ch in range(channelSlice.start, channelSlice.stop):
            results += (self.vec_choose(input, ch),)

        # Stack the channels together
        output = numpy.concatenate( results, self.channelIndex )
        
        result[...] = output[...]

if __name__ == "__main__":
    from lazyflow.graph import Graph
    import numpy
    import vigra
    
    # Create a label array that's symmetric about the x-y axes
    data = numpy.indices((10,10), dtype=int).sum(0)

    assert (data == data.transpose()).all()

    data = data.view(vigra.VigraArray)
    data.axistags = vigra.defaultAxistags('xy')
    data = data.withAxes(*'txyzc')

    assert data.shape == (1,10,10,1,1)

    graph = Graph()
    op = OpColorizeLabels(graph=graph)
    op.Input.setValue(data)

    # If we transpose x-y, then the data should still be the same,
    # which implies that identical labels got identical colors
    # (i.e. we chose deterministic colors)
    colorizedData = op.Output[...].wait()
    assert colorizedData.shape == (1,10,10,1,3)
    assert (colorizedData == colorizedData.transpose(0,2,1,3,4)).all()
    
