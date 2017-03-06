###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
from opWatershedLabeling import OpWatershedLabelingSingleLane
#from watershedLabelingSerializer import WatershedLabelingSerializer

class WatershedLabelingSingleLaneApplet( StandardApplet ):
    """
    This applet demonstrates how to use the WatershedLabelingGui base class, which serves as a reusable base class for other applet GUIs that need a watershedLabeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None, appletName="Simple WatershedLabeling" ):
        super(WatershedLabelingSingleLaneApplet, self).__init__( appletName, workflow )
            
    @property
    def singleLaneOperatorClass(self):
        return OpWatershedLabelingSingleLane

    @property
    def broadcastingSlots(self):
        return ['LabelEraserValue', 'LabelDelete']

    @property
    def dataSerializers(self):
        return [] # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from watershedLabelingGui import WatershedLabelingGui

        opWatershedLabeling = self.topLevelOperator.getLane(imageLaneIndex)
        
        watershedLabelingSlots = WatershedLabelingGui.WatershedLabelingSlots()
        watershedLabelingSlots.labelInput       = opWatershedLabeling.LabelInput
        watershedLabelingSlots.labelOutput      = opWatershedLabeling.LabelImage
        watershedLabelingSlots.labelEraserValue = opWatershedLabeling.LabelEraserValue
        watershedLabelingSlots.labelDelete      = opWatershedLabeling.LabelDelete
        watershedLabelingSlots.labelNames       = opWatershedLabeling.LabelNames
        
        # Special hack for watershedLabeling, required by the internal label array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opWatershedLabeling.LabelInput.connect( opWatershedLabeling.InputImage )

        return WatershedLabelingGui( self, watershedLabelingSlots, opWatershedLabeling, rawInputSlot=opWatershedLabeling.InputImage )
