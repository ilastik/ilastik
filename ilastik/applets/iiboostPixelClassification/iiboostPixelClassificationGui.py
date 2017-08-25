###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2017, the ilastik developers
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
import os

from PyQt5.QtWidgets import QMessageBox, QPushButton

from ilastik.applets.pixelClassification.pixelClassificationGui import PixelClassificationGui

class IIBoostPixelClassificationGui( PixelClassificationGui ):
    
    def __init__(self, parentApplet, topLevelOperatorView):
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'
        super(IIBoostPixelClassificationGui, self).__init__(parentApplet, topLevelOperatorView, labelingDrawerUiPath)

        # Init special base class members
        # (See LabelingGui base class)
        self.minLabelNumber = 2
        self.maxLabelNumber = 2

        self.labelingDrawerUi.labelListView.allowDelete = False
        self.labelingDrawerUi.AddLabelButton.setVisible(False)

        def clear_all_labels():
            confirmed = QMessageBox.question(self, "Clear Labels", \
                        "Are you sure you want to clear all labels from the image volume you are currently viewing?", \
                        QMessageBox.Yes | QMessageBox.Cancel, \
                        defaultButton=QMessageBox.Yes)
                
            if confirmed == QMessageBox.Yes:
                # Clear all labels, but don't remove the label classes from the list.
                self.topLevelOperatorView.opLabelPipeline.opLabelArray.clearLabel(1)
                self.topLevelOperatorView.opLabelPipeline.opLabelArray.clearLabel(2)
        
        self.labelingDrawerUi.ClearAllLabelsButton.clicked.connect( clear_all_labels )

        self.labelingDrawerUi.numStumpsBox.setRange(1, 1000)

        num_stumps = self.topLevelOperatorView.get_num_stumps()
        self.labelingDrawerUi.numStumpsBox.setValue( num_stumps )
        def update_num_stumps(num_stumps):
            self.topLevelOperatorView.set_num_stumps( num_stumps )
        self.labelingDrawerUi.numStumpsBox.valueChanged.connect( update_num_stumps )

        # Feature selection doesn't work in IIBoost
        self.labelingDrawerUi.suggestFeaturesButton.setVisible(False)
            
    def toggleInteractive(self, checked):
        """
        Overridden from the base class.  Called when entering/leaving "live update" mode.
        """
        super( IIBoostPixelClassificationGui, self ).toggleInteractive(checked)
        
        # Don't allow changing the classifier factory during "live update" mode.
        self.labelingDrawerUi.numStumpsBox.setEnabled( not checked )
