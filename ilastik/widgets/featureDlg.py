###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2018, the ilastik developers
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
#          http://ilastik.org/license.html
###############################################################################
import sys
import os
import numpy
from . import preView

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog
import qimage2ndarray


class FeatureDlg(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        # init
        # ------------------------------------------------

        localDir = os.path.split(os.path.abspath(__file__))[0]
        uic.loadUi(localDir + "/featureDialog.ui", self)

        # the preview is currently shown in a separate window
        self.preView = preView.PreView()
        self.cancel.clicked.connect(self.reject)
        self.ok.clicked.connect(self.accept)

        self.featureTableWidget.itemSelectionChanged.connect(self.updateOKButton)

    # methods
    # ------------------------------------------------
    @property
    def scales(self):
        """Return the list of scale values that the user might have edited."""
        return self.featureTableWidget.sigmas

    @property
    def computeIn2d(self):
        """Return the list of scale values that the user might have edited."""
        return self.featureTableWidget.computeIn2d

    @property
    def selectionMatrix(self):
        """Return the bool matrix of features that the user selected."""
        return numpy.asarray(self.featureTableWidget.featureMatrix)

    @selectionMatrix.setter
    def selectionMatrix(self, newMatrix):
        """Populate the table of selected features with the provided matrix."""
        self.featureTableWidget.setFeatureMatrix(newMatrix)

    def createFeatureTable(self, features, sigmas, computeIn2d, window_size):
        self.featureTableWidget.setup(features, sigmas, computeIn2d, window_size)

    def setImageToPreView(self, image):
        self.preView.setVisible(image is not None)
        if image is not None:
            self.preView.setPreviewImage(qimage2ndarray.array2qimage(image))

    def setIconsToTableWidget(self, checked=None, partiallyChecked=None, unchecked=None, icon2d=None, icon3d=None):
        self.featureTableWidget.itemDelegate.setCheckBoxIcons(checked, partiallyChecked, unchecked, icon2d, icon3d)

    def updateOKButton(self):
        num_features = numpy.sum(self.featureTableWidget.featureMatrix)
        self.ok.setEnabled(num_features > 0)

    def showEvent(self, event):
        super().showEvent(event)
        self.updateOKButton()

    def setEnableItemMask(self, mask):
        # See comments in FeatureTableWidget.setEnableItemMask()
        self.featureTableWidget.setEnableItemMask(mask)

    def setComputeIn2dHidden(self, hidden):
        if hidden:
            self.featureTableWidget.hideRow(0)
        else:
            self.featureTableWidget.showRow(0)


if __name__ == "__main__":
    # make the program quit on Ctrl+C
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from PyQt5.QtWidgets import QApplication
    from featureTableWidget import FeatureEntry

    app = QApplication(sys.argv)

    # app.setStyle("windows")
    # app.setStyle("motif")
    # app.setStyle("cde")
    # app.setStyle("plastique")
    # app.setStyle("macintosh")
    # app.setStyle("cleanlooks")

    ex = FeatureDlg()
    ex.createFeatureTable([("Color", [FeatureEntry("Banananananaana", minimum_scale=.3)]),
                           ("Edge", [FeatureEntry("Mango"), FeatureEntry("Cherry")])],
                          [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0], [False, False, False, False, True, True, True], 3.5)
    ex.setWindowTitle("FeatureTest")
    ex.setImageToPreView(None)

    def handle_accepted():
        print("ACCEPTED")
        print(ex.selectionMatrix)
    ex.accepted.connect(handle_accepted)
    ex.exec_()
    print("DONE")
    # app.exec_()
