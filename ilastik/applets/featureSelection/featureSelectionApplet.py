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
from opFeatureSelection import OpFeatureSelection
from featureSelectionSerializer import FeatureSelectionSerializer, Ilastik05FeatureSelectionDeserializer

class FeatureSelectionApplet( StandardApplet ):
    """
    This applet allows the user to select sets of input data, 
    which are provided as outputs in the corresponding top-level applet operator.
    """
    def __init__( self, workflow, guiName, projectFileGroupName, filter_implementation='Original' ):
        self._filter_implementation = filter_implementation
        super(FeatureSelectionApplet, self).__init__(guiName, workflow)
        self._serializableItems = [ FeatureSelectionSerializer(self.topLevelOperator, projectFileGroupName),
                                    Ilastik05FeatureSelectionDeserializer(self.topLevelOperator) ]
        self.busy = False

    @property
    def singleLaneOperatorClass(self):
        return OpFeatureSelection

    @property
    def singleLaneOperatorInitArgs(self):
        return ((), {'filter_implementation' : self._filter_implementation})

    @property
    def broadcastingSlots(self):
        return ['Scales', 'FeatureIds', 'SelectionMatrix', 'FeatureListFilename']

    @property
    def singleLaneGuiClass(self):
        from featureSelectionGui import FeatureSelectionGui
        return FeatureSelectionGui

#    def createSingleLaneGui( self , laneIndex):
#        from featureSelectionGui import FeatureSelectionGui
#        opFeat = self.topLevelOperator.getLane(laneIndex)
#        gui = FeatureSelectionGui( opFeat, self )
#        return gui

    @property
    def dataSerializers(self):
        return self._serializableItems

