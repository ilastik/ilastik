from PyQt4 import uic, QtGui
import os
import logging
from ilastik.applets.tracking.base.trackingGuiBase import TrackingGuiBase

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class ConservationTrackingGui( TrackingGuiBase ):
                
    def _setMergerLegend(self, labels, selection):        
        for i in range(1,len(labels)+1):
            if i <= selection:
                labels[i-1].setVisible(True)
            else:
                labels[i-1].setVisible(False)
    
    def _loadUiFile(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")        
        return self._drawer

    def initAppletDrawerUi(self):
        super(ConservationTrackingGui, self).initAppletDrawerUi()        
        
        self.mergerLabels = [self._drawer.merg1,
                             self._drawer.merg2,
                             self._drawer.merg3,
                             self._drawer.merg4,
                             self._drawer.merg5,
                             self._drawer.merg6,
                             self._drawer.merg7]
        for i in range(len(self.mergerLabels)):
            self._labelSetStyleSheet(self.mergerLabels[i], self.mergerColors[i+1])
        
        self._onMaxObjectsBoxChanged()
        self._drawer.maxObjectsBox.valueChanged.connect(self._onMaxObjectsBoxChanged)
        self._drawer.appBox.stateChanged.connect(self._onAppDisappBoxChanged)
        self._drawer.disappBox.stateChanged.connect(self._onAppDisappBoxChanged)
        self._onAppDisappBoxChanged()

    def _onMaxObjectsBoxChanged(self):
        self._setMergerLegend(self.mergerLabels, self._drawer.maxObjectsBox.value())
    
    def _onAppDisappBoxChanged(self):
        if self._drawer.appBox.isChecked() or self._drawer.disappBox.isChecked():
            self._drawer.fixDetectionsBox.setEnabled(True)
        else:
            self._drawer.fixDetectionsBox.setChecked(False)
            self._drawer.fixDetectionsBox.setEnabled(False)
        
    def _onTrackButtonPressed( self ):        
        maxDist = self._drawer.maxDistBox.value()
        maxObj = self._drawer.maxObjectsBox.value()        
        divThreshold = self._drawer.divThreshBox.value()
        
        from_t = self._drawer.from_time.value()
        to_t = self._drawer.to_time.value()
        from_x = self._drawer.from_x.value()
        to_x = self._drawer.to_x.value()
        from_y = self._drawer.from_y.value()
        to_y = self._drawer.to_y.value()        
        from_z = self._drawer.from_z.value()
        to_z = self._drawer.to_z.value()        
        from_size = self._drawer.from_size.value()
        to_size = self._drawer.to_size.value()     
        
        self.time_range =  range(from_t, to_t + 1)
        avgSize = [self._drawer.avgSizeBox.value()]
        
        withAppearance = self._drawer.appBox.isChecked()
        withDisappearance = self._drawer.disappBox.isChecked()
        fixedDetections = self._drawer.fixDetectionsBox.isChecked()
        withTracklets = self._drawer.trackletsBox.isChecked()
        sizeDependent = self._drawer.sizeDepBox.isChecked()
        
        try:
            self.mainOperator.track(
                time_range = self.time_range,
                x_range = (from_x, to_x + 1),
                y_range = (from_y, to_y + 1),
                z_range = (from_z, to_z + 1),
                size_range = (from_size, to_size + 1),
                x_scale = self._drawer.x_scale.value(),
                y_scale = self._drawer.y_scale.value(),
                z_scale = self._drawer.z_scale.value(),
                maxDist=maxDist,         
                maxObj = maxObj,               
                divThreshold=divThreshold,
                avgSize=avgSize,
                fixedDetections=fixedDetections,
                withAppearance=withAppearance,
                withDisappearance=withDisappearance,
                withTracklets=withTracklets,
                sizeDependent=sizeDependent
                )
        except Exception as e:
            QtGui.QMessageBox.critical(self, "Error", "Error: " + str(e), QtGui.QMessageBox.Ok)                        
            return
        
        self._drawer.exportButton.setEnabled(True)
        self._drawer.exportTifButton.setEnabled(True)
#        self._drawer.lineageTreeButton.setEnabled(True)
        
        self._setLayerVisible("Objects", False)
            
            