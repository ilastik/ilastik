from lazyflow.graph import Graph, Operator, OperatorWrapper, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot

from lazyflow.operators import OpSlicedBlockedArrayCache, OpSingleChannelSelector, OpMultiArraySlicer2

from lazyflow.operators import OpVigraWatershed, OpColorizeLabels

import numpy
import vigra
from functools import partial
import random
import logging

class OpVigraWatershedViewer(Operator):
    name = "OpWatershedViewer"
    category = "top-level"
    
    InputImage = InputSlot()
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpVigraWatershedViewer, self).__init__(*args, **kwargs)
        self.opChannelSelector = OpMultiArraySlicer2(graph=self.graph, parent=self)
        self.opWatershed = OpVigraWatershed(graph=self.graph, parent=self)
        self.opWatershedCache = OpSlicedBlockedArrayCache(graph=self.graph, parent=self)
        self.opColorizer = OpColorizeLabels(graph=self.graph, parent=self)

        self.opChannelSelector.Input.connect(self.InputImage)
        self.opChannelSelector.AxisFlag.setValue('c')

        # Inner and outer block shapes are the same.
        # We're using this cache for the "sliced" property, not the "blocked" property.
        self.opWatershedCache.innerBlockShape.setValue( ((1,256,256,1,1),(1,256,1,256,1),(1,1,256,256,1)) )
        self.opWatershedCache.outerBlockShape.setValue( ((1,256,256,1,1),(1,256,1,256,1),(1,1,256,256,1)) )
        self.opWatershedCache.Input.connect(self.opWatershed.Output)
        
        self.opColorizer.Input.connect(self.opWatershedCache.Output)
        self.Output.connect(self.opColorizer.Output)
        self.opWatershed.PaddingWidth.setValue(10)
        
    def setupOutputs(self):
        # Can't make this last connection in __init__ because 
        #  opChannelSelector.Slices won't have any data until its input is ready 
        self.opWatershed.InputImage.connect(self.opChannelSelector.Slices[0])

if __name__ == "__main__":
    import lazyflow
    graph = lazyflow.graph.Graph()
    
    inputData = numpy.random.random( (1,10,100,100,1) )
    inputData *= 256
    inputData = inputData.astype('float32')
    inputData = inputData.view(vigra.VigraArray)
    inputData.axistags = vigra.defaultAxistags('txyzc')
#
#    print inputData.shape
#    
#    op = OpVigraWatershed(graph=graph)
#    op.InputImage.setValue( inputData )
#    op.PaddingWidth.setValue(10)
#    
#    result = op.Output[:, 0:5, 6:20, 30:40,...].wait()
#
#
#    
#    opColorize = OpColorizeLabels(graph=graph)
#    opColorize.Input.setValue(result)
#    colored = opColorize.Output[...].wait()
#
#    print colored.shape
#    print result.shape
#
#    print colored[:,:,:,0:10,:]

    
    # Does this crash?
    opViewer = OpWatershedViewer(graph=graph)
    opViewer.InputImage.setValue( inputData )
    result = opViewer.Output[:, 0:5, 6:20, 30:40,...].wait()
    
    





























