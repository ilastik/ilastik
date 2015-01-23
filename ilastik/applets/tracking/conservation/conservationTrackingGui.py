from PyQt4 import uic, QtGui
import os
import logging
import sys
import re
import traceback
from ilastik.applets.tracking.base.trackingBaseGui import TrackingBaseGui
from ilastik.utility.gui.threadRouter import threadRouted
from ilastik.config import cfg as ilastik_config

from lazyflow.request.request import Request

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class ConservationTrackingGui( TrackingBaseGui ):     
    
    withMergers = True
    
    @threadRouted
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
        
        parameters = self.topLevelOperatorView.Parameters.value        
        if 'maxDist' in parameters.keys():
            self._drawer.maxDistBox.setValue(parameters['maxDist'])
        if 'maxObj' in parameters.keys():
            self._drawer.maxObjectsBox.setValue(parameters['maxObj'])
        if 'divThreshold' in parameters.keys():
            self._drawer.divThreshBox.setValue(parameters['divThreshold'])
        if 'avgSize' in parameters.keys():
            self._drawer.avgSizeBox.setValue(parameters['avgSize'][0])
        if 'withTracklets' in parameters.keys():
            self._drawer.trackletsBox.setChecked(parameters['withTracklets'])
        if 'sizeDependent' in parameters.keys():
            self._drawer.sizeDepBox.setChecked(parameters['sizeDependent'])
        if 'divWeight' in parameters.keys():
            self._drawer.divWeightBox.setValue(parameters['divWeight'])
        if 'transWeight' in parameters.keys():
            self._drawer.transWeightBox.setValue(parameters['transWeight'])
        if 'withDivisions' in parameters.keys():
            self._drawer.divisionsBox.setChecked(parameters['withDivisions'])
        if 'withOpticalCorrection' in parameters.keys():
            self._drawer.opticalBox.setChecked(parameters['withOpticalCorrection'])
        if 'withClassifierPrior' in parameters.keys():
            self._drawer.classifierPriorBox.setChecked(parameters['withClassifierPrior'])
        if 'withMergerResolution' in parameters.keys():
            self._drawer.mergerResolutionBox.setChecked(parameters['withMergerResolution'])
        if 'borderAwareWidth' in parameters.keys():
            self._drawer.bordWidthBox.setValue(parameters['borderAwareWidth'])
        if 'cplex_timeout' in parameters.keys():
            self._drawer.timeoutBox.setText(str(parameters['cplex_timeout']))
        if 'appearanceCost' in parameters.keys():
            self._drawer.appearanceBox.setValue(parameters['appearanceCost'])
        if 'disappearanceCost' in parameters.keys():
            self._drawer.disappearanceBox.setValue(parameters['disappearanceCost'])
        
        return self._drawer

    def initAppletDrawerUi(self):
        super(ConservationTrackingGui, self).initAppletDrawerUi()        

        self._allowedTimeoutInputRegEx = re.compile('^[0-9]*$')
        self._drawer.timeoutBox.textChanged.connect(self._onTimeoutBoxChanged)

        if not ilastik_config.getboolean("ilastik", "debug"):
            assert self._drawer.trackletsBox.isChecked()
            self._drawer.trackletsBox.hide()
            
            assert not self._drawer.hardPriorBox.isChecked()
            self._drawer.hardPriorBox.hide()

            assert not self._drawer.opticalBox.isChecked()
            self._drawer.opticalBox.hide()

            self._drawer.maxDistBox.hide() # hide the maximal distance box
            self._drawer.label_2.hide() # hie the maximal distance label
            self._drawer.label_5.hide() # hide division threshold label
            self._drawer.divThreshBox.hide()
            self._drawer.label_25.hide() # hide avg. obj size label
            self._drawer.avgSizeBox.hide()
          
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

    @threadRouted
    def _onTimeoutBoxChanged(self, *args):
        inString = str(self._drawer.timeoutBox.text())
        if self._allowedTimeoutInputRegEx.match(inString) is None:
            self._drawer.timeoutBox.setText(inString.decode("utf8").encode("ascii", "replace")[:-1])

    def _setRanges(self, *args):
        super(ConservationTrackingGui, self)._setRanges()        
        maxx = self.topLevelOperatorView.LabelImage.meta.shape[1] - 1
        maxy = self.topLevelOperatorView.LabelImage.meta.shape[2] - 1
        maxz = self.topLevelOperatorView.LabelImage.meta.shape[3] - 1
        
        maxBorder = min(maxx, maxy)
        if maxz != 0:
            maxBorder = min(maxBorder, maxz)
        self._drawer.bordWidthBox.setRange(0, maxBorder/2)
        
        
    def _onMaxObjectsBoxChanged(self):
        self._setMergerLegend(self.mergerLabels, self._drawer.maxObjectsBox.value())
        
    def _onTrackButtonPressed( self ):    
        if not self.mainOperator.ObjectFeatures.ready():
            self._criticalMessage("You have to compute object features first.")            
            return
        
        def _track():    
            self.applet.busy = True
            self.applet.appletStateUpdateRequested.emit()
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

            cplex_timeout = None
            if len(str(self._drawer.timeoutBox.text())):
                cplex_timeout = int(self._drawer.timeoutBox.text())

            withTracklets = self._drawer.trackletsBox.isChecked()
            sizeDependent = self._drawer.sizeDepBox.isChecked()
            hardPrior = self._drawer.hardPriorBox.isChecked()
            classifierPrior = self._drawer.classifierPriorBox.isChecked()
            divWeight = self._drawer.divWeightBox.value()
            transWeight = self._drawer.transWeightBox.value()
            withDivisions = self._drawer.divisionsBox.isChecked()        
            withOpticalCorrection = self._drawer.opticalBox.isChecked()
            withMergerResolution = self._drawer.mergerResolutionBox.isChecked()
            borderAwareWidth = self._drawer.bordWidthBox.value()
            withArmaCoordinates = True
            appearanceCost = self._drawer.appearanceBox.value()
            disappearanceCost = self._drawer.disappearanceBox.value()
    
            ndim=3
            if (to_z - from_z == 0):
                ndim=2
            
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
                    withTracklets=withTracklets,
                    sizeDependent=sizeDependent,
                    divWeight=divWeight,
                    transWeight=transWeight,
                    withDivisions=withDivisions,
                    withOpticalCorrection=withOpticalCorrection,
                    withClassifierPrior=classifierPrior,
                    ndim=ndim,
                    withMergerResolution=withMergerResolution,
                    borderAwareWidth = borderAwareWidth,
                    withArmaCoordinates = withArmaCoordinates,
                    cplex_timeout = cplex_timeout,
                    appearance_cost = appearanceCost,
                    disappearance_cost = disappearanceCost
                    )
            except Exception:           
                ex_type, ex, tb = sys.exc_info()
                traceback.print_tb(tb)            
                self._criticalMessage("Exception(" + str(ex_type) + "): " + str(ex))       
                return                     
        
        def _handle_finished(*args):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)
            self._drawer.TrackButton.setEnabled(True)
            self._drawer.exportButton.setEnabled(True)
            self._drawer.exportTifButton.setEnabled(True)
            self._setLayerVisible("Objects", False) 
            
        def _handle_failure( exc, exc_info ):
            self.applet.busy = False
            self.applet.appletStateUpdateRequested.emit()
            self.applet.progressSignal.emit(100)
            traceback.print_exception(*exc_info)
            sys.stderr.write("Exception raised during tracking.  See traceback above.\n")
            self._drawer.TrackButton.setEnabled(True)
        
        self.applet.progressSignal.emit(0)
        self.applet.progressSignal.emit(-1)
        req = Request( _track )
        req.notify_failed( _handle_failure )
        req.notify_finished( _handle_finished )
        req.submit()

    def menus(self):
        if not ilastik_config.getboolean("ilastik", "debug"):
            return []

        m = QtGui.QMenu("&Export", self.volumeEditorWidget)
        m.addAction("Export Tracking Information").triggered.connect(self.export_tracking_info)

        return [m]
                
    def export_tracking_info(self):
        from ilastik.utility.exportFile import ExportFile, Mode, objects_per_frame, ilastik_ids, ProgressPrinter
        from ilastik.widgets.exportObjectInfoDialog import ExportObjectInfoDialog

        op = self.topLevelOperatorView
        dimensions = op.RawImage.meta.shape
        computed_features = op.ObjectFeatures

        feature_names = {}
        #feature_names = op.ComputedFeatureNames([]).wait()

        dialog = ExportObjectInfoDialog(dimensions, feature_names)
        if not dialog.exec_():
            return
        settings = dialog.settings()
        selected_features = dialog.checked_features()

        obj_count = list(objects_per_frame(op.LabelImage))
        track_ids, extra_track_ids, divisions = op.export_track_ids()

        export_file = ExportFile(settings["file path"])

        ip = ProgressPrinter("InsertionProgress", range(100, -1, -5))
        ep = ProgressPrinter("ExportProgress", range(100, -1, -5))
        export_file.ExportProgress.subscribe(ep)
        export_file.InsertionProgress.subscribe(ip)
        #multi_move_max = op.Parameters["maxObj"] if op.Parameters.ready() else 2
        multi_move_max = 2

        export_file.add_columns("table", range(sum(obj_count)), Mode.List, {"names": ("object_id",)})
        ids = ilastik_ids(obj_count)
        export_file.add_columns("table", list(ids), Mode.List, {"names": ("time", "ilastik_id")})
        export_file.add_columns("table", track_ids, Mode.IlastikTrackingTable,
                                {"max": multi_move_max, "counts": obj_count, "extra ids": extra_track_ids})
        export_file.add_columns("table", computed_features, Mode.IlastikFeatureTable,
                                {"selection": selected_features})
        export_file.add_columns("divisions", divisions, Mode.List,
                                {"names": (
                                    "time", "parent", "track", "child1", "child_track1", "child2", "child_track2"
                                )})

        if settings["file type"] == "h5":
            export_file.add_rois("/images/{}/labeling", op.LabelImage, "table", settings["margin"], "labeling")
            if settings["include raw"]:
                export_file.add_image("/images/raw", op.RawImage)
            else:
                export_file.add_rois("/images/{}/raw", op.RawImage, "table", settings["margin"])

        export_file.write_all(settings["file type"], settings["compression"])