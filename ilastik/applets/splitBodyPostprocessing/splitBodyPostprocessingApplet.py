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
from opSplitBodyPostprocessing import OpSplitBodyPostprocessing
from splitBodyPostprocessingSerializer import SplitBodyPostprocessingSerializer

class SplitBodyPostprocessingApplet( StandardApplet ):
    def __init__( self, workflow ):
        super(SplitBodyPostprocessingApplet, self).__init__("Split-body post-processing", workflow)

        self._serializer = SplitBodyPostprocessingSerializer( self.topLevelOperator, "split-body-postprocessing" )

    @property
    def singleLaneOperatorClass(self):
        return OpSplitBodyPostprocessing
    
    @property
    def singleLaneGuiClass(self):
        from splitBodyPostprocessingGui import SplitBodyPostprocessingGui
        return SplitBodyPostprocessingGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return [self._serializer]
