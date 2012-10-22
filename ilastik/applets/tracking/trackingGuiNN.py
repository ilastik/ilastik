from PyQt4.QtGui import QWidget, QColor, QVBoxLayout, QFileDialog
from PyQt4 import uic

import os
import math

from ilastik.applets.layerViewer import LayerViewerGui
from volumina.widgets.thresholdingWidget import ThresholdingWidget
from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ConstantSource, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables


import logging
import os.path as path
from lazyflow.operators.obsolete.generic import axisTagsToString
from lazyflow.rtype import SubRegion
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer
import ctracking
import numpy as np
import h5py

from ilastik.utility import bind

class TrackingGuiNN( QWidget ):
    """
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self.volumeEditorWidget        

    def appletDrawers( self ):
        return [ ("Tracking", self._drawer ) ]

    def menus( self ):
        return []

    def viewerControlWidget( self ):
        return self._viewerControlWidget

    def setImageIndex( self, imageIndex ):
        mainOperator = self.mainOperator.innerOperators[imageIndex]

        # self.rawsrc = LazyflowSource( mainOperator.RawData )
        # layerraw = GrayscaleLayer( self.rawsrc )
        # layerraw.name = "Raw"
        # self.layerstack.append( layerraw )

        self.objectssrc = LazyflowSource( mainOperator.LabelImage )
        ct = colortables.create_default_8bit()
        ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
        layer = ColortableLayer( self.objectssrc, ct )
        layer.name = "Objects"
        self.layerstack.append(layer)

        ct[255] = QColor(0,0,0,255).rgba() # misdetections        
        self.trackingsrc = LazyflowSource( mainOperator.Output )
        layer = ColortableLayer( self.trackingsrc, ct )
        layer.name = "Tracking"
        self.layerstack.append(layer)

        if mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = mainOperator.LabelImage.meta.shape

            maxt = mainOperator.LabelImage.meta.shape[0]
            maxx = mainOperator.LabelImage.meta.shape[1]
            maxy = mainOperator.LabelImage.meta.shape[2]
            maxz = mainOperator.LabelImage.meta.shape[3]            
            self._drawer.from_time.setRange(0,maxt-1)
            self._drawer.from_time.setValue(0)
            self._drawer.to_time.setRange(0,maxt-2)
            self._drawer.to_time.setValue(maxt-2)       

            self._drawer.from_x.setRange(0,maxx-1)
            self._drawer.from_x.setValue(0)
            self._drawer.to_x.setRange(0,maxx-1)
            self._drawer.to_x.setValue(maxx-1)       
        
            self._drawer.from_y.setRange(0,maxy-1)
            self._drawer.from_y.setValue(0)
            self._drawer.to_y.setRange(0,maxy-1)
            self._drawer.to_y.setValue(maxy-1)       

            self._drawer.from_z.setRange(0,maxz-1)
            self._drawer.from_z.setValue(0)
            self._drawer.to_z.setRange(0,maxz-1)
            self._drawer.to_z.setValue(maxz-1)       

    def reset( self ):
        print "TrackinGui.reset(): not implemented"

    ###########################################
    ###########################################
    
    def __init__(self, mainOperator):
        """
        """
        super(TrackingGuiNN, self).__init__()
        self.mainOperator = mainOperator
        self.layerstack = LayerStackModel()

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        
        if self.mainOperator.LabelImage.meta.shape:
            self.editor.dataShape = self.mainOperator.LabelImage.meta.shape
        self.mainOperator.LabelImage.notifyMetaChanged( self._onMetaChanged)


    def _onMetaChanged( self, slot ):
        if slot is self.mainOperator.LabelImage:
            if slot.meta.shape:
                print slot.meta.shape
                self.editor.dataShape = slot.meta.shape

                maxt = slot.meta.shape[0]
                self._drawer.from_time.setRange(0,maxt-1)
                self._drawer.from_time.setValue(0)
                self._drawer.to_time.setRange(0,maxt-2)
                self._drawer.to_time.setValue(maxt-2)       

    def _initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """

        self.editor = VolumeEditor(self.layerstack)

        #self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        #self.editor.setInteractionMode( 'navigation' )
        self.volumeEditorWidget = VolumeEditorWidget()
        self.volumeEditorWidget.init(self.editor)                
        
        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        model.canMoveSelectedUp.connect(self._viewerControlWidget.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self._viewerControlWidget.DownButton.setEnabled)
        model.canDeleteSelected.connect(self._viewerControlWidget.DeleteButton.setEnabled)

        # Connect our layer movement buttons to the appropriate layerstack actions
        self._viewerControlWidget.layerWidget.init(model)
        self._viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
        self._viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
        self._viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)

        self.editor._lastImageViewFocus = 0

            
    def _initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawerNN.ui")

        self._drawer.TrackButton.pressed.connect(self._onTrackButtonPressed)
        self._drawer.exportButton.pressed.connect(self._onExportButtonPressed)

    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")


    def _onExportButtonPressed(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory', '/home')      
        
        if directory is None:
            print "cancelled."
            return
        
        print "Saving first label image..."
        self._write_events([], str(directory), 0)
        
        events = self.mainOperator.innerOperators[0].events
        print "Saving events..."
        print "Length of events " + str(len(events))
        
        for i, events_at in enumerate(events):
            self._write_events(events_at, str(directory), i+1)

        
        
    def _onTrackButtonPressed( self ):
        divDist = self._drawer.divDistBox.value()
        movDist = self._drawer.movDistBox.value()        
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
        distanceFeatures = []
        if self._drawer.comCheckBox.isChecked():
            distanceFeatures.append("com")
        if self._drawer.volCheckBox.isChecked():
            distanceFeatures.append("count")
        
        if len(distanceFeatures) == 0:
            self._drawer.comCheckBox.setChecked(True)
            distanceFeatures.append("com")
        splitterHandling = self._drawer.splitterHandlingBox.isChecked()
        
        self.time_range =  range(from_t, to_t + 1)
        
        self.mainOperator.innerOperators[0].track(
            time_range = self.time_range,
            x_range = (from_x, to_x + 1),
            y_range = (from_y, to_y + 1),
            z_range = (from_z, to_z + 1),
            size_range = (from_size, to_size + 1),
            x_scale = self._drawer.x_scale.value(),
            y_scale = self._drawer.y_scale.value(),
            z_scale = self._drawer.z_scale.value(),
            divDist=divDist,
            movDist=movDist,
            distanceFeatures=distanceFeatures,
            divThreshold=divThreshold,
            splitterHandling=splitterHandling
            )
        
        self._drawer.exportButton.setEnabled(True)
                
                
    def handleThresholdGuiValuesChanged(self, minVal, maxVal):
        with Tracer(traceLogger):
            self.mainOperator.MinValue.setValue(minVal)
            self.mainOperator.MaxValue.setValue(maxVal)
    
    def setupLayers(self, currentImageIndex):
        print "tracking: setupLayers"
        with Tracer(traceLogger):
            layers = []
    
            # Show the thresholded data
            outputImageSlot = self.mainOperator.Output
            if outputImageSlot.ready():
                outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
                outputLayer.name = "min <= x <= max"
                outputLayer.visible = True                
                outputLayer.opacity = 1.0
                layers.append(outputLayer)
            
            # # Show the  data
            # invertedOutputSlot = self.mainOperator.InvertedOutput[ currentImageIndex ]
            # if invertedOutputSlot.ready():
            #     invertedLayer = self.createStandardLayerFromSlot( invertedOutputSlot )
            #     invertedLayer.name = "(x < min) U (x > max)"
            #     invertedLayer.visible = True
            #     invertedLayer.opacity = 0.25
            #     layers.append(invertedLayer)
            
            # # Show the raw input data
            # inputImageSlot = self.mainOperator.InputImage[ currentImageIndex ]
            # if inputImageSlot.ready():
            #     inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            #     inputLayer.name = "Raw Input"
            #     inputLayer.visible = True
            #     inputLayer.opacity = 1.0
            #     layers.append(inputLayer)
    
            return layers


    def handleEditorRightClick(self, currentImageIndex, position5d, globalWindowCoordinate):
        print 'position5d = ' + str(position5d)
        print 'currentImageIndex = ' + str(currentImageIndex)


    def _write_events(self, events, directory, t):
        fn =  directory + "/" + str(t).zfill(5)  + ".h5"
        
        dis = []
        app = []
        div = []
        mov = []
        print "-- Writing results to " + path.basename(fn)
        for event in events:
            if event.type == ctracking.EventType.Appearance:
                app.append((event.traxel_ids[0], event.energy))
            if event.type == ctracking.EventType.Disappearance:
                dis.append((event.traxel_ids[0], event.energy))
            if event.type == ctracking.EventType.Division:
                div.append((event.traxel_ids[0], event.traxel_ids[1], event.traxel_ids[2], event.energy))
            if event.type == ctracking.EventType.Move:
                mov.append((event.traxel_ids[0], event.traxel_ids[1], event.energy))
    
        # convert to ndarray for better indexing
        dis = np.asarray(dis)
        app = np.asarray(app)
        div = np.asarray(div)
        mov = np.asarray(mov)
    
    
        key = []
        for idx, flag in enumerate(axisTagsToString(self.mainOperator.innerOperators[0].LabelImage.meta.axistags)):
            if flag is 't':
                key.append(slice(t,t+1))
            elif flag is 'c':
                key.append(slice(0,1))                
            else:
                key.append(slice(0,self.mainOperator.innerOperators[0].LabelImage.meta.shape[idx]))                
        roi = SubRegion(self.mainOperator.innerOperators[0].LabelImage, key)
        
        labelImage = self.mainOperator.innerOperators[0].LabelImage.get(roi).wait()
        
        # write only if file exists
        with LineageH5(fn, 'a') as f_curr:
            # delete old label image
            if "segmentation" in f_curr.keys():
                del f_curr["segmentation"]
            
            seg = f_curr.create_group("segmentation")            
            # write label image
            seg.create_dataset("labels", data = labelImage[0,...,0], dtype=np.uint16)
            
            # delete old tracking
            if "tracking" in f_curr.keys():
                del f_curr["tracking"]

            tg = f_curr.create_group("tracking")            
            
            # write associations
            if len(app):
                ds = tg.create_dataset("Appearances", data=app[:, :-1], dtype=np.int32)
                ds.attrs["Format"] = "cell label appeared in current file"
    
                ds = tg.create_dataset("Appearances-Energy", data=app[:, -1], dtype=np.double)
                ds.attrs["Format"] = "lower energy -> higher confidence"
    
            if len(dis):
                ds = tg.create_dataset("Disappearances", data=dis[:, :-1], dtype=np.int32)
                ds.attrs["Format"] = "cell label disappeared in current file"
    
                ds = tg.create_dataset("Disappearances-Energy", data=dis[:, -1], dtype=np.double)
                ds.attrs["Format"] = "lower energy -> higher confidence"
    
    
            if len(mov):
                ds = tg.create_dataset("Moves", data=mov[:, :-1], dtype=np.int32)
                ds.attrs["Format"] = "from (previous file), to (current file)"
    
                ds = tg.create_dataset("Moves-Energy", data=mov[:, -1], dtype=np.double)
                ds.attrs["Format"] = "lower energy -> higher confidence"
    
                
            if len(div):
                ds = tg.create_dataset("Splits", data=div[:, :-1], dtype=np.int32)
                ds.attrs["Format"] = "ancestor (previous file), descendant (current file), descendant (current file)"
    
                ds = tg.create_dataset("Splits-Energy", data=div[:, -1], dtype=np.double)
                ds.attrs["Format"] = "lower energy -> higher confidence"
    
        print "-> results successfully written"








class LineageH5( h5py.File ):
    mov_ds = "/tracking/Moves"
    mov_ener_ds = "/tracking/Moves-Energy"
    app_ds = "/tracking/Appearances"
    app_ener_ds = "/tracking/Appearances-Energy"
    dis_ds = "/tracking/Disappearances"
    dis_ener_ds = "/tracking/Disappearances-Energy"
    div_ds = "/tracking/Splits"
    div_ener_ds = "/tracking/Splits-Energy"
    feat_gn = "/features"
    track_gn = "/tracking/"

    @property
    def x_scale( self ):
        return self._x_scale
    @x_scale.setter
    def x_scale( self, scale ):
        self._x_scale = scale

    @property
    def y_scale( self ):
        return self._y_scale
    @y_scale.setter
    def y_scale( self, scale ):
        self._y_scale = scale

    @property
    def z_scale( self ):
        return self._z_scale
    @z_scale.setter
    def z_scale( self, scale ):
        self._z_scale = scale
        
    # timestep will be set in loaded traxels accordingly
    def __init__( self, *args, **kwargs):
        h5py.File.__init__(self, *args, **kwargs)
        if "timestep" in kwargs:
            self.timestep = kwargs["timestep"]
        else:
            self.timestep = 0
        
        self._x_scale = 1.0
        self._y_scale = 1.0
        self._z_scale = 1.0

    def init_tracking( self, div=np.empty(0), mov=np.empty(0), dis=np.empty(0), app=np.empty(0)):
        if "tracking" in self.keys():
            del self["tracking"]
        self.create_group("tracking")

    def has_tracking( self ):
        if "tracking" in self.keys():
            return True
        else:
            return False
            
    def add_move( self, from_id, to_id):
        n_moves = self[self.mov_ds].shape[0];
        movs = self.get_moves()
        new = np.vstack([movs, (from_id, to_id)])
        self.update_moves(new)

    def update_moves( self, mov_pairs ):
        if path.basename(self.mov_ds) in self[self.track_gn].keys():
            del self[self.mov_ds]
        if len(mov_pairs) > 0:
            self[self.track_gn].create_dataset("Moves", data=np.asarray( mov_pairs, dtype=np.int32))

    def get_moves( self ):
        if self.has_tracking() and path.basename(self.mov_ds) in self[self.track_gn].keys():
            return self[self.mov_ds].value
        else:
            return np.empty(0)
    def get_move_energies( self ):
        if path.basename(self.mov_ener_ds) in self[self.track_gn].keys():
            e = self[self.mov_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)
        

    def get_divisions( self ):
        if self.has_tracking() and path.basename(self.div_ds) in self[self.track_gn].keys():
            return self[self.div_ds].value
        else:
            return np.empty(0)

    def update_divisions( self, div_triples ):
        if path.basename(self.div_ds) in self[self.track_gn].keys():
            del self[self.div_ds]
        if len(div_triples) > 0:
            self[self.track_gn].create_dataset("Splits", data=np.asarray( div_triples, dtype=np.int32))

    def get_division_energies( self ):
        if path.basename(self.div_ener_ds) in self[self.track_gn].keys():
            e = self[self.div_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)

    def get_disappearances( self ):
        if self.has_tracking() and path.basename(self.dis_ds) in self[self.track_gn].keys():
            dis = self[self.dis_ds].value
            if isinstance(dis, np.ndarray):
                return dis
            else:
                return np.array([dis])
        else:
            return np.empty(0)

    def update_disappearances( self, dis_singlets ):
        if path.basename(self.dis_ds) in self[self.track_gn].keys():
            del self[self.dis_ds]
        if len(dis_singlets) > 0:
            self[self.track_gn].create_dataset("Disappearances", data=np.asarray( dis_singlets, dtype=np.int32))
        
    def get_disappearance_energies( self ):
        if path.basename(self.dis_ener_ds) in self[self.track_gn].keys():
            e = self[self.dis_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)


    def get_appearances( self ):
        if self.has_tracking() and path.basename(self.app_ds) in self[self.track_gn].keys():
            app = self[self.app_ds].value
            if isinstance(app, np.ndarray):
                return app
            else:
                return np.array([app])
        else:
            return np.empty(0)

    def update_appearances( self, app_singlets ):
        if path.basename(self.app_ds) in self[self.track_gn].keys():
            del self[self.app_ds]
        if len(app_singlets) > 0:
            self[self.track_gn].create_dataset("Appearances", data=np.asarray( app_singlets, dtype=np.int32))

    def get_appearance_energies( self ):
        if path.basename(self.app_ener_ds) in self[self.track_gn].keys():
            e = self[self.app_ener_ds].value
            if isinstance(e, np.ndarray):
                return e
            else:
                return np.array([e])
        else:
            return np.empty(0)

    def rm_appearance( self, id ):
        apps = self.get_appearances()
        if not id in apps:
            raise Exception("LineageH5::rm_appearance(): id %d not an appearance" % id)
        filtered = apps[apps!=id]
        b = np.empty(dtype=apps.dtype, shape=(filtered.shape[0], 1))
        b[:,0] = filtered[:]
        self.update_appearances( b )

    def rm_disappearance( self, id ):
        diss = self.get_disappearances()
        if not id in diss:
            raise Exception("LineageH5::rm_disappearance(): id %d not an disappearance" % id)
        filtered = diss[diss!=id]
        b = np.empty(dtype=diss.dtype, shape=(filtered.shape[0], 1))
        b[:,0] = filtered[:]
        self.update_disappearances( b )

    def get_ids( self ):
        features_group = self[self.feat_gn]
        labelcontent = features_group["labelcontent"].value
        valid_labels = (np.arange(len(labelcontent))+1)[labelcontent==1]
        return valid_labels
        
#    def Tracklets( self , timestep=None, position='mean', add_features_as_meta=True):
#        valid_labels = self.get_ids()
#        features_group = self[self.feat_gn]
#        tracklets = _ts.Tracklets([tracklet_from_labelgroup( features_group[str(label)], timestep=timestep, add_features_as_meta = add_features_as_meta, position=position ) for label in valid_labels])
#        return tracklets

    def Traxels( self , timestep=None, position='mean', add_features_as_meta=True):
        return self.Tracklets( timestep, position, add_features_as_meta )

#    def cTraxels( self, as_python_list=False, prediction_threshold=None ):
#        if prediction_threshold:
#            print "LineageH5::cTraxels: predicition threshold %f" % prediction_threshold
#        # probe for objects group (higher io performance than features group)
#        if 'objects' in self.keys():
#            return self._cTraxels_from_objects_group( as_python_list, prediction_threshold )
#        # use old 'features' format for traxels
#        else:
#            raise Exception("objects group not found")
#            #if as_python_list or prediction_threshold:
#            #    raise Exception("LineageH5::cTraxels: old format: requested options not implemented")
#            #return self._cTraxels_from_features_group()
#
#    def _cTraxels_from_objects_group( self , as_python_list = False, prediction_threshold=None):
#        objects_g = self["objects"]
#        features_g = self["objects/features"]
#        ids = objects_g["meta/id"].value
#        valid = objects_g["meta/valid"].value
#        prediction = None
#        if "prediction" in objects_g["meta"]:
#            prediction = objects_g["meta/prediction"]
#        elif prediction_threshold:
#            raise Exception("prediction_threshold set, but no prediction dataset found")
#        features = {}
#        for name in features_g.keys():
#            features[name] = features_g[name].value
#
#        if as_python_list:
#            ts = list()
#        else:
#            ts = ctracking.cTraxels()
#        for idx, is_valid in enumerate(valid):
#            if prediction_threshold:
#                if prediction[idx] < prediction_threshold:
#                    is_valid = False
#            if is_valid:
#                tr = ctracking.cTraxel()
#                #tr.set_intmaxpos_locator()
#                tr.set_x_scale(self._x_scale)
#                tr.set_y_scale(self._y_scale)
#                tr.set_z_scale(self._z_scale)
#                tr.Id = int(ids[idx])
#                tr.Timestep = self.timestep
#                for name_value in features.items():
#                    tr.add_feature_array(str(name_value[0]), len(name_value[1][idx]))
#                    for i,v in enumerate(name_value[1][idx]):
#                        tr.set_feature_value(str(name_value[0]), i, float(v))
#                if as_python_list:
#                    ts.append(tr)
#                else:
#                    ts.add_traxel(tr)
#        return ts
#
#    def _cTraxels_from_features_group( self ):
#        features_group = self[self.feat_gn]
#        labelcontent = features_group["labelcontent"].value
#        invalid_labels = (np.arange(len(labelcontent))+1)[labelcontent==0]
#
#        # note, that we used the ctracklet_from_labelgroup() here before, but had
#        # to replace it by the following code due to bad performance
#
#        ts = ctracking.cTraxels()
#        # state machine for parsing features group
#        class Harvester( object ):
#            def __init__( self, invalid_labels=[], timestep=0):
#                self.current_ctracklet = None
#                self.timestep = timestep
#                self.invalid_labels = map(int, invalid_labels )
#                
#            def __call__(self, name, obj):
#                # name is the full path inside feature group
#                # entering a new label group...
#                if name.isdigit():
#                    # store away the last cTraxel
#                    if self.current_ctracklet != None:
#                        ts.add_traxel(self.current_ctracklet)
#                    if int(name) in self.invalid_labels:
#                        self.current_ctracklet = None
#                        print "invalid!"
#                    else:
#                        self.current_ctracklet = ctracking.cTraxel()
#                        self.current_ctracklet.Id = int(name)
#                        self.current_ctracklet.Timestep = self.timestep
#                elif name == 'featurecontent' or name == 'labelcontent' or name == 'labelcount':
#                    pass
#                else:
#                    feature_name = path.basename(name)
#                    self.current_ctracklet.add_feature_array(str(feature_name), len(obj.value))
#                    for i,v in enumerate(obj.value):
#                        self.current_ctracklet.set_feature_value(str(feature_name), i, float(v))
#        harvest = Harvester(invalid_labels, self.timestep)
#        features_group.visititems(harvest)
#
#        return ts
#
#
#
#
