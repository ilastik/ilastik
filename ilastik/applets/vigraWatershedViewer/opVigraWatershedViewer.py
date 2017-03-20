###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
from lazyflow.graph import Operator, InputSlot, OutputSlot

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

    FreezeCache = InputSlot(value=True) # opWatershedCache

    InputChannelIndexes = InputSlot(value=[0])
    WatershedPadding = InputSlot(value=10)
    OverrideLabels = InputSlot(value={ 0: (0,0,0,0) })
    SeedThresholdValue = InputSlot(value=0.0)
    MinSeedSize = InputSlot(value=0)
    CacheBlockShape = InputSlot(value=(256, 10)) # opWatershedCache block shapes. Expected: tuple of (width, depth) viewing shape

    Seeds = OutputSlot()            # For batch export
    WatershedLabels = OutputSlot()  # Watershed labeled output
    SummedInput = OutputSlot()      # Watershed input (for gui display)
    ColoredPixels = OutputSlot()    # Colored watershed labels (for gui display)
    ColoredSeeds = OutputSlot()     # Seeds to the watershed (for gui display)
    
    SelectedInputChannels = OutputSlot(level=1)

    def __init__(self, *args, **kwargs):
        super(OpVigraWatershedViewer, self).__init__(*args, **kwargs)
        self._seedThreshold = None
        
        # Overview Schematic
        # Example here uses input channels 0,2,5
        
        # InputChannelIndexes=[0,2,5] ----
        #                                 \
        # InputImage --> opChannelSlicer .Slices[0] ---\
        #                                .Slices[1] ----> opAverage -------------------------------------------------> opWatershed --> opWatershedCache --> opColorizer --> GUI
        #                                .Slices[2] ---/           \                                                  /
        #                                                           \     MinSeedSize                                /
        #                                                            \               \                              /
        #                              SeedThresholdValue ----------> opThreshold --> opSeedLabeler --> opSeedFilter --> opSeedCache --> opSeedColorizer --> GUI
        
        # Create operators
        self.opChannelSlicer = OpMultiArraySlicer2(parent=self)
        self.opAverage = OpMultiArrayMerger(parent=self)
        self.opWatershed = OpVigraWatershed(parent=self)
        self.opWatershedCache = OpSlicedBlockedArrayCache(parent=self)
        self.opColorizer = OpColorizeLabels(parent=self)
        
        self.opThreshold = OpPixelOperator(parent=self)
        self.opSeedLabeler = OpVigraLabelVolume(parent=self)
        self.opSeedFilter = OpFilterLabels(parent=self)
        self.opSeedCache = OpSlicedBlockedArrayCache(parent=self)        
        self.opSeedColorizer = OpColorizeLabels(parent=self)

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
        self.Seeds.connect( self.opSeedCache.Output )
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

        blockShapeX = tuple( blockDimsX[k][1] for k in axisOrder )
        blockShapeY = tuple( blockDimsY[k][1] for k in axisOrder )
        blockShapeZ = tuple( blockDimsZ[k][1] for k in axisOrder )
        self.opWatershedCache.BlockShape.setValue( (blockShapeX, blockShapeY, blockShapeZ) )

        # Seed cache has same shape as watershed cache
        self.opSeedCache.BlockShape.setValue( (blockShapeX, blockShapeY, blockShapeZ) )

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

if __name__ == "__main__":
    import h5py
    from lazyflow.graph import Graph
    from lazyflow.utility import Timer

    print "Reading data..."    
    prediction_path = '/tmp/STACKED_prediction.h5'
    with h5py.File( prediction_path, 'r' ) as prediction_file:
        data = prediction_file['volume/predictions'][:] #[0:50,0:50,0:50,:]

    # Scale and convert to uint8, then add axistags and drange
    data = (data*255).astype(numpy.uint8)
    data = vigra.taggedView( data, 'xyzc' )
    data.drange = (0,255)
    
    graph = Graph()
    op = OpVigraWatershedViewer(graph=graph)
    op.InputImage.setValue( data )
    op.InputChannelIndexes.setValue([0])
    op.WatershedPadding.setValue(0)
    op.FreezeCache.setValue(False)
    op.CacheBlockShape.setValue((520,520))
    op.OverrideLabels.setValue({})
    op.SeedThresholdValue.setValue(0)
    op.MinSeedSize.setValue(5)
    
    assert op.WatershedLabels.ready()
    
    print "Computing watershed..."
    with Timer() as timer:
        watershed_labels = op.opWatershed.Output[:].wait()
    print "Computing watershed took {} seconds".format( timer.seconds() )
    
    print "Saving watershed..."
    with h5py.File('/tmp/watershed_output.h5', 'w') as output_file:
        output_file.create_dataset('watershed_labels', data=watershed_labels)
    
    print "DONE."





















