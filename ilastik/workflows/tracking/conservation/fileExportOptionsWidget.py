###############################################################################
#   volumina: volume slicing and editing library
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
import os

from PyQt4 import uic
from PyQt4.QtCore import Qt, QEvent
from PyQt4.QtGui import QWidget, QFileDialog

from volumina.utility import encode_from_qstring, decode_to_qstring

class FileExportOptionsWidget(QWidget):
    
    def __init__(self, parent):
        super( FileExportOptionsWidget, self ).__init__(parent)
        uic.loadUi( os.path.splitext(__file__)[0] + '.ui', self )

        self.filepathEdit.installEventFilter(self)

    def eventFilter(self, watched, event):
        # Apply the new path if the user presses 
        #  'enter' or clicks outside the filepathe editbox
        if watched == self.filepathEdit:
            if event.type() == QEvent.FocusOut or \
               ( event.type() == QEvent.KeyPress and \
                 ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return) ):
                newpath = self.filepathEdit.text()
                newpath = encode_from_qstring(newpath)
                self._filepathSlot.setValue( newpath )
        return False

    def initSlot(self, filepathSlot, file_filter):        
        self._filepathSlot = filepathSlot
        self.fileSelectButton.clicked.connect( self._browseForFilepath )

        self._file_filter = file_filter

    def showEvent(self, event):
        super(FileExportOptionsWidget, self).showEvent(event)
        self.updateFromSlot()
        
    def updateFromSlot(self):
        if self._filepathSlot.ready():
            file_path = self._filepathSlot.value
            file_path = os.path.splitext(file_path)[0]
            self.filepathEdit.setText( decode_to_qstring(file_path) )
            
            # Re-configure the slot in case we changed the extension
            self._filepathSlot.setValue( file_path )
    
    def _browseForFilepath(self):
        starting_dir = os.path.expanduser("~")
        if self._filepathSlot.ready():
            starting_dir = os.path.split(self._filepathSlot.value)[-1]
        
        dlg = QFileDialog( self, "Export Location", starting_dir, self._file_filter )
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if not dlg.exec_():
            return
        
        exportPath = encode_from_qstring( dlg.selectedFiles()[0] )
        self._filepathSlot.setValue( exportPath )
        self.filepathEdit.setText( decode_to_qstring(exportPath) )

if __name__ == "__main__":
    from PyQt4.QtGui import QApplication
    from lazyflow.graph import Graph
    from lazyflow.operators.ioOperators import OpNpyWriter

    op = OpNpyWriter(graph=Graph())

    app = QApplication([])
    w = FileExportOptionsWidget(None)
    w.initSlot(op.Filepath)
    w.show()
    app.exec_()

    print "Selected Filepath: {}".format( op.Filepath.value )


