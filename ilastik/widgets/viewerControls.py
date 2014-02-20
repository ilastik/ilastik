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

# Built-in
import os

# Third-party
from PyQt4 import uic
from PyQt4.QtGui import QWidget

from volumina.widgets.exportHelper import get_settings_and_export_layer

class ViewerControls(QWidget):
    def __init__(self, parent = None, model=None):
        QWidget.__init__(self, parent)
        localDir = os.path.split(__file__)[0]
        uic.loadUi( os.path.join( localDir, "viewerControls.ui" ), self )
    
    def setupConnections(self,model):
        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model.canMoveSelectedUp.connect(self.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self.DownButton.setEnabled)
        model.canDeleteSelected.connect(self.SaveButton.setEnabled)
        
        # Connect our layer movement buttons to the appropriate layerstack actions
        self.layerWidget.init(model)
        self.UpButton.clicked.connect(model.moveSelectedUp)
        self.DownButton.clicked.connect(model.moveSelectedDown)
        self.SaveButton.clicked.connect(self.export)

    def export(self):
        modelindex = self.layerWidget.currentIndex()
        model = self.layerWidget.model()
        layer = model[modelindex.row()]
        dataSource = layer.datasources[0]
        
        if not hasattr(dataSource, "dataSlot"):
            raise RuntimeError("can not export from a non-lazyflow data source (layer=%r, datasource=%r)" % (type(layer), type(dataSource)) )
        import lazyflow
        assert isinstance(dataSource.dataSlot, lazyflow.graph.Slot), "slot is of type %r" % (type(dataSource.dataSlot))
        assert isinstance(dataSource.dataSlot.getRealOperator(), lazyflow.graph.Operator), "slot's operator is of type %r" % (type(dataSource.dataSlot.getRealOperator()))
        get_settings_and_export_layer( layer, self )
        
