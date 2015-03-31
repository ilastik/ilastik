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

class OpSubModelSelection(Operator):
    """
    Given an input image and visible crop lines,
    allows selection of a SubModel.
    """
    name = "OpSubModelSelection"
    category = "Pointwise"
    
    InputImage = InputSlot()
    PredictionImage = InputSlot()
    CropInputs = InputSlot()
    CropImages = InputSlot()
    CropNames = InputSlot()
    CropsAllowedFlags = InputSlot()

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

    #def __init__( self, *args, **kwargs ):
        # Hook up Cropping Pipeline
        #self.opCropPipeline = OpMultiLaneWrapper( OpCropPipeline, parent=self, broadcastingSlotNames=['DeleteCrop'] )

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

    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.CropImage.setDirty(roi)
        elif slot.name == "PredictionImage":
            self.CropPrediction.setDirty( roi )
        else:
            self.CropImage.setDirty( slice(None) )
            self.CropPrediction.setDirty( slice(None) )

#class OpCropPipeline( Operator ):
#    RawImage = InputSlot()
#    CropInput = InputSlot()
#    DeleteCrop = InputSlot()
#
#    Output = OutputSlot()
#    nonzeroBlocks = OutputSlot()
#
#    def __init__(self, *args, **kwargs):
#        super( OpCropPipeline, self ).__init__( *args, **kwargs )
#
#        self.opCropArray = OpCompressedUserCropArray( parent=self )
#        self.opCropArray.Input.connect( self.CropInput )
#        self.opCropArray.eraser.setValue(100)
#
#        self.opCropArray.deleteCrop.connect( self.DeleteCrop )
#
#        # Connect external outputs to their internal sources
#        self.Output.connect( self.opCropArray.Output )
#        self.nonzeroBlocks.connect( self.opCropArray.nonzeroBlocks )
#
#    def setupOutputs(self):
#        tagged_shape = self.RawImage.meta.getTaggedShape()
#        tagged_shape['c'] = 1
#
#        # Aim for blocks that are roughly 1MB
#        block_shape = determineBlockShape( tagged_shape.values(), 1e6 )
#        self.opCropArray.blockShape.setValue( block_shape )
#
#    def setInSlot(self, slot, subindex, roi, value):
#        # Nothing to do here: All inputs that support __setitem__
#        #   are directly connected to internal operators.
#        pass
#
#    def execute(self, slot, subindex, roi, result):
#        assert False, "Shouldn't get here.  Output is assigned a value in setupOutputs()"
#
#    def propagateDirty(self, slot, subindex, roi):
#        # Our output changes when the input changed shape, not when it becomes dirty.
#        pass

