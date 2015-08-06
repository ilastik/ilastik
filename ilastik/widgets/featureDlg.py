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
from PyQt4.QtGui import QDialog
import sys        
import os
from PyQt4 import uic
import qimage2ndarray
import numpy
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
        self.featureTableWidget.itemSelectionChanged.connect( self.updateOKButton )
                
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
    
    def createFeatureTable(self, features, sigmas, window_size, brushNames=None):
        self.featureTableWidget.createTableForFeatureDlg(features, sigmas, window_size, brushNames)
    
    def setImageToPreView(self, image):
        self.preView.setVisible(image is not None)
        if image is not None:
            self.preView.setPreviewImage(qimage2ndarray.array2qimage(image))
        
    def setIconsToTableWidget(self, checked, partiallyChecked, unchecked):
        self.featureTableWidget.itemDelegate.setCheckBoxIcons(checked, partiallyChecked, unchecked)
    
    def updateOKButton(self):
        num_features = numpy.sum( self.featureTableWidget.createSelectedFeaturesBoolMatrix() )
        self.ok.setEnabled( num_features > 0 )

    def showEvent(self, event):
        super( FeatureDlg, self ).showEvent(event)
        self.updateOKButton()
    
    def setEnableItemMask(self, mask):
        # See comments in FeatureTableWidget.setEnableItemMask()
        self.featureTableWidget.setEnableItemMask(mask)

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
    
