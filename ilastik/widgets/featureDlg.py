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


from PyQt4.QtGui import QDialog
import sys        
import os
from PyQt4 import uic
import qimage2ndarray
import featureTableWidget
import preView

class FeatureDlg(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        # init
        # ------------------------------------------------

        localDir = os.path.split(os.path.abspath(__file__))[0]
        uic.loadUi(localDir+"/featureDialog.ui", self)
        
        #the preview is currently shown in a separate window
        self.preView = preView.PreView()
        self.cancel.clicked.connect(self.reject)
        self.ok.clicked.connect(self.accept)
        
        self.featureTableWidget.brushSizeChanged.connect(self.preView.setFilledBrsuh)
                
    # methods
    # ------------------------------------------------
    
    @property
    def selectedFeatureBoolMatrix(self):
        """Return the bool matrix of features that the user selected."""
        return self.featureTableWidget.createSelectedFeaturesBoolMatrix()

    @selectedFeatureBoolMatrix.setter
    def selectedFeatureBoolMatrix(self, newMatrix):
        """Populate the table of selected features with the provided matrix."""
        self.featureTableWidget.setSelectedFeatureBoolMatrix(newMatrix)
    
    def createFeatureTable(self, features, sigmas, brushNames=None):
        self.featureTableWidget.createTableForFeatureDlg(features, sigmas, brushNames)
    
    def setImageToPreView(self, image):
        self.preView.setVisible(image is not None)
        if image is not None:
            self.preView.setPreviewImage(qimage2ndarray.array2qimage(image))
        
    def setIconsToTableWidget(self, checked, partiallyChecked, unchecked):
        self.featureTableWidget.itemDelegate.setCheckBoxIcons(checked, partiallyChecked, unchecked)

        
if __name__ == "__main__":
    #make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt4.QtGui import QApplication
    from featureTableWidget import FeatureEntry
    
    app = QApplication(sys.argv)
    
    #app.setStyle("windows")
    #app.setStyle("motif")
    #app.setStyle("cde")
    #app.setStyle("plastique")
    #app.setStyle("macintosh")
    #app.setStyle("cleanlooks")
    
    ex = FeatureDlg()
    ex.createFeatureTable([("Color", [FeatureEntry("Banananananaana")]), ("Edge", [FeatureEntry("Mango"), FeatureEntry("Cherry")])], [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0])
    ex.setWindowTitle("FeatureTest")
    ex.setImageToPreView(None)
    ex.exec_()
    
    app.exec_()
    
