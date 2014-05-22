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
from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon, QColor

from ilastik.widgets.overlayTreeWidget import OverlayTreeWidget, OverlayEntry

class PyOverlayTreeWidgetPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent = None):
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        
    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized
    
    def createWidget(self, parent):
        o = OverlayTreeWidget(parent)
        a = OverlayEntry("Labels")
        b = OverlayEntry("Raw Data")
        p0 = OverlayEntry("Probability")
        o.addOverlaysToTreeWidget({"Classification/Labels": a, "Classification/Probability 0": p0, "Raw Data": b}, [], [], True)
    
        return o
    
    def name(self):
        return "OverlayTreeWidget"

    def group(self):
        return "ilastik widgets"
    
    def icon(self):
        return QIcon(QPixmap(16,16))
                           
    def toolTip(self):
        return ""
    
    def whatsThis(self):
        return ""
    
    def isContainer(self):
        return False
    
    def domXml(self):
        return (
               '<widget class="OverlayTreeWidget" name=\"overlayTreeWidget\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "ilastik.widgets.overlayTreeWidget"
 
