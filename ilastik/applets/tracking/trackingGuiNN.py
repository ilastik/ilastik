from PyQt4.QtGui import QWidget, QColor, QFileDialog
from PyQt4 import uic

import os

from volumina.api import LazyflowSource, LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables


import logging
import os.path as path
from lazyflow.operators.obsolete.generic import axisTagsToString
from lazyflow.rtype import SubRegion
from lazyflow.roi import sliceToRoi
from ilastik.applets.tracking.opTrackingNN import relabel
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer
import ctracking
import numpy as np
import h5py
import vigra

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
        self._drawer.exportTifButton.pressed.connect(self._onExportTifButtonPressed)
        self._drawer.lineageTreeButton.pressed.connect(self._onLineageTreeButtonPressed)

    def _initViewerControlUi( self ):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")


    def _onExportButtonPressed(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'))      
        
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
            
    def _onExportTifButtonPressed(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Directory',os.getenv('HOME'))      
        
        if directory is None:
            print "cancelled."
            return
        
        print 'Saving results as tiffs...'
        
        label2color = self.mainOperator.innerOperators[0].label2color
        lshape = list(self.mainOperator.innerOperators[0].LabelImage.meta.shape)
    
        for t, label2color_at in enumerate(label2color):
            print 'exporting tiffs for t = ' + str(t)            
            
            roi = SubRegion(self.mainOperator.innerOperators[0].LabelImage, start=[t,] + 4*[0,], stop=[t+1,] + list(lshape[1:]))
            labelImage = self.mainOperator.innerOperators[0].LabelImage.get(roi).wait()
            relabeled = relabel(labelImage[0,...,0],label2color_at)
            for i in range(relabeled.shape[2]):
                out_im = relabeled[:,:,i]
                out_fn = str(directory) + '/vis_' + str(t).zfill(4) + '_' + str(i).zfill(4) + '.tif'
                vigra.impex.writeImage(np.asarray(out_im,dtype=np.uint8), out_fn)
        
        print 'Tiffs exported.'
                    
        
    def _onLineageTreeButtonPressed(self):
        fn = QFileDialog.getSaveFileName(self, 'Save Lineage Trees', os.getenv('HOME'))      
        
        if fn is None:
            print "cancelled."
            return        
        
        print "Computing Lineage Trees..."
        
        self._createLineageTrees(str(fn))
        
        print 'Lineage Trees saved.'
        
        
        
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
        mergerHandling = self._drawer.mergerHandlingBox.isChecked()
        
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
            splitterHandling=splitterHandling,
            mergerHandling=mergerHandling
            )
        
        self._drawer.exportButton.setEnabled(True)
        self._drawer.exportTifButton.setEnabled(True)
        self._drawer.lineageTreeButton.setEnabled(True)
                
                
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
            seg.create_dataset("labels", data = labelImage[0,...,0], dtype=np.uint32, compression=1)
            
            # delete old tracking
            if "tracking" in f_curr.keys():
                del f_curr["tracking"]

            tg = f_curr.create_group("tracking")            
            
            # write associations
            if len(app):
                ds = tg.create_dataset("Appearances", data=app[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "cell label appeared in current file"    
                ds = tg.create_dataset("Appearances-Energy", data=app[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"    
            if len(dis):
                ds = tg.create_dataset("Disappearances", data=dis[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "cell label disappeared in current file"
                ds = tg.create_dataset("Disappearances-Energy", data=dis[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"    
            if len(mov):
                ds = tg.create_dataset("Moves", data=mov[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "from (previous file), to (current file)"    
                ds = tg.create_dataset("Moves-Energy", data=mov[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"                
            if len(div):
                ds = tg.create_dataset("Splits", data=div[:, :-1], dtype=np.uint32, compression=1)
                ds.attrs["Format"] = "ancestor (previous file), descendant (current file), descendant (current file)"    
                ds = tg.create_dataset("Splits-Energy", data=div[:, -1], dtype=np.double, compression=1)
                ds.attrs["Format"] = "lower energy -> higher confidence"
    
        print "-> results successfully written"


    def _createLineageTrees(self, fn=None):
        from ete2 import Tree, NodeStyle, AttrFace
                
        tree = Tree()
        
        text_rotated = False 
        
        style = self._getNodeStyle()
        divisionStyle = self._getNodeStyle()
        
        invisibleNodeStyle = NodeStyle()
        invisibleNodeStyle["hz_line_color"] = "white"
        invisibleNodeStyle["vt_line_color"] = "white"
        invisibleNodeStyle["fgcolor"] = "white"
        
        distanceFromRoot = 0
        
        nodeMap = {}
        branchSize = {}
        
        # add all nodes which appear in the first frame
        for event in self.mainOperator.innerOperators[0].events[0]:
            if event.type != ctracking.EventType.Appearance:
                label = event.traxel_ids[0]
                appNode = tree.add_child(name=self._getNodeName(0, label), dist=distanceFromRoot )
                nodeMap[str(self._getNodeName(0, label))] = appNode
                branchSize[str(self._getNodeName(0, label))] = 0                    
                # making the branches to the root node invisible
                n = appNode
                while n:
                    n.set_style(invisibleNodeStyle)
                    n = n.up
                appNode.set_style(invisibleNodeStyle)
                name = AttrFace("name")
                name.fsize = 6
        
        # add all lineages
        for t, events_at in enumerate(self.mainOperator.innerOperators[0].events):
            t = t+1            
            for event in events_at:
                if event.type == ctracking.EventType.Appearance:
                    label = event.traxel_ids[0]
                    appNode = tree.add_child(name=self._getNodeName(t, label), dist=distanceFromRoot + t)
                    nodeMap[str(self._getNodeName(t, label))] = appNode
                    branchSize[str(self._getNodeName(t, label))] = 0                    
                    # making the branches to the root node invisible
                    n = appNode
                    while n:
                        n.set_style(invisibleNodeStyle)
                        n = n.up
                    appNode.set_style(invisibleNodeStyle)
                    name = AttrFace("name")
                    name.fsize = 6
#                    if text_rotated is False:
#                        appNode.add_face(name, column=0, position="branch-top")
#                    else:
#                        rot_text = faces.StaticItemFace(RotatedTextItem(rootNode.name, 7, "black", 270))
#                        appNode.add_face(rot_text, column=0, position="branch-top")
            
                elif event.type == ctracking.EventType.Disappearance:
                    label = event.traxel_ids[0]                    
                    newNode = nodeMap[str(self._getNodeName(t-1,str(label)))].add_child(
                        name = self._getNodeName(t-1,str(label)),dist = branchSize[str(self._getNodeName(t-1,str(label)))])                     
                    newNode.set_style(style)
                    del nodeMap[str(self._getNodeName(t-1,str(label)))]
                    del branchSize[str(self._getNodeName(t-1,str(label)))]
                    
                elif event.type == ctracking.EventType.Division:
                    labelOld = event.traxel_ids[0]
                    labelNew1 = event.traxel_ids[1]
                    labelNew2 = event.traxel_ids[2]                    
                    newNode = nodeMap[str(self._getNodeName(t-1,str(labelOld)))].add_child(
                            name = self._getNodeName(t-1,str(self._getNodeName(t-1,str(labelOld)))),
                            dist = branchSize[str(self._getNodeName(t-1,str(labelOld)))] )
                    del nodeMap[str(self._getNodeName(t-1,str(labelOld)))]
                    del branchSize[str(self._getNodeName(t-1,str(labelOld)))]
                    newNode.set_style(divisionStyle)
                    nodeMap[str(self._getNodeName(t,str(labelNew1)))] = newNode
                    nodeMap[str(self._getNodeName(t,str(labelNew2)))] = newNode
                    branchSize[str(self._getNodeName(t,str(labelNew1)))] = 1
                    branchSize[str(self._getNodeName(t,str(labelNew2)))] = 1                    
                    
                elif event.type == ctracking.EventType.Move:
                    labelOld = event.traxel_ids[0]
                    labelNew = event.traxel_ids[1]                    
                    nodeMap[str(self._getNodeName(t,str(labelNew)))] = nodeMap[str(self._getNodeName(t-1,str(labelOld)))]
                    del nodeMap[str(self._getNodeName(t-1,str(labelOld)))]
                    branchSize[str(self._getNodeName(t,str(labelNew)))] = branchSize[str(self._getNodeName(t-1,str(labelOld)))] + 1 
                    del branchSize[str(self._getNodeName(t-1,str(labelOld)))]

        for label in nodeMap.keys():
            # TODO: label(t) = label(t+1) ?!?!
            newNode = nodeMap[label].add_child(name = label,dist = branchSize[label])
        
        
        self._plotTree(tree, out_fn=fn, rotation=270, show_leaf_name=False, 
                  show_branch_length=False, circularTree=False, show_division_nodes=False, 
                  distance_between_branches=4, height=800)


    def _getNodeStyle(self, line_width=1, branch_type=0, node_color='DimGray', node_size=6, node_shape='circle'):
        from ete2 import NodeStyle
    
        style = NodeStyle()        
        style["hz_line_width"] = line_width
        style["vt_line_width"] = line_width
        # line type : 0 - solid, 1 - dashed, 2 - dotted
        style["hz_line_type"] = branch_type
        style["vt_line_type"] = branch_type
        style["fgcolor"] = node_color
        style["size"] = node_size
        # node shape: circle, sphere, square
        style["shape"] = node_shape
    
    def _getNodeName(self, frame, label):        
        name = "%s/%s" %(frame,label)     
        return name

    def _plotTree(self, tree, out_fn=None, rotation=270, show_leaf_name=False, 
                  show_branch_length=False, circularTree=False, show_division_nodes=True, 
                  distance_between_branches=4, show_border=False, width=None, height=None):            
        from ete2 import TreeStyle        
        from PyQt4 import QtSvg, QtCore, QtGui
        from ete2.treeview import qt4_render, drawer, main
        
          
        ts = TreeStyle()   
        ts.show_scale = False
        ts.show_border = show_border
        ts.orientation = 1 # 0, tree is drawn from left-to-right. 1, tree is drawn from right-to-left
        ts.rotation = rotation
        ts.show_leaf_name = show_leaf_name
        ts.show_branch_length = show_branch_length
        if circularTree:
            ts.mode = 'c'
        else:
            ts.mode = 'r'
        ts.branch_vertical_margin = distance_between_branches
        
        
        def hideInternalNodesLayout(node):
            if not node.is_leaf():
                node.img_style["size"] = 0
        
        if show_division_nodes is False:
            ts.layout_fn = hideInternalNodesLayout
        
        if out_fn is not None:        
#            scene, img = init_scene(tree, None, ts)
            scene  = qt4_render._TreeScene()
            img = ts
            
            tree_item, n2i, n2f = qt4_render.render(tree, img)
            scene.init_data(tree, img, n2i, n2f)
            tree_item.setParentItem(scene.master_item)
            scene.master_item.setPos(0,0)
            scene.addItem(scene.master_item)      
            main.save(scene, out_fn, w=width, h=height, dpi=600)    
              
        else:
            scene, img = drawer.init_scene(tree, None, ts)
            tree_item, n2i, n2f = qt4_render.render(tree, img)
            scene.init_data(tree, img, n2i, n2f)
        
            tree_item.setParentItem(scene.master_item)
            scene.addItem(scene.master_item)
        
            size = tree_item.rect()
            w, h = size.width(), size.height()
        
            svg = QtSvg.QSvgGenerator()
            svg.setFileName("test.svg")
            svg.setSize(QtCore.QSize(w, h))
            svg.setViewBox(size)
            pp = QtGui.QPainter()
            pp.begin(svg)
            #pp.setRenderHint(QtGui.QPainter.Antialiasing)
            #pp.setRenderHint(QtGui.QPainter.TextAntialiasing)
            #pp.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            scene.render(pp, tree_item.rect(), tree_item.rect(), QtCore.Qt.KeepAspectRatio)
    #            pp.end()
    #            img = QtSvg.QGraphicsSvgItem("test.svg")
    #            #img.setParentItem(scene.master_item)
    #            #scene.removeItem(tree_item)
    #            #tree_item.
        return





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

    def Traxels( self , timestep=None, position='mean', add_features_as_meta=True):
        return self.Tracklets( timestep, position, add_features_as_meta )
