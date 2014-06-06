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
