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
import glob
import numpy
import os
import uuid
import vigra
import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.metaDict import MetaDict
from lazyflow.operators.ioOperators import (
    OpStreamingHdf5Reader, OpStreamingHdf5SequenceReaderS, OpInputDataReader
)
from lazyflow.operators.valueProviders import OpMetadataInjector, OpZeroDefault
from lazyflow.operators.opArrayPiper import OpArrayPiper
from ilastik.utility.operatorSubView import OperatorSubView
from ilastik.applets.base.applet import DatasetConstraintError
from lazyflow.classifiers import TikTorchLazyflowClassifierFactory

from ilastik.utility import OpMultiLaneWrapper
from lazyflow.utility import PathComponents, isUrl, make_absolute


class OpCNNModelSelection(Operator):
    """
    The top-level operator for the CNN model selection applet.
    """
    name = "OpCNNModelSelection"
    category = "Top-level"

    # Inputs
    ModelPath = InputSlot()
    #HyperparametersPath = InputSlot()
    
    # Outputs
    ClassifierFactory = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpCNNModelSelection, self).__init__(*args, **kwargs)

    def execute(self, slot, subindex, roi, result):
        print('exectue')
        result =  TikTorchLazyflowClassifierFactory(self.ModelPath.wait())
        return result
        
    def setupOutputs(self):
        print('setup outputs')

    def propagateDirty(self, slot, subindex, roi):
        self.ClassifierFactory.setDirty()

    def addLane(self, laneIndex):
        pass

    def getLane(self, laneIndex):
        return OperatorSubView(self, laneIndex)

