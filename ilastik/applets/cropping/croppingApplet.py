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
from opCropping import OpCroppingTopLevel
from croppingSerializer import CroppingSerializer


class CroppingApplet( StandardApplet ):
    """
    This applet demonstrates how to use the CroppingGui base class, which serves as a reusable base class for other applet GUIs that need a cropping UI.
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        # Provide a custom top-level operator before we init the base class.
        if blockDims is None:
            blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1}
        
        self.__topLevelOperator = None
        if self.topLevelOperator is None:
            self.__topLevelOperator = OpCroppingTopLevel(parent=workflow, blockDims=blockDims)
            self._serializableItems = [ CroppingSerializer( self.__topLevelOperator, projectFileGroupName ) ]

        super(CroppingApplet, self).__init__( "Cropping" )
        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from croppingGui import CroppingGui

        opCropping = self.topLevelOperator.getLane(imageLaneIndex)
        
        croppingSlots = CroppingGui.CroppingSlots()
        croppingSlots.cropInput = opCropping.CropInputs
        #croppingSlots.cropOutput = opCropping.CropImages
        croppingSlots.cropEraserValue = opCropping.CropEraserValue
        croppingSlots.cropDelete = opCropping.CropDelete
        croppingSlots.cropsAllowed = opCropping.CropsAllowedFlags
        croppingSlots.cropNames = opCropping.CropNames

        return CroppingGui( self, croppingSlots, opCropping, rawInputSlot=opCropping.InputImages )
