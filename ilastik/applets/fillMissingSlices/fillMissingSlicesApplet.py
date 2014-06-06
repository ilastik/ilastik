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
from ilastik.applets.base.standardApplet import StandardApplet

from opFillMissingSlices import OpFillMissingSlices
from fillMissingSlicesSerializer import FillMissingSlicesSerializer

from lazyflow.operatorWrapper import OperatorWrapper


class FillMissingSlicesApplet(StandardApplet):
    """
    TODO: write some documentation
    """
    def __init__(self, workflow, guiName, projFileGroupName, detectionMethod):
        super(FillMissingSlicesApplet, self).__init__(guiName, workflow)
        self._operator = self.topLevelOperator
        self._operator.DetectionMethod.setValue(detectionMethod)
        self._serializableItems = \
            [FillMissingSlicesSerializer("FillMissingSlices", self._operator)]
        return

    @property
    def singleLaneOperatorClass(self):
        return OpFillMissingSlices

    @property
    def broadcastingSlots(self):
        return ["DetectionMethod", "OverloadDetector", "PatchSize", "HaloSize"]

    @property
    def singleLaneGuiClass(self):
        from fillMissingSlicesGui import FillMissingSlicesGui
        return FillMissingSlicesGui

    @property
    def dataSerializers(self):
        return self._serializableItems
