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

class MultiViewerApplet( LayerViewerApplet ):
    """
    This applet can be used as a simple viewer of raw image data.  
    Its main purpose is to provide a simple example of how to use the LayerViewerGui, 
    which is intended to be used as a base class for most other applet GUIs.
    """
    def __init__( self, workflow ):
        super(MultiViewerApplet, self).__init__(workflow)
    
    @property
    def singleLaneGuiClass(self):
        from multiEditorGui import MultiEditorGui
        return MultiEditorGui
