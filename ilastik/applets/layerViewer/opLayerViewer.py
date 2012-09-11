from lazyflow.graph import Operator, InputSlot, OutputSlot

from lazyflow.operators import OpSlicedBlockedArrayCache, OpMultiArraySlicer2, OpMultiArrayMerger, OpPixelOperator

from lazyflow.operators import OpVigraWatershed, OpColorizeLabels, OpVigraLabelVolume, OpFilterLabels

import numpy
import vigra
from functools import partial
import random
import logging

class OpLayerViewer(Operator):
    name = "OpLayerViewer"
    category = "top-level"

    RawInput = InputSlot()

