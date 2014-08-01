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
from PyQt4 import uic, QtGui
import os

import logging
from ilastik.applets.tracking.base.trackingBaseGui import TrackingBaseGui
from lazyflow.request import Request
import sys
import traceback
import re
from ilastik.utility.gui.threadRouter import threadRouted
from ilastik.utility import log_exception

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
        if 'with_divisions' in parameters.keys():
            self._drawer.withDivisionsBox.setChecked(parameters['with_divisions'])
        if 'cplex_timeout' in parameters.keys():
            self._drawer.timeoutBox.setText(str(parameters['cplex_timeout']))
        
        return self._drawer
    
    def initAppletDrawerUi(self):
        super(ChaingraphTrackingGui, self).initAppletDrawerUi()
        self._allowedTimeoutInputRegEx = re.compile('^[0-9]*$')    
        self._drawer.timeoutBox.textChanged.connect(self._onTimeoutBoxChanged)
        
    @threadRouted            
    def _onTimeoutBoxChanged(self, *args):        
        inString = str(self._drawer.timeoutBox.text())
        if self._allowedTimeoutInputRegEx.match(inString) is None:
            self._drawer.timeoutBox.setText(inString.decode("utf8").encode("ascii", "replace")[:-1])
    
    
    def _onTrackButtonPressed( self ):    
        if not self.mainOperator.ObjectFeatures.ready():
            self._criticalMessage("You have to compute object features first.")            
            return
        
        
        def _track():
            self.applet.busy = True
            self.applet.appletStateUpdateRequested.emit()
            
            app = self._drawer.appSpinBox.value()
            dis = self._drawer.disSpinBox.value()
            opp = self._drawer.oppSpinBox.value()
            noiserate = self._drawer.noiseRateSpinBox.value()
            noiseweight = self._drawer.noiseWeightSpinBox.value()
            epGap = self._drawer.epGapSpinBox.value()
            n_neighbors = self._drawer.nNeighborsSpinBox.value()
            with_div = self._drawer.withDivisionsBox.isChecked()
            cplex_timeout = None
            if len(str(self._drawer.timeoutBox.text())):
                cplex_timeout = int(self._drawer.timeoutBox.text())
                
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
                            n_neighbors=n_neighbors,
                            with_div=with_div,
                            cplex_timeout=cplex_timeout)
            except Exception:
                ex_type, ex, tb = sys.exc_info()
                log_exception( logger )    
                self._criticalMessage("Exception(" + str(ex_type) + "): " + str(ex))                        
                return
    
        def _handle_finished(*args):
            self.applet.progressSignal.emit(100)
            self._drawer.TrackButton.setEnabled(True)
            self._drawer.exportButton.setEnabled(True)
            self._drawer.exportTifButton.setEnabled(True)
            self._setLayerVisible("Objects", False) 
            self.applet.busy = False            
            self.applet.appletStateUpdateRequested.emit()
            
        def _handle_failure( exc, exc_info ):
            self.applet.progressSignal.emit(100)
            msg = "Exception raised during tracking.  See traceback above.\n"
            log_exception( logger, msg, exc_info )    
            self._drawer.TrackButton.setEnabled(True)
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
        
        self._drawer.TrackButton.setEnabled(False)        
        self.applet.progressSignal.emit(0)
        self.applet.progressSignal.emit(-1)
        req = Request( _track )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()

