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

from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from PyQt4.QtGui import QPixmap, QIcon, QColor

from ilastik.widgets.featureTableWidget import FeatureTableWidget, FeatureEntry

class PyFeatureTableWidgetPlugin(QPyDesignerCustomWidgetPlugin):

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
        t = FeatureTableWidget(parent)
        t.createTableForFeatureDlg( \
            {"Color": [FeatureEntry("Banana")],
             "Edge": [FeatureEntry("Mango"),
                      FeatureEntry("Cherry")] \
            }, \
            [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0] \
        )
        return t
    
    def name(self):
        return "FeatureTableWidget"

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
               '<widget class="FeatureTableWidget" name=\"featureTableWidget\">\n'
               "</widget>\n"
               )
    
    def includeFile(self):
        return "ilastik.widgets.tableWidget"
 
