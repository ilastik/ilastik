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
from opLayerViewer import OpLayerViewer

class LayerViewerApplet( StandardApplet ):
    """
    This applet can be used as a simple viewer of raw image data.  
    Its main purpose is to provide a simple example of how to use the LayerViewerGui, 
    which is intended to be used as a base class for most other applet GUIs.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("Viewer", workflow)
        self._serializableItems = []

    @property
    def singleLaneOperatorClass(self):
        return OpLayerViewer
    
    @property
    def singleLaneGuiClass(self):
        from layerViewerGui import LayerViewerGui
        return LayerViewerGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return self._serializableItems
