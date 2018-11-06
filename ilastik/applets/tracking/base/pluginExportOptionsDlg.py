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

import numpy
from PyQt5 import uic
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from ilastik.plugins import pluginManager

try:
    from lazyflow.graph import Operator, InputSlot, OutputSlot
    _has_lazyflow = True
except:
    _has_lazyflow = False


#**************************************************************************
# DataExportOptionsDlg
#**************************************************************************
class PluginExportOptionsDlg(QDialog):

    def __init__(self, parent, topLevelOp=None):
        """
        Constructor.
        
        :param parent: The parent widget
        :param opDataExport: The operator to configure.  The operator is manipulated LIVE, so supply a 
                             temporary operator that can be discarded in case the user clicked 'cancel'.
                             If the user clicks 'OK', then copy the slot settings from the temporary op to your real one.
        """
        global _has_lazyflow
        assert _has_lazyflow, "This widget requires lazyflow."
        super( PluginExportOptionsDlg, self ).__init__(parent)
        uic.loadUi( os.path.splitext(__file__)[0] + '.ui', self )

        assert parent is not None or topLevelOp is not None, "Need either a parent widget or a top level operator!"

        if topLevelOp is None:
            self._topLevelOp = parent.topLevelOperator
        else:
            self._topLevelOp = topLevelOp

        self.pluginName = self._topLevelOp.SelectedPlugin.value

        # Connect the 'transaction slot'.
        # All slot changes will occur immediately
        self._topLevelOp.TransactionSlot.setValue(True)

        # connect the Ok cancel buttons
        def onOkClicked():
            if self.pluginName == 'Fiji-MaMuT':
                if self._additionalPluginArgumentsSlot.ready() and \
                        'bdvFilepath' in self._additionalPluginArgumentsSlot.value:
                    self.accept()
                else:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Please provide BigDataViewer file path")
                    msg.setWindowTitle("Fiji-MaMuT export")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
            else:
                self.accept()

        self.buttonBox.accepted.connect(onOkClicked)
        self.buttonBox.rejected.connect(self.reject)

        # Init child widgets
        self._initMetaInfoText()
        self._initFileOptions()
        self._initBdvFileSelection()

        # See self.eventFilter()
        self.filepathEdit.installEventFilter(self)
        self.installEventFilter(self)

        # plugin was selected if this dialog was opened
        if parent is not None:
            parent.pluginWasSelected = True

        # Plugin Dropdown
        availableExportPlugins = self.getAvailablePlugins()

        def onSelectedExportPluginChanged(pluginText):
            self._topLevelOp.SelectedPlugin.setValue(pluginText)
            self.pluginName = self._topLevelOp.SelectedPlugin.value
            self._initMetaInfoText()
            self._updateBdvWidget()

        self.pluginDropdown = self.comboBox
        self.pluginDropdown.addItems(availableExportPlugins)
        self.pluginDropdown.currentIndexChanged[str].connect(onSelectedExportPluginChanged)

        try:
            # select the combo box entry that represents the value from SelectedPlugin,
            # which triggers displaying the appropriate description (because of the connect above)
            selectedIndex = availableExportPlugins.index(self._topLevelOp.SelectedPlugin.value)
            self.pluginDropdown.setCurrentIndex(selectedIndex)
        except ValueError:
            pass
            # some unknown value was selected before, we ignore that case and simply go with the default selection then

    @classmethod
    def getAvailablePlugins(cls):
        '''
        Checks whether any plugins are found and whether we use the hytra backend.
        Returns the list of available plugins
        '''
        try:
            import hytra
            # export plugins only available with hytra backend
            exportPlugins = pluginManager.getPluginsOfCategory('TrackingExportFormats')
            availableExportPlugins = [pluginInfo.name for pluginInfo in exportPlugins]

            return availableExportPlugins
        except ImportError:
            return []

    def eventFilter(self, watched, event):
        # Apply the new path if the user presses 
        #  'enter' or clicks outside the filepath editbox
        if watched == self.filepathEdit:
            if event.type() == QEvent.FocusOut or \
               ( event.type() == QEvent.KeyPress and \
                 ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return) ):
                newpath = self.filepathEdit.text()
                self._filepathSlot.setValue( newpath )
                return True
        elif watched == self and \
           event.type() == QEvent.KeyPress and \
           ( event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return):
            return True
        return False


    #**************************************************************************
    # Meta-info (display only)
    #**************************************************************************
    def _initMetaInfoText(self):
        ## meta-info display widgets
        plugin = pluginManager.getPluginByName(self.pluginName, category="TrackingExportFormats")
        self.metaInfoTextEdit.setHtml(plugin.description)

    #**************************************************************************
    # File path selection and options
    #**************************************************************************
    def _initFileOptions(self):
        self._filepathSlot = self._topLevelOp.OutputFilenameFormat
        self.fileSelectButton.clicked.connect(self._browseForFilepath)

    def _initBdvFileSelection(self):
        # init BigDataViewer file selection widget
        self._additionalPluginArgumentsSlot = self._topLevelOp.AdditionalPluginArguments
        self.bdvFileSelectButton.clicked.connect(self._browseForBdvFile)
        self._updateBdvWidget()

    def _updateBdvWidget(self):
        """Show/Hide BigDataViewer file widget"""
        is_visible = self.pluginName == 'Fiji-MaMuT'
        for i in range(self.gridLayout.count()):
            widget = self.gridLayout.itemAt(i).widget()
            if widget.objectName().startswith('bdv'):
                widget.setVisible(is_visible)

    def showEvent(self, event):
        super(PluginExportOptionsDlg, self).showEvent(event)
        self.updateFromSlot()

    def updateFromSlot(self):
        if self._filepathSlot.ready():
            file_path = self._filepathSlot.value
            file_path = os.path.splitext(file_path)[0]
            self.filepathEdit.setText(file_path)

            # Re-configure the slot in case we changed the extension
            self._filepathSlot.setValue(file_path)

        if self._additionalPluginArgumentsSlot.ready():
            # handle additional arguments on a per-plugin basis
            if self.pluginName == 'Fiji-MaMuT':
                bdv_file_path = self._additionalPluginArgumentsSlot.value.get('bdvFilepath')
                self.bdvFilepath.setText(bdv_file_path)

    def _browseForFilepath(self):
        starting_dir = os.path.expanduser("~")
        if self._filepathSlot.ready():
            starting_dir = os.path.split(self._filepathSlot.value)[-1]

        dlg = QFileDialog(self, "Export Location", starting_dir)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if not dlg.exec_():
            return

        exportPath = dlg.selectedFiles()[0]
        self._filepathSlot.setValue( exportPath )
        self.filepathEdit.setText( exportPath )

    def _browseForBdvFile(self):
        """Browse for BigDataViewer file and add the its path to the additionalPluginArgumentsSlot"""
        starting_dir = self._topLevelOp.WorkingDirectory.value
        additional_args_ready = self._additionalPluginArgumentsSlot.ready()
        if additional_args_ready:
            bdv_file_path = self._additionalPluginArgumentsSlot.value.get('bdvFilepath')
            if bdv_file_path is not None:
                starting_dir = os.path.split(bdv_file_path)[0]

        dlg = QFileDialog(self, "BigDataViewer File Location", starting_dir, "XML files (*.xml)")
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        if not dlg.exec_():
            return

        bdv_file_path = dlg.selectedFiles()[0]
        if additional_args_ready:
            additional_args = self._additionalPluginArgumentsSlot.value
        else:
            additional_args = {}
        additional_args['bdvFilepath'] = bdv_file_path
        self._additionalPluginArgumentsSlot.setValue(additional_args)
        self.bdvFilepath.setText(bdv_file_path)

#**************************************************************************
# Quick debug
#**************************************************************************
if __name__ == "__main__":
    import vigra
    from PyQt5.QtWidgets import QApplication
    from lazyflow.graph import Graph
    from ilastik.applets.tracking.base.opTrackingBaseDataExport import OpTrackingBaseDataExport

    data = numpy.zeros( (10,20,30,3), dtype=numpy.float32 )
    data = vigra.taggedView(data, 'xyzc')

    availablePlugins = PluginExportOptionsDlg.getAvailablePlugins()

    g = Graph()
    op = OpTrackingBaseDataExport(graph=g)
    # op.Input.setValue(data)
    op.SelectedPlugin.setValue(availablePlugins[0])
    op.SelectedExportSource.setValue(OpTrackingBaseDataExport.PluginOnlyName)
    op.TransactionSlot.setValue(True)

    app = QApplication([])
    w = PluginExportOptionsDlg(None, topLevelOp=op)
    w.show()

    app.exec_()
