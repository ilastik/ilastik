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
from ilastik.applets.labeling import LabelingSingleLaneApplet
from opSeededWatershed import OpSeededWatershed
#from labelingSerializer import LabelingSerializer

class SeededWatershedApplet( LabelingSingleLaneApplet ):
    """
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        super(SeededWatershedApplet, self).__init__( workflow, "Seeded Watershed", appletName="SeededWatershed" )
            
    @property
    def singleLaneOperatorClass(self):
        return OpSeededWatershed

    @property
    def broadcastingSlots(self):
        return ['LabelEraserValue', 'LabelDelete']

    @property
    def dataSerializers(self):
        return [] # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from seededWatershedGui import SeededWatershedGui

        opSeededWatershed = self.topLevelOperator.getLane(imageLaneIndex)
        
        labelingSlots = SeededWatershedGui.LabelingSlots()
        labelingSlots.labelInput = opSeededWatershed.LabelInput
        labelingSlots.labelOutput = opSeededWatershed.LabelImage
        labelingSlots.labelEraserValue = opSeededWatershed.LabelEraserValue
        labelingSlots.labelDelete = opSeededWatershed.LabelDelete
        labelingSlots.labelsAllowed = opSeededWatershed.LabelsAllowedFlag
        labelingSlots.labelNames = opSeededWatershed.LabelNames
        
        # Special hack for labeling, required by the internal label array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opSeededWatershed.LabelInput.connect( opSeededWatershed.InputImage )

        return SeededWatershedGui( self, labelingSlots, opSeededWatershed, rawInputSlot=opSeededWatershed.InputImage )
