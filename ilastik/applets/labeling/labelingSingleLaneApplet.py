from __future__ import absolute_import

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
# 		   http://ilastik.org/license.html
###############################################################################
from ilastik.applets.base.standardApplet import StandardApplet
from .opLabeling import OpLabelingSingleLane

# from labelingSerializer import LabelingSerializer


class LabelingSingleLaneApplet(StandardApplet):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.
    """

    def __init__(self, workflow, projectFileGroupName, blockDims=None, appletName="Simple Labeling"):
        super(LabelingSingleLaneApplet, self).__init__(appletName, workflow)

    @property
    def singleLaneOperatorClass(self):
        return OpLabelingSingleLane

    @property
    def broadcastingSlots(self):
        return ["LabelEraserValue", "LabelDelete"]

    @property
    def dataSerializers(self):
        return []  # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from .labelingGui import LabelingGui, LabelingSlots

        opLabeling = self.topLevelOperator.getLane(imageLaneIndex)

        labelingSlots = LabelingSlots(
            labelInput=opLabeling.LabelInput,
            labelOutput=opLabeling.LabelImage,
            labelEraserValue=opLabeling.LabelEraserValue,
            labelDelete=opLabeling.LabelDelete,
            labelNames=opLabeling.LabelNames,
        )

        # Special hack for labeling, required by the internal label array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opLabeling.LabelInput.connect(opLabeling.InputImage)

        return LabelingGui(self, labelingSlots, opLabeling, rawInputSlot=opLabeling.InputImage)
