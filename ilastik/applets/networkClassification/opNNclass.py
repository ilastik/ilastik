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




class OpNNClassification(Operator):

    Classifier = InputSlot()
    InputImage = InputSlot()
    NumClasses = InputSlot()
    BlockShape = InputSlot()

    # Model_List = InputSlot(stype="str", optional=True)

    FreezePredictions = InputSlot(stype='bool')

    PredictionProbabilities = OutputSlot()
    CachedPredictionProbabilities = OutputSlot()
    PredictionProbabilityChannels = OutputSlot(level=1)



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

        self.PredictionProbabilityChannels.setDirty(slice(None))


