# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

from ilastik.applets.base.standardApplet import StandardApplet
from opLabeling import OpLabelingSingleLane
#from labelingSerializer import LabelingSerializer

class LabelingSingleLaneApplet( StandardApplet ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        super(LabelingSingleLaneApplet, self).__init__( "Simple Labeling", workflow )
            
    @property
    def singleLaneOperatorClass(self):
        return OpLabelingSingleLane

    @property
    def broadcastingSlots(self):
        return ['LabelEraserValue', 'LabelDelete']

    @property
    def dataSerializers(self):
        return [] # TODO

    def createSingleLaneGui(self, imageLaneIndex):
        from labelingGui import LabelingGui

        opLabeling = self.topLevelOperator.getLane(imageLaneIndex)
        
        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = opLabeling.LabelInput
        labelingSlots.labelOutput = opLabeling.LabelImage
        labelingSlots.labelEraserValue = opLabeling.LabelEraserValue
        labelingSlots.labelDelete = opLabeling.LabelDelete
        labelingSlots.maxLabelValue = opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = opLabeling.LabelsAllowedFlag
        
        # Special hack for labeling, required by the internal label array operator
        # Normally, it is strange to connect two same-operator input slots together like this.
        opLabeling.LabelInput.connect( opLabeling.InputImage )

        return LabelingGui( self, labelingSlots, opLabeling, rawInputSlot=opLabeling.InputImage )
