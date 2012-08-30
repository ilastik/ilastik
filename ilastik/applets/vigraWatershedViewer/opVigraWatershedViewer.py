from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiOutputSlot

from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2

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
    FreezeCache = InputSlot()
    OverrideLabels = InputSlot(stype='object')
    WatershedPadding = InputSlot()
    
    ColoredPixels = OutputSlot()
    WatershedLabels = OutputSlot()
    
    InputChannels = MultiOutputSlot(level=1)
    
    def __init__(self, *args, **kwargs):
        super(OpVigraWatershedViewer, self).__init__(*args, **kwargs)
        self.opChannelSelector = OpMultiArraySlicer2(graph=self.graph, parent=self)
        self.opWatershed = OpVigraWatershed(graph=self.graph, parent=self)
        self.opWatershedCache = OpSlicedBlockedArrayCache(graph=self.graph, parent=self)
        self.opColorizer = OpColorizeLabels(graph=self.graph, parent=self)

        self.opChannelSelector.Input.connect(self.InputImage)
        self.opChannelSelector.AxisFlag.setValue('c')

        self.opWatershedCache.fixAtCurrent.connect( self.FreezeCache )
        self.opWatershedCache.Input.connect(self.opWatershed.Output)
        
        self.opColorizer.Input.connect(self.opWatershedCache.Output)
        self.opColorizer.OverrideColors.connect(self.OverrideLabels)
        self.opWatershed.PaddingWidth.connect(self.WatershedPadding)
        
        self.ColoredPixels.connect(self.opColorizer.Output)
        self.InputChannels.connect(self.opChannelSelector.Slices)
        
    def setupOutputs(self):
        # Can't make this last connection in __init__ because 
        #  opChannelSelector.Slices won't have any data until its input is ready 
        if len(self.opChannelSelector.Slices) > 0:
            self.opWatershed.InputImage.connect(self.opChannelSelector.Slices[0])

        ## Cache blocks
        # Inner and outer block shapes are the same.
        # We're using this cache for the "sliced" property, not the "blocked" property.
        blockDimsX = { 't' : (1,1),
                       'z' : (256,256),
                       'y' : (256,256),
                       'x' : (1,1),
                       'c' : (1,1) }

        blockDimsY = { 't' : (1,1),
                       'z' : (256,256),
                       'y' : (1,1),
                       'x' : (256,256),
                       'c' : (1,1) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (1,1),
                       'y' : (256,256),
                       'x' : (256,256),
                       'c' : (1,1) }

        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in self.InputImage.meta.axistags ]

        innerBlockShapeX = tuple( blockDimsX[k][0] for k in axisOrder )
        outerBlockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )

        innerBlockShapeY = tuple( blockDimsY[k][0] for k in axisOrder )
        outerBlockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )

        innerBlockShapeZ = tuple( blockDimsZ[k][0] for k in axisOrder )
        outerBlockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )

        self.opWatershedCache.innerBlockShape.setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
        self.opWatershedCache.outerBlockShape.setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )

        # For now watershed labels always come from the X-Y slicing view
        if len(self.opWatershedCache.InnerOutputs) > 0:
            self.WatershedLabels.connect( self.opWatershedCache.InnerOutputs[2] )

    def propagateDirty(self, inputSlot, roi):
        pass # Output is connected directly to an internal operator

if __name__ == "__main__":
    import lazyflow
    graph = lazyflow.graph.Graph()
    
    inputData = numpy.random.random( (1,10,100,100,1) )
    inputData *= 256
    inputData = inputData.astype('float32')
    inputData = inputData.view(vigra.VigraArray)
    inputData.axistags = vigra.defaultAxistags('txyzc')
    
    # Does this crash?
    opViewer = OpVigraWatershedViewer(graph=graph)
    opViewer.InputImage.setValue( inputData )
    opViewer.FreezeCache.setValue(False)
    result = opViewer.Output[:, 0:5, 6:20, 30:40,...].wait()
    
    





























