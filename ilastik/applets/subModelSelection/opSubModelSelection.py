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

#print "----- SLTt -----> in opSubModelSelection" ###xxx

from lazyflow.graph import Operator, InputSlot, OutputSlot

import numpy

class OpSubModelSelection(Operator):
    #print " ==== SLT =====> in opModelSelectionSerializer" ###xxx
    """
    Given an input image and visible crop lines,
    allows selection of a SubModel.
    """
    name = "OpSubModelSelection"
    category = "Pointwise"
    
    InputImage = InputSlot()
    PredictionImage = InputSlot()

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

    #InvertedOutput = OutputSlot()

    def setupOutputs(self):
        #print " ==== SLT =====> in setupOutputs opSubModelSelectionSerializer" ###xxx
        # Copy the input metadata to both outputs
        self.CropImage.meta.assignFrom( self.InputImage.meta )
        self.CropPrediction.meta.assignFrom( self.PredictionImage.meta )
        #self.InvertedOutput.meta.assignFrom( self.InputImage.meta )

        # SANITY CHECK OF THESE VALUES FIRST,

        self._MinValueT=self.MinValueT.value
        #print "self.InputImage.meta.shape",self.InputImage.meta.shape
        #print "self.InputImage.meta.getTaggedShape()",self.InputImage.meta.getTaggedShape() # returns a dictionary
        #print "self.InputImage.meta.axistags",self.InputImage.meta.axistags





        self._MaxValueT=self.MaxValueT.value
        self._MinValueX=self.MinValueX.value
        self._MaxValueX=self.MaxValueX.value
        self._MinValueY=self.MinValueY.value
        self._MaxValueY=self.MaxValueY.value
        self._MinValueZ=self.MinValueZ.value
        self._MaxValueZ=self.MaxValueZ.value

        # compare the two shapes: image and prediction

        # datasetConstraintError (somwhere in ilastik) vs. assert/value error error


    def execute(self, slot, subindex, roi, result):
        print " ==== SLT =====> in execute opModelSelectionSerializer" ###xxx
        key = roi.toSlice()
        #raw = self.InputImage[key].wait()
        #mask = numpy.ones_like(raw)#logical_and(self.MinValue.value <= raw, raw <= self.MaxValue.value)
        
        if slot.name == 'CropImage':
            raw = self.InputImage[key].wait()
            mask = numpy.ones_like(raw)#<------------------------------------------
            result[...] = mask * raw ###xxxxxxxxxxxxxxx
        if slot.name == 'CropPrediction':
            raw = self.PredictionImage[key].wait()
            mask = numpy.ones_like(raw)#<--------------------------------------------------
            result[...] = numpy.logical_not(mask) * raw ###xxxxxxxxxxxxxxxxxxxxxxx

    def propagateDirty(self, slot, subindex, roi):
        #print " ==== SLT =====> in propagateDirty opSubModelSelectionSerializer" ###xxx
        if slot.name == "InputImage":
            self.CropImage.setDirty(roi)
            #self.InvertedOutput.setDirty(roi)
        elif slot.name == "PredictionImage":
            self.CropPrediction.setDirty( roi )
            #self.InvertedOutput.setDirty( slice(None) )
        else:
            self.CropImage.setDirty( slice(None) )
            self.CropPrediction.setDirty( slice(None) )
            #assert False, "Unknown dirty input slot"
