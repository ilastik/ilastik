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
from opCropping import OpCroppingSingleLane
#from croppingSerializer import CroppingSerializer

class CroppingSingleLaneApplet( StandardApplet ):
    """
    This applet demonstrates how to use the CroppingGui base class, which serves as a reusable base class for other applet GUIs that need a cropping UI.
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None, appletName="Simple Cropping" ):
        super(CroppingSingleLaneApplet, self).__init__( appletName, workflow )
            
    @property
    def singleLaneOperatorClass(self):
        return OpCroppingSingleLane

    @property
    def broadcastingSlots(self):
        return ['CropEraserValue', 'CropDelete']

    @property
    def dataSerializers(self):
        return [] # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from croppingGui import CroppingGui

        opCropping = self.topLevelOperator.getLane(imageLaneIndex)
        
        croppingSlots = CroppingGui.CroppingSlots()
        croppingSlots.cropInput = opCropping.CropInput
        croppingSlots.cropOutput = opCropping.CropImage
        croppingSlots.cropEraserValue = opCropping.CropEraserValue
        croppingSlots.cropDelete = opCropping.CropDelete
        croppingSlots.cropsAllowed = opCropping.CropsAllowedFlag
        croppingSlots.cropNames = opCropping.CropNames
        
        # Special hack for cropping, required by the internal crop array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opCropping.CropInput.connect( opCropping.InputImage )

        return CroppingGui( self, croppingSlots, opCropping, rawInputSlot=opCroping.InputImage )
