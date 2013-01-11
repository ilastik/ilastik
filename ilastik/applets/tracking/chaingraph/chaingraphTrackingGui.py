from PyQt4 import uic

import os
import math

import logging
from ilastik.applets.tracking.base.trackingGuiBase import TrackingGuiBase

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class ChaingraphTrackingGui( TrackingGuiBase ):

    def _loadUiFile(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")        
        return self._drawer
    
    def _onTrackButtonPressed( self ):
        app = self._drawer.appSpinBox.value()
        dis = self._drawer.disSpinBox.value()
        opp = self._drawer.oppSpinBox.value()
        noiserate = self._drawer.noiseRateSpinBox.value()
        noiseweight = self._drawer.noiseWeightSpinBox.value()
        epGap = self._drawer.epGapSpinBox.value()

        det = noiseweight*(-1)*math.log(1-noiserate)
        mdet = noiseweight*(-1)*math.log(noiserate)
        
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
                    opp=opp,
                    det=det,
                    mdet=mdet,
                    ep_gap=epGap)
    
        self._setLayerVisible("Objects", False)
    