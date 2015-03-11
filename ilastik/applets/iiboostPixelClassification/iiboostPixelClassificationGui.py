import os

from PyQt4.QtGui import QMessageBox

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
