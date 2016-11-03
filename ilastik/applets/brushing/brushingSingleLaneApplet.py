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
from opBrushing import OpBrushingSingleLane
#from brushingSerializer import BrushingSerializer

class BrushingSingleLaneApplet( StandardApplet ):
    """
    This applet demonstrates how to use the BrushingGui base class, which serves as a reusable base class for other applet GUIs that need a brushing UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None, appletName="Simple Brushing" ):
        super(BrushingSingleLaneApplet, self).__init__( appletName, workflow )
            
    @property
    def singleLaneOperatorClass(self):
        return OpBrushingSingleLane

    @property
    def broadcastingSlots(self):
        return ['LabelEraserValue', 'LabelDelete']

    @property
    def dataSerializers(self):
        return [] # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from brushingGui import BrushingGui

        opBrushing = self.topLevelOperator.getLane(imageLaneIndex)
        
        brushingSlots = BrushingGui.BrushingSlots()
        brushingSlots.labelInput = opBrushing.LabelInput
        brushingSlots.labelOutput = opBrushing.LabelImage
        brushingSlots.labelEraserValue = opBrushing.LabelEraserValue
        brushingSlots.labelDelete = opBrushing.LabelDelete
        brushingSlots.labelNames = opBrushing.LabelNames
        
        # Special hack for brushing, required by the internal label array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opBrushing.LabelInput.connect( opBrushing.InputImage )

        return BrushingGui( self, brushingSlots, opBrushing, rawInputSlot=opBrushing.InputImage )
