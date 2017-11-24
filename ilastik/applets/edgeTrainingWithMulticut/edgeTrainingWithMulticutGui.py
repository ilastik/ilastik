from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QSpacerItem, QSizePolicy, QMenu
from PyQt5.QtGui import QColor

from functools import partial
from collections import defaultdict
import numpy
from past.utils import old_div


from volumina.view3d.meshgenerator import MeshGeneratorDialog, mesh_to_obj
from volumina.view3d.volumeRendering import RenderingManager

from ilastik.applets.edgeTraining.edgeTrainingGui import EdgeTrainingGui
from ilastik.applets.multicut.multicutGui import MulticutGuiMixin

class EdgeTrainingWithMulticutGui(MulticutGuiMixin, EdgeTrainingGui):
    
    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        MulticutGuiMixin.__init__(self, parentApplet, topLevelOperatorView)
        EdgeTrainingGui.__init__(self, parentApplet, topLevelOperatorView)

        # Disable 3D view by default
        self.render = False
        self.tagged_shape = defaultdict(lambda: 1)
        self.tagged_shape.update( topLevelOperatorView.RawData.meta.getTaggedShape() )
        is_3d = (self.tagged_shape['x'] > 1 and self.tagged_shape['y'] > 1 and self.tagged_shape['z'] > 1)

        if is_3d:
            try:
                self._renderMgr = RenderingManager( self.editor.view3d )
                self._shownObjects3D = {}
                self.render = True
            except:
                self.render = False

    def _after_init(self):
        EdgeTrainingGui._after_init(self)
        MulticutGuiMixin._after_init(self)

    def initAppletDrawerUi(self):
        training_controls = EdgeTrainingGui.createDrawerControls(self)
        training_controls.layout().setContentsMargins(5,0,5,0)
        training_layout = QVBoxLayout()
        training_layout.addWidget( training_controls )
        training_layout.setContentsMargins(0,15,0,0)
        training_box = QGroupBox( "Training", parent=self )
        training_box.setLayout(training_layout)
        training_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        multicut_controls = MulticutGuiMixin.createDrawerControls(self)
        multicut_controls.layout().setContentsMargins(5,0,5,0)
        multicut_layout = QVBoxLayout()
        multicut_layout.addWidget( multicut_controls )
        multicut_layout.setContentsMargins(0,15,0,0)
        multicut_box = QGroupBox( "Multicut", parent=self )
        multicut_box.setLayout(multicut_layout)
        multicut_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        drawer_layout = QVBoxLayout()
        drawer_layout.addWidget(training_box)
        drawer_layout.addWidget(multicut_box)
        drawer_layout.setSpacing(2)
        drawer_layout.setContentsMargins(5,5,5,5)
        drawer_layout.addSpacerItem( QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding) )
        
        self._drawer = QWidget(parent=self)
        self._drawer.setLayout(drawer_layout)        

        # GUI will be initialized in _after_init()
        #self.configure_gui_from_operator()

    def appletDrawer(self):
        return self._drawer

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base classes
        EdgeTrainingGui.stopAndCleanUp(self)
        MulticutGuiMixin.stopAndCleanUp(self)

    def setupLayers(self):
        layers = []
        edgeTrainingLayers = EdgeTrainingGui.setupLayers(self)

        mc_disagreement_layer = MulticutGuiMixin.create_multicut_disagreement_layer(self)
        if mc_disagreement_layer:
            layers.append(mc_disagreement_layer)
        
        mc_edge_layer = MulticutGuiMixin.create_multicut_edge_layer(self)
        if mc_edge_layer:
            layers.append(mc_edge_layer)

        mc_seg_layer = MulticutGuiMixin.create_multicut_segmentation_layer(self)
        if mc_seg_layer:
            layers.append(mc_seg_layer)

        layers += edgeTrainingLayers
        return layers


    def handleEditorRightClick(self, position5d, globalWindowCoordinate):

        multicutOp = self.topLevelOperatorView

        if not multicutOp.Output.ready():
            print("no output yet")
            return

        slicing = tuple(slice(i, i+1) for i in position5d)
        arr = multicutOp.Output[slicing].wait()
        objectLabel = arr.flat[0]
        print("you clicked object #", objectLabel)
        if objectLabel == 0:
            # no output yet
            return
        menu = QMenu(self)
        if self.render:
            if objectLabel in self._shownObjects3D.keys():
                # Remove
                def onRemove3D(_name):
                    label = self._shownObjects3D.pop(_name)
                    self._renderMgr.removeObject(label)
                    self._update_rendering()
                removeAction = menu.addAction("Remove %s from 3D view" % objectLabel)
                removeAction.triggered.connect( partial(onRemove3D, objectLabel) )
            else:
                # Show
                def onShow3D(_name):
                    label = self._renderMgr.addObject()
                    self._shownObjects3D[_name] = label
                    self._update_rendering()
                showAction = menu.addAction("Show 3D %s" % objectLabel)
                showAction.triggered.connect( partial(onShow3D, objectLabel ) )

            # Export mesh

            exportAction = menu.addAction("Export mesh for %s" % objectLabel)
            exportAction.triggered.connect( partial(self._onContextMenuExportMesh, objectLabel) )

        action = menu.exec_(globalWindowCoordinate)

    def _update_rendering(self):
        if not self.render:
            return

        op = self.topLevelOperatorView
        seg_volume = op.Output[:].wait().squeeze()
        print("seg volume shape:", seg_volume.shape)
        if not self._renderMgr.ready:
            self._renderMgr.setup(seg_volume.shape)

        # remove nonexistent objects
        # TODO: replace that with removing objects with an index < max(topLevelOperatorView.NodeLabelsCache)
        # self._shownObjects3D = dict((k, v) for k, v in self._shownObjects3D.items()
        #                           if k in list(op.MST.value.object_lut.keys()))

        maxNodeValue = numpy.max(seg_volume)
        print("THE CURRENT MAX OBJECT:", maxNodeValue)
        self._shownObjects3D = dict((k, v) for k, v in self._shownObjects3D.items() if k < maxNodeValue)

        lut = numpy.zeros((maxNodeValue+1,), dtype=numpy.uint32)

        label_name_map = {}
        for name, label in self._shownObjects3D.items():
            lut[name] = name #for voxelwise relabeling
            label_name_map[name]=label
            label_name_map[label] = name


        '''
            objectSupervoxels =
            objectSupervoxels = op.MST.value.object_lut[name]
            lut[objectSupervoxels] = label
            label_name_map[label] = name
            label_name_map[name] = label

        if self._showSegmentationIn3D:
            # Add segmentation as label, which is green
            label_name_map[self._segmentation_3d_label] = CURRENT_SEGMENTATION_NAME
            label_name_map[CURRENT_SEGMENTATION_NAME] = self._segmentation_3d_label
            lut[:] = numpy.where( op.MST.value.getSuperVoxelSeg() == 2, self._segmentation_3d_label, lut )
        '''

        self._renderMgr.volume = lut[seg_volume], label_name_map  # (Advanced indexing)
        self._update_colors()
        self._renderMgr.update()

    def _onContextMenuExportMesh(self, objectLabel):
        print("exporting mesh of object", objectLabel)

    def _update_colors(self):
        op = self.topLevelOperatorView
        seg_layer = self.getLayerByName("Multicut Segmentation")
        ctable = seg_layer.colorTable

        for name, label in self._shownObjects3D.items():
            #color = QColor(ctable[name])
            color = QColor(255, 0, 0)
            color = (old_div(color.red(), 255.0), old_div(color.green(), 255.0), old_div(color.blue(), 255.0))
            self._renderMgr.setColor(label, color)


    def configure_gui_from_operator(self, *args):
        EdgeTrainingGui.configure_gui_from_operator(self)
        MulticutGuiMixin.configure_gui_from_operator(self)
    
    def configure_operator_from_gui(self):
        EdgeTrainingGui.configure_operator_from_gui(self)
        MulticutGuiMixin.configure_operator_from_gui(self)
