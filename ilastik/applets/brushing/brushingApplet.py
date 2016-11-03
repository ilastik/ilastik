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
from opBrushing import OpBrushingTopLevel
from brushingSerializer import BrushingSerializer


class BrushingApplet( StandardApplet ):
    """
    This applet demonstrates how to use the BrushingGui base class, which serves as a reusable base class for other applet GUIs that need a brushing UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        # Provide a custom top-level operator before we init the base class.
        if blockDims is None:
            blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1}
        
        self.__topLevelOperator = None
        if self.topLevelOperator is None:
            self.__topLevelOperator = OpBrushingTopLevel(parent=workflow, blockDims=blockDims)
            self._serializableItems = [ BrushingSerializer( self.__topLevelOperator, projectFileGroupName ) ]

        super(BrushingApplet, self).__init__( "Brushing" )
        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from brushingGui import BrushingGui

        opBrushing = self.topLevelOperator.getLane(imageLaneIndex)
        
        brushingSlots = BrushingGui.BrushingSlots()
        brushingSlots.labelInput = opBrushing.LabelInputs
        brushingSlots.labelOutput = opBrushing.LabelImages
        brushingSlots.labelEraserValue = opBrushing.LabelEraserValue
        brushingSlots.labelDelete = opBrushing.LabelDelete
        brushingSlots.labelNames = opBrushing.LabelNames

        return BrushingGui( self, brushingSlots, opBrushing, rawInputSlot=opBrushing.InputImages )
