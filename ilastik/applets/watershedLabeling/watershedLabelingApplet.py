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
from opWatershedLabeling import OpWatershedLabelingTopLevel
from watershedLabelingSerializer import WatershedLabelingSerializer


class WatershedLabelingApplet( StandardApplet ):
    """
    This applet demonstrates how to use the WatershedLabelingGui base class, which serves as a reusable base class for other applet GUIs that need a watershedLabeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        # Provide a custom top-level operator before we init the base class.
        if blockDims is None:
            blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1}
        
        self.__topLevelOperator = None
        if self.topLevelOperator is None:
            self.__topLevelOperator = OpWatershedLabelingTopLevel(parent=workflow, blockDims=blockDims)
            self._serializableItems = [ WatershedLabelingSerializer( self.__topLevelOperator, projectFileGroupName ) ]

        super(WatershedLabelingApplet, self).__init__( "WatershedLabeling" )
        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from watershedLabelingGui import WatershedLabelingGui

        opWatershedLabeling = self.topLevelOperator.getLane(imageLaneIndex)
        
        watershedLabelingSlots = WatershedLabelingGui.WatershedLabelingSlots()
        watershedLabelingSlots.labelInput       = opWatershedLabeling.LabelInputs
        watershedLabelingSlots.labelOutput      = opWatershedLabeling.LabelImages
        watershedLabelingSlots.labelEraserValue = opWatershedLabeling.LabelEraserValue
        watershedLabelingSlots.labelDelete      = opWatershedLabeling.LabelDelete
        watershedLabelingSlots.labelNames       = opWatershedLabeling.LabelNames

        return WatershedLabelingGui( self, watershedLabelingSlots, opWatershedLabeling, rawInputSlot=opWatershedLabeling.InputImages )
