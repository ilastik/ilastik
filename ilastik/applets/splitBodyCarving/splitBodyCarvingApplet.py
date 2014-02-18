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

from ilastik.workflows.carving.carvingApplet import CarvingApplet
from ilastik.utility import OpMultiLaneWrapper

from opSplitBodyCarving import OpSplitBodyCarving
from splitBodyCarvingSerializer import SplitBodyCarvingSerializer

class SplitBodyCarvingApplet(CarvingApplet):
    
    workflowName = "Split-body Carving"
    
    def __init__(self, workflow, *args, **kwargs):
        self._topLevelOperator = OpMultiLaneWrapper( OpSplitBodyCarving, parent=workflow )
        super(SplitBodyCarvingApplet, self).__init__(workflow, *args, **kwargs)
        self._serializers = None
        
    @property
    def dataSerializers(self):
        if self._serializers is None:
            self._serializers = [ SplitBodyCarvingSerializer(self.topLevelOperator, self._projectFileGroupName) ]
        return self._serializers
    
    def createSingleLaneGui(self, laneIndex):
        """
        Override from base class.
        """
        from splitBodyCarvingGui import SplitBodyCarvingGui
        # Get a single-lane view of the top-level operator
        topLevelOperatorView = self.topLevelOperator.getLane(laneIndex)

        gui = SplitBodyCarvingGui( topLevelOperatorView )

        gui.minLabelNumber = 2
        gui.maxLabelNumber = 2

        return gui
