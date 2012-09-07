from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiOutputSlot

from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2, OpMultiArrayMerger, OpPixelOperator

from lazyflow.operators import OpVigraWatershed, OpColorizeLabels, OpVigraLabelVolume

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
    InputChannelIndexes = InputSlot(stype='object')
    
    SeedThresholdValue = InputSlot(optional=True)
    #MinSeedSize = InputSlot()
    
    SummedInput = OutputSlot()
    WatershedLabels = OutputSlot()
    ColoredPixels = OutputSlot()
    
    SelectedInputChannels = MultiOutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpVigraWatershedViewer, self).__init__(*args, **kwargs)
        self._seedThreshold = None
        
        # Overview (example shown uses input channels 0,1,5)
        #
        # [0,1,5]    --> opChannelSlicer
        # InputImage --> opChannelSlicer .Slices[0] --> opAverage ---\
        #                                .Slices[1] --> opAverage ------> opWatershed --> opWatershedCache --> opColorizer
        #                                .Slices[5] --> opAverage ---/

        # Create operators
        self.opChannelSlicer = OpMultiArraySlicer2(graph=self.graph, parent=self)
        self.opAverage = OpMultiArrayMerger(graph=self.graph, parent=self)
        self.opWatershed = OpVigraWatershed(graph=self.graph, parent=self)
        self.opWatershedCache = OpSlicedBlockedArrayCache(graph=self.graph, parent=self)
        self.opColorizer = OpColorizeLabels(graph=self.graph, parent=self)
        self.opThreshold = OpPixelOperator(graph=self.graph, parent=self)
        self.opSeedLabeler = OpVigraLabelVolume(graph=self.graph, parent=self)

        self.opChannelSlicer.Input.connect( self.InputImage )
        self.opChannelSlicer.SliceIndexes.connect( self.InputChannelIndexes )
        self.opChannelSlicer.AxisFlag.setValue('c')

        def average(arrays):
            if len(arrays) == 0:
                return 0
            else:
                return sum(arrays) / float(len(arrays))

        self.opAverage.MergingFunction.setValue( average )
        self.opAverage.Inputs.connect( self.opChannelSlicer.Slices )

        self.opThreshold.Input.connect( self.opAverage.Output )

        self.opSeedLabeler.Input.connect( self.opThreshold.Output )

        self.opWatershedCache.fixAtCurrent.connect( self.FreezeCache )
        self.opWatershedCache.Input.connect(self.opWatershed.Output)
        
        self.opColorizer.Input.connect( self.opWatershedCache.Output )
        self.opColorizer.OverrideColors.connect( self.OverrideLabels )

        self.opWatershed.InputImage.connect( self.opAverage.Output )
        self.opWatershed.PaddingWidth.connect( self.WatershedPadding )

        # Connnect external outputs the operators that provide them
        self.ColoredPixels.connect( self.opColorizer.Output )
        self.SelectedInputChannels.connect( self.opChannelSlicer.Slices )
        self.SummedInput.connect( self.opAverage.Output )
        
    def setupOutputs(self):
        ## Cache blocks
        # Inner and outer block shapes are the same.
        # We're using this cache for the "sliced" property, not the "blocked" property.
        blockDimsX = { 't' : (1,1),
                       'z' : (256,256),
                       'y' : (256,256),
                       'x' : (10,10),
                       'c' : (1,1) }

        blockDimsY = { 't' : (1,1),
                       'z' : (256,256),
                       'y' : (10,10),
                       'x' : (256,256),
                       'c' : (1,1) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (10,10),
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
        
        if self.SeedThresholdValue.ready():
            seedThreshold = self.SeedThresholdValue.value
            if not self.opWatershed.SeedImage.connected() or seedThreshold != self._seedThreshold:
                self._seedThreshold = seedThreshold
                
                self.opThreshold.Function.setValue( lambda a: (a <= seedThreshold).astype(numpy.uint8) )                
                self.opWatershed.SeedImage.connect( self.opSeedLabeler.Output )
        else:
            self.opWatershed.SeedImage.disconnect()

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
    
    





























