# Built-in
import os
import logging
import threading
from functools import partial

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4.QtGui import QMessageBox, QColor, QShortcut, QKeySequence, QPushButton, QWidget, QIcon

# HCI
from lazyflow.utility import traceLogged
from volumina.api import LazyflowSource, AlphaModulatedLayer
from volumina.utility import ShortcutManager

# ilastik
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.base.applet import ShellRequest, ControlCommand

from volumina.widgets.exportDlg import ExportDialog

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
        expDlg = ExportDialog(parent = self)
        import lazyflow
        assert isinstance(dataSource.dataSlot, lazyflow.graph.Slot), "slot is of type %r" % (type(dataSource.dataSlot))
        assert isinstance(dataSource.dataSlot.getRealOperator(), lazyflow.graph.Operator), "slot's operator is of type %r" % (type(dataSource.dataSlot.getRealOperator()))
        expDlg.setInput(dataSource.dataSlot)
        expDlg.show()
        
