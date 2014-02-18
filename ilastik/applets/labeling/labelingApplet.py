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
from opLabeling import OpLabelingTopLevel
from labelingSerializer import LabelingSerializer


class LabelingApplet( StandardApplet ):
    """
    This applet demonstrates how to use the LabelingGui base class, which serves as a reusable base class for other applet GUIs that need a labeling UI.  
    """
    def __init__( self, workflow, projectFileGroupName, blockDims=None ):
        # Provide a custom top-level operator before we init the base class.
        if blockDims is None:
            blockDims = {'c': 1, 'x':512, 'y': 512, 'z': 512, 't': 1}
        
        self.__topLevelOperator = None
        if self.topLevelOperator is None:
            self.__topLevelOperator = OpLabelingTopLevel(parent=workflow, blockDims=blockDims)
            self._serializableItems = [ LabelingSerializer( self.__topLevelOperator, projectFileGroupName ) ]

        super(LabelingApplet, self).__init__( "Labeling" )
        self._gui = None
            
    @property
    def topLevelOperator(self):
        return self.__topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    def createSingleLaneGui(self, imageLaneIndex):
        from labelingGui import LabelingGui

        opLabeling = self.topLevelOperator.getLane(imageLaneIndex)
        
        labelingSlots = LabelingGui.LabelingSlots()
        labelingSlots.labelInput = opLabeling.LabelInputs
        labelingSlots.labelOutput = opLabeling.LabelImages
        labelingSlots.labelEraserValue = opLabeling.LabelEraserValue
        labelingSlots.labelDelete = opLabeling.LabelDelete
        labelingSlots.maxLabelValue = opLabeling.MaxLabelValue
        labelingSlots.labelsAllowed = opLabeling.LabelsAllowedFlags

        return LabelingGui( self, labelingSlots, opLabeling, rawInputSlot=opLabeling.InputImages )
