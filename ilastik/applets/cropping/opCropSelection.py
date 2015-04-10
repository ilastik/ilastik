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
from ilastik.utility import OpMultiLaneWrapper

import numpy
from lazyflow.operators import OpCompressedUserCropArray
#from lazyflow.operators import OpValueCache, OpTrainClassifierBlocked, OpClassifierPredict,\
#                               OpSlicedBlockedArrayCache, OpMultiArraySlicer2, \
#                               OpPixelOperator, OpMaxChannelIndicatorOperator, OpCompressedUserLabelArray
class OpCropSelection(Operator):
    """
    Given an input image and visible crop lines,
    allows selection of a crop.
    """
    name = "OpCropSelection"
    category = "Pointwise"
    
    InputImage = InputSlot()
    PredictionImage = InputSlot()

    CropInputs = InputSlot(optional = True)
    #CropImages = InputSlot()
    #CropNames = InputSlot()
    CropsAllowedFlags = InputSlot(optional = True)

    MinValueT = InputSlot(value=0)
    MaxValueT = InputSlot(value=0)
    MinValueX = InputSlot(value=0)
    MaxValueX = InputSlot(value=0)
    MinValueY = InputSlot(value=0)
    MaxValueY = InputSlot(value=0)
    MinValueZ = InputSlot(value=0)
    MaxValueZ = InputSlot(value=0)

    CropImage = OutputSlot()
    CropPrediction = OutputSlot()


    CropOutput = OutputSlot()
    # GUI-only (not part of the pipeline, but saved to the project)
    CropNames = OutputSlot()
    CropColors = OutputSlot()
    PmapColors = OutputSlot()
    NumClasses = OutputSlot()





    #def __init__( self, *args, **kwargs ):
    def __init__( self, parent=None, graph=None ):
        super(OpCropSelection, self).__init__(parent=parent, graph=graph)
        # Hook up Cropping Pipeline
        #self.opCropPipeline = OpMultiLaneWrapper( OpCropPipeline, parent=self, broadcastingSlotNames=['DeleteCrop'] )
        self.opCropPipeline = OpCropPipeline(parent=self)#, broadcastingSlotNames=['DeleteCrop'] )
        self.CropNames.setValue( [] )
        self.CropColors.setValue( [] )
        self.PmapColors.setValue( [] )
        #self.CropInputs.connect( self.InputImage )

        def _updateNumClasses(*args):
            """
            When the number of labels changes, we MUST make sure that the prediction image changes its shape (the number of channels).
            Since setupOutputs is not called for mere dirty notifications, but is called in response to setValue(),
            we use this function to call setValue().
            """
            numClasses = len(self.CropNames.value)
            #self.opTrain.MaxLabel.setValue( numClasses )
            #self.opPredictionPipeline.NumClasses.setValue( numClasses )
            self.NumClasses.setValue( numClasses )
        self.CropNames.notifyDirty( _updateNumClasses )

    def setupOutputs(self):
        self.CropImage.meta.assignFrom( self.InputImage.meta )
        self.CropPrediction.meta.assignFrom( self.PredictionImage.meta )
        self._MinValueT=self.MinValueT.value
        self._MaxValueT=self.MaxValueT.value
        self._MinValueX=self.MinValueX.value
        self._MaxValueX=self.MaxValueX.value
        self._MinValueY=self.MinValueY.value
        self._MaxValueY=self.MaxValueY.value
        self._MinValueZ=self.MinValueZ.value
        self._MaxValueZ=self.MaxValueZ.value

        self.CropNames.meta.dtype = object
        self.CropNames.meta.shape = (1,)
        #self.CropNames.setValue([])

        self.CropColors.meta.dtype = object
        self.CropColors.meta.shape = (1,)
        #self.CropColors.setValue([])

        self.PmapColors.meta.dtype = object
        self.PmapColors.meta.shape = (1,)
        #self.PmapColors.setValue([])


    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()

        if slot.name == 'CropImage':
            raw = self.InputImage[key].wait()
            mask = numpy.ones_like(raw)
            result[...] = mask * raw
        if slot.name == 'CropPrediction':
            raw = self.PredictionImage[key].wait()
            mask = numpy.ones_like(raw)
            result[...] = numpy.logical_not(mask) * raw

        if slot.name == 'CropInputs':
            raw = self.InputImage[key].wait()
            mask = numpy.ones_like(raw)
            result[...] = mask * raw

        #if slot.name == 'CropNames':
        #    cropNames = self.CropNames[key].wait()
        #    result[...] = cropNames

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.CropImage.setDirty(roi)
        elif slot.name == "PredictionImage":
            self.CropPrediction.setDirty( roi )
        elif slot.name == "CropNames":
            self.CropNames.setDirty( roi )
        else:
            self.CropImage.setDirty( slice(None) )
            self.CropPrediction.setDirty( slice(None) )
            self.CropNames.setDirty( slice(None) )

class OpCropPipeline( Operator ):
    RawImage = InputSlot()
    CropInput = InputSlot()
    DeleteCrop = InputSlot()

    Output = OutputSlot()
    nonzeroBlocks = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpCropPipeline, self ).__init__( *args, **kwargs )

        self.opCropArray = OpCompressedUserCropArray( parent=self )
        self.opCropArray.Input.connect( self.CropInput )
        self.opCropArray.eraser.setValue(100)

        self.opCropArray.deleteCrop.connect( self.DeleteCrop )

        # Connect external outputs to their internal sources
        self.Output.connect( self.opCropArray.Output )
        self.nonzeroBlocks.connect( self.opCropArray.nonzeroBlocks )

    def setupOutputs(self):
        tagged_shape = self.RawImage.meta.getTaggedShape()
        tagged_shape['c'] = 1

        # Aim for blocks that are roughly 1MB
        block_shape = determineBlockShape( tagged_shape.values(), 1e6 )
        self.opCropArray.blockShape.setValue( block_shape )

    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"

    def propagateDirty(self, slot, subindex, roi):
        # Our output changes when the input changed shape, not when it becomes dirty.
        pass

