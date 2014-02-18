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
from opDeviationFromMean import OpDeviationFromMean
from deviationFromMeanSerializer import DeviationFromMeanSerializer

class DeviationFromMeanApplet( StandardApplet ):
    """
    This applet serves as an example multi-image-lane applet.
    The GUI is not aware of multiple image lanes (it is written as if the applet were single-image only).
    The top-level operator is explicitly multi-image (it is not wrapped in an operatorwrapper).
    """
    def __init__( self, workflow, projectFileGroupName ):
        # Multi-image operator
        self._topLevelOperator = OpDeviationFromMean(parent=workflow)
        
        # Base class
        super(DeviationFromMeanApplet, self).__init__( "Deviation From Mean", workflow )
        self._serializableItems = [ DeviationFromMeanSerializer( self._topLevelOperator, projectFileGroupName ) ]
            
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def singleLaneGuiClass(self):
        from deviationFromMeanGui import DeviationFromMeanGui
        return DeviationFromMeanGui

    @property
    def dataSerializers(self):
        return self._serializableItems


