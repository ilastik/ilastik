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
from ilastik.applets.layerViewer import LayerViewerApplet
from opLabelImageViewer import OpLabelImageViewer

class LabelImageViewerApplet( LayerViewerApplet ):
    """
    Viewer applet for prediction probabilities produced via headless or cluster mode.
    """
    def __init__( self, workflow ):
        super(LayerViewerApplet, self).__init__("Label Image Viewer", workflow)
        self._deserializers = []

    @property
    def singleLaneOperatorClass(self):
        return OpLabelImageViewer
    
    @property
    def singleLaneGuiClass(self):
        from labelImageViewerGui import LabelImageViewerGui
        return LabelImageViewerGui

    @property
    def broadcastingSlots(self):
        return []
    
    @property
    def dataSerializers(self):
        return self._deserializers
