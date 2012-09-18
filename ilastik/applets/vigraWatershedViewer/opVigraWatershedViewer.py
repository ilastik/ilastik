from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiOutputSlot

from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2, OpMultiArrayMerger, OpPixelOperator

from lazyflow.operators import OpVigraWatershed, OpColorizeLabels, OpVigraLabelVolume, OpFilterLabels

import numpy
import vigra
from functools import partial
import random
import logging

class OpVigraWatershedViewer(Operator):
    name = "OpWatershedViewer"
    category = "top-level"
    
    RawImage = InputSlot(optional=True) # Displayed in the GUI (not used in pipeline)
    
    InputImage = InputSlot() # The image to be sliced and watershedded

    InputChannelIndexes = InputSlot(stype='object') # opChannelSlicer
    WatershedPadding = InputSlot() # opWatershed
    FreezeCache = InputSlot() # opWatershedCache
    CacheBlockShape = InputSlot() # opWatershedCache block shapes. Expected: tuple of (width, depth) viewing shape
    OverrideLabels = InputSlot(stype='object') # opColorizer
    SeedThresholdValue = InputSlot(optional=True) # opThreshold
    MinSeedSize = InputSlot() # opSeedLabeler
    
    WatershedLabels = OutputSlot()  # Watershed labeled output
    SummedInput = OutputSlot()      # Watershed input (for gui display)
    ColoredPixels = OutputSlot()    # Colored watershed labels (for gui display)
    ColoredSeeds = OutputSlot()     # Seeds to the watershed (for gui display)
    
    SelectedInputChannels = MultiOutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpVigraWatershedViewer, self).__init__(*args, **kwargs)
        self._seedThreshold = None
        
        # Overview Schematic
        # Example here uses input channels 0,2,5
        
        # InputChannelIndexes=[0,2,5] ---
        #                                \
        # InputImage -------------------> opChannelSlicer .Slices[0] ---\
        #                                                 .Slices[1] ----> opAverage --> opWatershed --> opWatershedCache --> opColorizer --> GUI 
        #                                                 .Slices[2] ---/               /
        #                                                                              /
        # SeedThresholdValue ---                   MinSeedSize ---                    /
        #                       \                                 \                  /
        # InputImage ----------> opThreshold --> opSeedLabeler --> opSeedFilter ----- ---> opSeedCache --> opSeedColorizer --> GUI
        
        # Create operators
        self.opChannelSlicer = OpMultiArraySlicer2(graph=self.graph, parent=self)
        self.opAverage = OpMultiArrayMerger(graph=self.graph, parent=self)
        self.opWatershed = OpVigraWatershed(graph=self.graph, parent=self)
        self.opWatershedCache = OpSlicedBlockedArrayCache(graph=self.graph, parent=self)
        self.opColorizer = OpColorizeLabels(graph=self.graph, parent=self)
        
        self.opThreshold = OpPixelOperator(graph=self.graph, parent=self)
        self.opSeedLabeler = OpVigraLabelVolume(graph=self.graph, parent=self)
        self.opSeedFilter = OpFilterLabels(graph=self.graph, parent=self)
        self.opSeedCache = OpSlicedBlockedArrayCache(graph=self.graph, parent=self)        
        self.opSeedColorizer = OpColorizeLabels(graph=self.graph, parent=self)

        # Select specific input channels
        self.opChannelSlicer.Input.connect( self.InputImage )
        self.opChannelSlicer.SliceIndexes.connect( self.InputChannelIndexes )
        self.opChannelSlicer.AxisFlag.setValue('c')

        # Average selected channels
        def average(arrays):
            if len(arrays) == 0:
                return 0
            else:
                return sum(arrays) / float(len(arrays))
        self.opAverage.MergingFunction.setValue( average )
        self.opAverage.Inputs.connect( self.opChannelSlicer.Slices )

        # Threshold for seeds
        self.opThreshold.Input.connect( self.opAverage.Output )

        # Label seeds
        self.opSeedLabeler.Input.connect( self.opThreshold.Output )

        # Filter seeds
        self.opSeedFilter.MinLabelSize.connect( self.MinSeedSize )
        self.opSeedFilter.Input.connect( self.opSeedLabeler.Output )
        
        # Cache seeds
        self.opSeedCache.fixAtCurrent.connect( self.FreezeCache )
        self.opSeedCache.Input.connect(self.opSeedFilter.Output)
        
        # Color seeds for RBG display
        self.opSeedColorizer.Input.connect( self.opSeedCache.Output )
        self.opSeedColorizer.OverrideColors.setValue( { 0: (0,0,0,0) } )

        # Compute watershed labels (possibly with seeds, see setupOutputs)
        self.opWatershed.InputImage.connect( self.opAverage.Output )
        self.opWatershed.PaddingWidth.connect( self.WatershedPadding )

        # Cache the watershed output
        self.opWatershedCache.fixAtCurrent.connect( self.FreezeCache )
        self.opWatershedCache.Input.connect(self.opWatershed.Output)

        # Colorize the watershed labels for RGB display        
        self.opColorizer.Input.connect( self.opWatershedCache.Output )
        self.opColorizer.OverrideColors.connect( self.OverrideLabels )

        # Connnect external outputs the operators that provide them
        self.ColoredPixels.connect( self.opColorizer.Output )
        self.SelectedInputChannels.connect( self.opChannelSlicer.Slices )
        self.SummedInput.connect( self.opAverage.Output )
        self.ColoredSeeds.connect( self.opSeedColorizer.Output )
        
    def setupOutputs(self):
        # User has control over cache block shape
        # Width and depth are applied to x,y, or z depending on which slicing view is being used.
        width, depth = self.CacheBlockShape.value

        ## Cache blocks
        # Inner and outer block shapes are the same.
        # We're using this cache for the "sliced" property, not the "blocked" property.
        blockDimsX = { 't' : (1,1),
                       'z' : (width,width),
                       'y' : (width,width),
                       'x' : (depth,depth),
                       'c' : (1,1) }

        blockDimsY = { 't' : (1,1),
                       'z' : (width,width),
                       'y' : (depth,depth),
                       'x' : (width,width),
                       'c' : (1,1) }

        blockDimsZ = { 't' : (1,1),
                       'z' : (depth,depth),
                       'y' : (width,width),
                       'x' : (width,width),
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

        # Seed cache has same shape as watershed cache
        self.opSeedCache.innerBlockShape.setValue( (innerBlockShapeX, innerBlockShapeY, innerBlockShapeZ) )
        self.opSeedCache.outerBlockShape.setValue( (outerBlockShapeX, outerBlockShapeY, outerBlockShapeZ) )

        # For now watershed labels always come from the X-Y slicing view
        if len(self.opWatershedCache.InnerOutputs) > 0:
            self.WatershedLabels.connect( self.opWatershedCache.InnerOutputs[2] )
        
        if self.SeedThresholdValue.ready():
            seedThreshold = self.SeedThresholdValue.value
            if not self.opWatershed.SeedImage.connected() or seedThreshold != self._seedThreshold:
                self._seedThreshold = seedThreshold
                
                self.opThreshold.Function.setValue( lambda a: (a <= seedThreshold).astype(numpy.uint8) )
                self.opWatershed.SeedImage.connect( self.opSeedFilter.Output )
        else:
            self.opWatershed.SeedImage.disconnect()
            self.opThreshold.Function.disconnect()

    def propagateDirty(self, slot, subindex, roi):
        # All outputs are directly connected to internal operators
        pass






















