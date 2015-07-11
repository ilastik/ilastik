import copy
import collections

from PyQt4.QtCore import pyqtSignal, Qt, QEvent
from PyQt4.QtGui import QTableWidget, QDoubleSpinBox, QLineEdit 

import numpy
import vigra

RowWidgets = collections.namedtuple('RowWidgets', "resolution_box description_edit")
class AxistagsEditorWidget(QTableWidget):
    axistagsUpdated = pyqtSignal()

    def __init__(self, parent=None):
        QTableWidget.__init__(self, parent)
        self.axistags = None

    def init_ui(self):
        # Note: For some reason this initialization has to happen outside the constructor.
        # Apparently widgets loaded from a .ui file get their properties overwritten AFTER the constructor is called.
        self.horizontalHeader().setStretchLastSection(True)
        self.setColumnCount( 2 )
        self.setHorizontalHeaderLabels(["Resolution", "Description"])

    def init(self, axistags):
        self.init_ui() # See note.
        self.axistags = copy.copy(axistags)
        axiskeys = [tag.key for tag in axistags]
        self._change_axistags_order(axiskeys)
        self._refresh_widgets_from_axistags()

    def change_axis_order(self, new_axiskeys):
        """
        Update our stored axistags with the given order, but preserve  
        axis infos that are carried over from the previous tags.
        """
        old_axiskeys = [tag.key for tag in self.axistags]
        if list(new_axiskeys) != old_axiskeys:
            self._change_axistags_order(new_axiskeys)
            self._refresh_widgets_from_axistags()

    def _change_axistags_order(self, new_axiskeys):
        # Update tags
        old_axiskeys = [tag.key for tag in self.axistags]
        new_axisinfos = []
        for key in new_axiskeys:
            if key in old_axiskeys:
                new_axisinfos.append(self.axistags[key])
            else:
                new_axisinfos.append( vigra.defaultAxistags(key)[0] )
        self.axistags = vigra.AxisTags(new_axisinfos)        

    def _refresh_widgets_from_axistags(self):
        axiskeys = [tag.key for tag in self.axistags]
        row_widgets = collections.OrderedDict()
        for key in axiskeys:
            tag_info = self.axistags[key]
            
            resolution_box = QDoubleSpinBox(parent=self)
            resolution_box.setRange(0.0, numpy.finfo(numpy.float32).max)
            resolution_box.setValue( tag_info.resolution )
            resolution_box.valueChanged.connect( self._update_axistags_from_widgets )
            resolution_box.installEventFilter(self)
            
            description_edit = QLineEdit(tag_info.description, parent=self)
            description_edit.textChanged.connect( self._update_axistags_from_widgets )
            description_edit.installEventFilter(self)            

            row_widgets[key] = RowWidgets( resolution_box, description_edit )

        # Clean up old widgets (if any)
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                w = self.cellWidget( row, col )
                if w:
                    w.removeEventFilter(self)

        # Fill table with widgets
        self.setRowCount( len(row_widgets) )
        self.setVerticalHeaderLabels( row_widgets.keys() )
        for row, widgets in enumerate(row_widgets.values()):
            self.setCellWidget( row, 0, widgets.resolution_box )
            self.setCellWidget( row, 1, widgets.description_edit )

    def _update_axistags_from_widgets(self):
        axiskeys = [tag.key for tag in self.axistags]
        for row, key in enumerate(axiskeys):
            self.axistags[key].resolution = self.cellWidget(row, 0).value()
            self.axistags[key].description = str(self.cellWidget(row, 1).text())

    def eventFilter(self, widget, event):
        key_pressed = event.type() == QEvent.KeyPress
        enter_pressed = key_pressed and ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return)
        focus_changed = event.type() == QEvent.FocusOut        

        if enter_pressed or focus_changed:
            self.axistagsUpdated.emit()
        return False

if __name__ == "__main__":
    from functools import partial
    from PyQt4.QtCore import QTimer
    from PyQt4.QtGui import QApplication
    
    tags = vigra.defaultAxistags("xyzc")
    tags['x'].resolution = 2.0
    tags['y'].resolution = 2.0
    tags['c'].description = 'rgb'
    
    app = QApplication([])

    axistags_editor = AxistagsEditorWidget( None )
    axistags_editor.init(tags)
    axistags_editor.show()
    axistags_editor.adjustSize()
    axistags_editor.raise_()

    def handle_update():
        print "Axistags were updated: {}".format( axistags_editor.axistags )
    axistags_editor.axistagsUpdated.connect( handle_update )

    # Change the order after 2 seconds
    QTimer.singleShot( 2000, partial(axistags_editor.change_axis_order, "tyxc" ) )
    
    app.exec_()

    # Print the final edited values
    print "FINAL AXISTAGS:"
    print axistags_editor.axistags.toJSON()
    