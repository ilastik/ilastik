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
#          http://ilastik.org/license.html
###############################################################################

from __future__ import print_function
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.classifierOperators import OpPixelwiseClassifierPredict
from lazyflow.operators import OpMultiArraySlicer2
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper


class OpNNClassification(Operator): 
    """
    Top-level operator for pixel classification
    """
    name="OpNNClassification"
    category = "Top-level"

    #Graph inputs
    Classifier = InputSlot()
    InputImage = InputSlot()
    NumClasses = InputSlot()
    BlockShape = InputSlot()

    FreezePredictions = InputSlot(stype='bool', value=False, nonlane=True)

    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()
    PredictionProbabilityChannels = OutputSlot(level=1)

    #Gui only (not part of the pipeline)
    ModelPath = OutputSlot()

    def setupOutputs(self):
        self.ModelPath.meta.dtype = object
        self.ModelPath.meta.shape = (1,)


    def __init__(self, *args, **kwargs):

        super(OpNNClassification, self).__init__(*args, **kwargs)

        self.ModelPath.setValue( [] )

        self.predict = OpPixelwiseClassifierPredict(parent=self)
        self.predict.name = "OpClassifierPredict"
        self.predict.Image.connect(self.InputImage)
        self.predict.Classifier.connect(self.Classifier)
        self.predict.LabelsCount.connect(self.NumClasses)
        self.PredictionProbabilities.connect(self.predict.PMaps)

        self.prediction_cache = OpBlockedArrayCache(parent=self)
        self.prediction_cache.name = "BlockedArrayCache"
        self.prediction_cache.inputs["Input"].connect(self.predict.PMaps)
        self.prediction_cache.BlockShape.connect(self.BlockShape)
        self.prediction_cache.inputs["fixAtCurrent"].connect(self.FreezePredictions)
        self.CachedPredictionProbabilities.connect(self.prediction_cache.Output)

        self.opPredictionSlicer = OpMultiArraySlicer2(parent=self)
        self.opPredictionSlicer.name = "opPredictionSlicer"
        self.opPredictionSlicer.Input.connect(self.prediction_cache.Output)
        self.opPredictionSlicer.AxisFlag.setValue('c')
        self.PredictionProbabilityChannels.connect(self.opPredictionSlicer.Slices)

        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImage.notifyResized( inputResizeHandler )

        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self._checkConstraints( index )
                # self.setupCaches( multislot.index(slot) )
            # multislot[index].notifyReady(handleInputReady)
                
        self.InputImage.notifyInserted( handleNewInputImage )

    def _checkConstraints(self, laneIndex):
        """
        Ensure that all input images have the same number of channels.
        """
        if not self.InputImage[laneIndex].ready():
            return

        thisLaneTaggedShape = self.InputImage[laneIndex].meta.getTaggedShape()

        # Find a different lane and use it for comparison
        validShape = thisLaneTaggedShape
        for i, slot in enumerate(self.InputImage):
            if slot.ready() and i != laneIndex:
                validShape = slot.meta.getTaggedShape()
                break

        if 't' in thisLaneTaggedShape:
            del thisLaneTaggedShape['t']
        if 't' in validShape:
            del validShape['t']

        if validShape['c'] != thisLaneTaggedShape['c']:
            raise DatasetConstraintError(
                 "Network Classification",
                 "All input images must have the same number of channels.  "\
                 "Your new image has {} channel(s), but your other images have {} channel(s)."\
                 .format( thisLaneTaggedShape['c'], validShape['c'] ) )
            
        if len(validShape) != len(thisLaneTaggedShape):
            raise DatasetConstraintError(
                 "Network Classification",
                 "All input images must have the same dimensionality.  "\
                 "Your new image has {} dimensions (including channel), but your other images have {} dimensions."\
                 .format( len(thisLaneTaggedShape), len(validShape) ) )
        
        mask_slot = self.PredictionMasks[laneIndex]
        input_shape = self.InputImage[laneIndex].meta.shape
        if mask_slot.ready() and mask_slot.meta.shape[:-1] != input_shape[:-1]:
            raise DatasetConstraintError(
                 "Network Classification",
                 "If you supply a prediction mask, it must have the same shape as the input image."\
                 "Your input image has shape {}, but your mask has shape {}."\
                 .format( input_shape, mask_slot.meta.shape ) )


    def propagateDirty(self, slot, subindex, roi):

        self.PredictionProbabilityChannels.setDirty(slice(None))

    def addLane(self, laneIndex):
        numLanes = len(self.InputImage)
        assert numLanes == laneIndex, "Image lanes must be appended."        
        self.InputImage.resize(numLanes+1)
        pass

    def removeLane(self, laneIndex, finalLength):
        self.InputImage.removeSlot(laneIndex, finalLength)
        pass

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)































