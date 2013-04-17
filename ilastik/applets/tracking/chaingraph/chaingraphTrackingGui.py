from PyQt4 import uic, QtGui
import os

import logging
from ilastik.applets.tracking.base.trackingBaseGui import TrackingBaseGui
import sys
import traceback

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class ChaingraphTrackingGui( TrackingBaseGui ):

    def _loadUiFile(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")        
        
        if not self.topLevelOperatorView.Parameters.ready():
            raise Exception("Parameter slot is not ready")
        
        parameters = self.topLevelOperatorView.Parameters.value        
        if 'appearance' in parameters.keys():
            self._drawer.appSpinBox.setValue(parameters['appearance'])
        if 'disappearance' in parameters.keys():
            self._drawer.disSpinBox.setValue(parameters['disappearance'])
        if 'opportunity' in parameters.keys():
            self._drawer.oppSpinBox.setValue(parameters['opportunity'])
        if 'noiserate' in parameters.keys():
            self._drawer.noiseRateSpinBox.setValue(parameters['noiserate'])
        if 'noiseweight' in parameters.keys():
            self._drawer.noiseWeightSpinBox.setValue(parameters['noiseweight'])
        if 'epgap' in parameters.keys():
            self._drawer.epGapSpinBox.setValue(parameters['epgap'])
        
        return self._drawer
    
    def _onTrackButtonPressed( self ):    
        if not self.mainOperator.ObjectFeatures.ready():
            QtGui.QMessageBox.critical(self, "Error", "You have to select object features first.", QtGui.QMessageBox.Ok)
            return
        
        app = self._drawer.appSpinBox.value()
        dis = self._drawer.disSpinBox.value()
        opp = self._drawer.oppSpinBox.value()
        noiserate = self._drawer.noiseRateSpinBox.value()
        noiseweight = self._drawer.noiseWeightSpinBox.value()
        epGap = self._drawer.epGapSpinBox.value()
        n_neighbors = self._drawer.nNeighborsSpinBox.value()

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

        try:
            self.mainOperator.track(
                        time_range = range(from_t, to_t + 1),
                        x_range = (from_x, to_x + 1),
                        y_range = (from_y, to_y + 1),
                        z_range = (from_z, to_z + 1),
                        size_range = (from_size, to_size + 1),
                        x_scale = self._drawer.x_scale.value(),
                        y_scale = self._drawer.y_scale.value(),
                        z_scale = self._drawer.z_scale.value(),
                        app=app,
                        dis=dis,
                        noiserate = noiserate,
                        noiseweight = noiseweight,
                        opp=opp,                        
                        ep_gap=epGap,
                        n_neighbors=n_neighbors)
        except Exception:
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)            
            QtGui.QMessageBox.critical(self, "Error", "Exception(" + str(ex_type) + "): " + str(ex), QtGui.QMessageBox.Ok)
            return
    
        self._drawer.exportButton.setEnabled(True)
        self._drawer.exportTifButton.setEnabled(True)
        self._setLayerVisible("Objects", False)    
            