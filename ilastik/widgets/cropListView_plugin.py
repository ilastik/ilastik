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

from ilastik.widgets.cropListView import CropListView
from ilastik.widgets.cropListModel import Crop, CropListModel

class PyCropListViewPlugin(QPyDesignerCustomWidgetPlugin):

    def __init__(self, parent = None):
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False
        print ".........................................> loading PyCropListViewPlugin"

    def initialize(self, core):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized
    
    def createWidget(self, parent):
        red   = QColor(255,0,0)
        green = QColor(0,255,0)
        blue  = QColor(0,0,255)
        model = CropListModel([Crop("Crop 1", red),
                                Crop("Crop 2", green),
                                Crop("Crop 3", blue)])
        a=CropListView(parent)
        a.setModel(model)
        return a
    
    def name(self):
        return "CropListView"

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
               '<widget class="CropListView" name=\"cropListView\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "ilastik.widgets.cropListView"
 