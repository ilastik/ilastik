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
#Python
from builtins import range
import copy
from functools import partial

#SciPy
import numpy
#import IPython
import vigra

#lazyflow
from lazyflow.roi import determineBlockShape
from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators import OpValueCache, OpTrainClassifierBlocked, OpClassifierPredict,\
                               OpSlicedBlockedArrayCache, OpMultiArraySlicer2, \
                               OpPixelOperator, OpMaxChannelIndicatorOperator, OpCompressedUserLabelArray, OpFeatureMatrixCache
import ilastik_feature_selection
import numpy as np

from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

#ilastik
from ilastik.applets.base.applet import DatasetConstraintError
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.utility import OpMultiLaneWrapper

#from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook

class OpDomainAdaptation(Operator):
    """
    Top-level operator for domain adaptation
    """
    name="OpDomainAdaptation"
    category = "Top-level"

    # Graph inputs
    InputTarget = InputSlot(level=1) # Original input data. Used for display only
    InputSource = InputSolt(level=1, optional=True)
    InputGroundTruthSource =InputSlot(level=1, optional=True)

    LabelInputs = InputSlot(level=1, optional=True)
