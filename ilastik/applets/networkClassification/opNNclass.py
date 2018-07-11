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
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.classifierOperators import OpPixelwiseClassifierPredict
from lazyflow.operators import OpMultiArraySlicer2, OpValueCache
from ilastik.utility.operatorSubView import OperatorSubView


class OpNNClassification(Operator):
    """
    Top-level operator for pixel classification
    """
    name = "OpNNClassification"
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
    ModelPath = InputSlot() # Path 
    FullModel = InputSlot(value=[]) # When full model serialization is enabled
    Halo_Size = InputSlot(value=32)
    Batch_Size = InputSlot(value=3)
    SaveFullModel = InputSlot(stype='bool', value=False, nonlane=True)

    def __init__(self, *args, **kwargs):

        super(OpNNClassification, self).__init__(*args, **kwargs)

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

    def propagateDirty(self, slot, subindex, roi):
        """
        PredicitionProbabilityChannels is called when the visibility of SetupLayers is changed
        """
        self.PredictionProbabilityChannels.setDirty(slice(None))

    def addLane(self, laneIndex):
        pass

    def removeLane(self, laneIndex, finalLength):
        pass

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)































