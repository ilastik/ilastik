# -*- coding: utf-8 -*-
from PyQt4.QtGui import QVBoxLayout, QHBoxLayout, QDialog, QToolButton, QGroupBox, QSpinBox, QSpacerItem

import treeWidget
import preView


class OverlaySelectionDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.treeGroupBox = QGroupBox("  Overlays")
        self.treeGroupBox.setFlat(True)
        self.treeGroupBox.setStyleSheet("border:0;")
        self.overlayTreeWidgetLayout = QHBoxLayout()
        self.overlayTreeWidget = treeWidget.OverlayTreeWidget()
        self.overlayTreeWidgetLayout.addWidget(self.overlayTreeWidget)
        self.overlayTreeWidget.itemSelectionChanged.connect(self.overlayTreeItemSelectionChanged)
        self.treeGroupBox.setLayout(self.overlayTreeWidgetLayout)
        
        self.preViewBoxAndButtonLayout = QVBoxLayout()
        self.preViewAndSpinBoxGroupBox = QGroupBox("  Preview")
        self.preViewAndSpinBoxGroupBox.setFlat(True)
        self.preViewAndSpinBoxGroupBox.setStyleSheet("border:0;")
        self.preViewAndSpinBoxLayout = QVBoxLayout()
        self.preView = preView.PreView()
        self.preViewAndSpinBoxLayout.addWidget(self.preView)
        
        self.spinBoxLayout = QHBoxLayout()
        self.channelSpinboxLabel = QLabel("Channel")
        self.channelSpinbox = QSpinBox(self)
        self.channelSpinbox.setEnabled(False)
#        self.connect(self.channelSpinbox, QtCore.SIGNAL('valueChanged(int)'), self.channelSpinboxValueChanged)
        self.sliceSpinboxLabel = QLabel("Slice")
        self.sliceSpinbox = QSpinBox(self)
        self.sliceSpinbox.setEnabled(False)
#        self.connect(self.sliceSpinbox, QtCore.SIGNAL('valueChanged(int)'), self.sliceSpinboxValueChanged)
        self.spinBoxLayout.addWidget(self.channelSpinboxLabel)
        self.spinBoxLayout.addWidget(self.channelSpinbox)
        self.spinBoxLayout.addStretch()
        self.spinBoxLayout.addWidget(self.sliceSpinboxLabel)
        self.spinBoxLayout.addWidget(self.sliceSpinbox)
        self.spinBoxLayout.addSpacerItem(QSpacerItem(10,0))
#        self.spinBoxLayout.addStretch()
        
        self.preViewAndSpinBoxLayout.addLayout(self.spinBoxLayout)
        self.preViewAndSpinBoxGroupBox.setLayout(self.preViewAndSpinBoxLayout)
        self.preViewBoxAndButtonLayout.addWidget(self.preViewAndSpinBoxGroupBox)
                
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(4)
        self.add_selectedButoon = QToolButton()
        self.add_selectedButoon.setText("Add Selected")
        self.add_selectedButoon.clicked.connect(self._on_add_selectedClicked)
        self.cancelButton = QToolButton()
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(self._on_cancelClicked)
        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.add_selectedButoon)
        self.buttonLayout.addWidget(self.cancelButton)
        self.buttonLayout.addSpacerItem(QSpacerItem(10,0))
        self.preViewBoxAndButtonLayout.addSpacerItem(QSpacerItem(10,10))
        self.preViewBoxAndButtonLayout.addLayout(self.buttonLayout)
        self.preViewBoxAndButtonLayout.addSpacerItem(QSpacerItem(0,10))
        
        self.layout.addWidget(self.treeGroupBox)
        self.layout.addLayout(self.preViewBoxAndButtonLayout)
        self.overlayTreeWidgetLayout.setContentsMargins(0, 10, 0, 0)
        self.treeGroupBox.setContentsMargins(4, 10, 4, 4)
        self.preViewAndSpinBoxLayout.setContentsMargins(0, 10, 0, 0)
        self.preViewAndSpinBoxGroupBox.setContentsMargins(4, 10, 4, 4)
        self.preViewBoxAndButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)
        
    # methods
    # ------------------------------------------------
    
    def overlayTreeItemSelectionChanged(self):
        currentTreeItem = self.overlayTreeWidget.currentItem()
        if isinstance(currentTreeItem, treeWidget.OverlayTreeWidgetItem):
            self.channelSpinbox.setEnabled(True)
            self.sliceSpinbox.setEnabled(True)
            self._showOverlayImageInPreView(currentTreeItem)
        else:
            self.channelSpinbox.setEnabled(False)
            self.sliceSpinbox.setEnabled(False)
            
    def _showOverlayImageInPreView(self, currentTreeItem):
        print currentTreeItem.item.name
    
    def createOverlayTreeWidget(self, overlayDict, forbiddenOverlays, preSelectedOverlays, singleOverlaySelection):
        self.overlayTreeWidget.addOverlaysToTreeWidget(overlayDict, forbiddenOverlays, preSelectedOverlays, singleOverlaySelection)
        
    def _on_add_selectedClicked(self):
        self.accept()
    
    def _on_cancelClicked(self):
        self.reject()
    
    def exec_(self):
        if QDialog.exec_(self) == QDialog.Accepted:
            return self.overlayTreeWidget.createSelectedItemList()  
        else:
            return []
    
    
    
class SimpleObject:
    def __init__(self, name):
        self.name = name

if __name__ == "__main__":
    import sys

    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import *
        
    app = QApplication(sys.argv)
    
#    app.setStyle("windows")
#    app.setStyle("motif")
#    app.setStyle("cde")
#    app.setStyle("plastique")
#    app.setStyle("macintosh")
    app.setStyle("cleanlooks")
    
    ex1 = OverlaySelectionDialog()
    a = SimpleObject("Labels")
    b = SimpleObject("Raw Data")
    ex1.createOverlayTreeWidget({"Classification/Labels/Channel A/xz": a, "Raw Data": b}, [], [], True)
    ex1.show()
    ex1.raise_()  
      
    
    app.exec_() 