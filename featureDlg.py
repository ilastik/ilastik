#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 C Sommer, C Straehle, U Koethe, FA Hamprecht. All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed


from PyQt4.QtGui import QVBoxLayout, QLabel, QHBoxLayout, QDialog, QToolButton, QGroupBox, QLayout, QSpacerItem
import numpy
import sys
import qimage2ndarray
import featureTableWidget
import preView

class FeatureDlg(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        # init
        # ------------------------------------------------
        self.setWindowTitle("Spatial Features")
        
        # widgets and layouts
        # ------------------------------------------------
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.tableAndViewGroupBox = QGroupBox(" Scales and Groups")
        self.tableAndViewGroupBox.setFlat(True)
        self.featureTableWidget = featureTableWidget.FeatureTableWidget()
        
        self.tableAndViewLayout = QVBoxLayout()
        self.tableAndViewLayout.setSizeConstraint(QLayout.SetNoConstraint)
        self.tableAndViewLayout.addWidget(self.featureTableWidget)
        
        self.viewAndButtonLayout =  QVBoxLayout() 
        self.preView = preView.PreView()
        self.viewAndButtonLayout.addWidget(self.preView)
        self.viewAndButtonLayout.addStretch()
        
        self.buttonsLayout = QHBoxLayout()
        self.memReqLabel = QLabel()
        self.buttonsLayout.addWidget(self.memReqLabel)
        self.ok = QToolButton()
        self.ok.setText("OK")
        self.ok.clicked.connect(self.on_okClicked)
        
        self.buttonsLayout.addStretch()
        self.buttonsLayout.addWidget(self.ok)
        
        self.cancel = QToolButton()
        self.cancel.setText("Cancel")
        self.cancel.clicked.connect(self.on_cancelClicked)

        self.buttonsLayout.addWidget(self.cancel)
        self.buttonsLayout.addSpacerItem(QSpacerItem(10,0))
#        self.viewAndButtonLayout.addLayout(self.buttonsLayout)
        self.viewAndButtonLayout.addSpacerItem(QSpacerItem(0,10))
#        self.tableAndViewLayout.addLayout(self.viewAndButtonLayout)
        self.tableAndViewGroupBox.setLayout(self.tableAndViewLayout)
        self.tableAndViewLayout.addStretch()
        self.tableAndViewLayout.addLayout(self.buttonsLayout)
        self.layout.addWidget(self.tableAndViewGroupBox)
        
        self.layout.setContentsMargins(0,0,0,0)
        self.tableAndViewGroupBox.setContentsMargins(4,10,4,4)
        self.tableAndViewLayout.setContentsMargins(0,10,0,0)
        
        self.featureTableWidget.brushSizeChanged.connect(self.preView.setFilledBrsuh)
        self.setMemReq()        
                
    # methods
    # ------------------------------------------------
    
    def createFeatureTable(self, features, sigmas, brushNames=None):
        self.featureTableWidget.createTableForFeatureDlg(features, sigmas, brushNames)
    
    def setImageToPreView(self, image):
        self.preView.setVisible(image is not None)
        if image is not None:
            self.preView.setPreviewImage(qimage2ndarray.array2qimage(image))
        
    def setIconsToTableWidget(self, checked, partiallyChecked, unchecked):
        self.featureTableWidget.itemDelegate.setCheckBoxIcons(checked, partiallyChecked, unchecked)
    
    def setMemReq(self):
#        featureSelectionList = self.featureTableWidget.createFeatureList()
        #TODO
        #memReq = self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)
        #self.memReqLabel.setText("%8.2f MB" % memReq)
        pass
    
    def on_okClicked(self):
#        featureSelectionList = self.featureTableWidget.createFeatureList()
#        selectedFeatureList = self.featureTableWidget.createSelectedFeatureList()
#        sigmaList = self.featureTableWidget.createSigmaList()
#        featureMgr.ilastikFeatureGroups.newGroupScaleValues = sigmaList
#        featureMgr.ilastikFeatureGroups.newSelection = selectedFeatureList
#        res = self.parent().project.dataMgr.Classification.featureMgr.setFeatureItems(featureSelectionList)
#        if res is True:
#            self.parent().labelWidget.setBorderMargin(int(self.parent().project.dataMgr.Classification.featureMgr.maxContext))
#            self.ilastik.project.dataMgr.Classification.featureMgr.computeMemoryRequirement(featureSelectionList)           
#            self.accept() 
#        else:
#            QErrorMessage.qtHandler().showMessage("Not enough Memory, please select fewer features !")
#            self.on_cancelClicked()
        self.accept()
    
    def on_cancelClicked(self):
        self.reject()
        
        
        
if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QApplication
    from featureTableWidget import FeatureEntry
    
    app = QApplication(sys.argv)
    
#    app.setStyle("windows")
#    app.setStyle("motif")
#    app.setStyle("cde")
#    app.setStyle("plastique")
#    app.setStyle("macintosh")
#    app.setStyle("cleanlooks")
    
    ex1 = FeatureDlg()
    ex1.createFeatureTable({"Color": [FeatureEntry("Banana")], "Edge": [FeatureEntry("Mango"), FeatureEntry("Cherry")]}, [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
    ex1.setWindowTitle("ex1")
    ex1.setImageToPreView((numpy.random.rand(200,200)*256).astype(numpy.uint8))
    ex1.setIconsToTableWidget("icons/CheckboxFull.png", "icons/CheckboxPartially.png", "icons/CheckboxEmpty.png")
#    print "table ", ex1.featureTableWidget.sizeHint()
#    print "horiHeader", ex1.featureTableWidget.horizontalHeader().sizeHint()
#    print "verticalHeader", ex1.featureTableWidget.verticalHeader().sizeHint().height()
#    print "HHeader columnWidth ", ex1.featureTableWidget.columnWidth(6)
#    print "tableHHeader ", ex1.featureTableWidget.horizontalHeaderItem(1).sizeHint()
#    print "tableAndViewLayout ", ex1.tableAndViewLayout.sizeHint()
#    print "tableAndViewGroupBox ", ex1.tableAndViewGroupBox.size()
#    print "layout ", ex1.layout.sizeHint()
    
    ex1.show()
    ex1.raise_()
    
    ex2 = FeatureDlg()
    ex2.createFeatureTable({"Color": [FeatureEntry("Banananananaana")], "Edge": [FeatureEntry("Mango"), FeatureEntry("Cherry")]}, [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
    ex2.setWindowTitle("ex2")
    ex2.setImageToPreView((numpy.random.rand(100,100)*256).astype(numpy.uint8))
    ex2.show()
    ex2.raise_()
    
    
    def test():
        selectedFeatures = ex1.featureTableWidget.createSelectedFeaturesBoolMatrix()
        ex2.featureTableWidget.setSelectedFeatureBoolMatrix(selectedFeatures)
            
    ex1.accepted.connect(test)
    
    
    app.exec_()       
