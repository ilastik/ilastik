from qtpy.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QSpacerItem, QSizePolicy, QCheckBox
from qtpy.QtCore import Signal

from lazyflow.slot import valueContext
from ilastik.applets.edgeTraining.edgeTrainingGui import EdgeTrainingMixin
from ilastik.applets.multicut.multicutGui import MulticutGuiMixin
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
import ilastik.utility.gui as guiutil


class EdgeTrainingWithMulticutGui(MulticutGuiMixin, EdgeTrainingMixin, LayerViewerGui):

    multicutUpdated = Signal()

    def __init__(self, parentApplet, topLevelOperatorView):
        self.__cleanup_fns = []
        super().__init__(parentApplet, topLevelOperatorView, crosshair=False)

    def initAppletDrawerUi(self):

        self.train_edge_clf_box = QCheckBox(
            text="Train edge classifier",
            toolTip="Manually select features and train a random forest classifier on them, to predict boundary probabilities. If left unchecked, training will be skipped, and probabilities will be calculated based on the mean probability along edges. This produces good results for clear boundaries.",
            checked=False,
        )

        training_controls = EdgeTrainingMixin.createDrawerControls(self)
        training_controls.layout().setContentsMargins(5, 0, 5, 0)
        training_layout = QVBoxLayout()
        training_layout.addWidget(training_controls)
        training_layout.setContentsMargins(0, 15, 0, 0)
        training_box = QGroupBox("Training", parent=self)
        training_box.setLayout(training_layout)
        training_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        training_box.setEnabled(self.train_edge_clf_box.isChecked())
        self._training_box = training_box

        multicut_controls = MulticutGuiMixin.createDrawerControls(self)
        multicut_controls.layout().setContentsMargins(5, 0, 5, 0)
        multicut_layout = QVBoxLayout()
        multicut_layout.addWidget(multicut_controls)
        multicut_layout.setContentsMargins(0, 15, 0, 0)
        multicut_box = QGroupBox("Multicut", parent=self)
        multicut_box.setLayout(multicut_layout)
        multicut_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        multicut_box.setEnabled(True)

        op = self.topLevelOperatorView
        multicut_required_slots = (op.Superpixels, op.Rag, op.EdgeProbabilities, op.EdgeProbabilitiesDict)
        self.__cleanup_fns.append(guiutil.enable_when_ready(multicut_box, multicut_required_slots))

        self.train_edge_clf_box.toggled.connect(self._handle_train_edge_clf_box_clicked)

        drawer_layout = QVBoxLayout()
        drawer_layout.addWidget(self.train_edge_clf_box)
        drawer_layout.addWidget(training_box)
        drawer_layout.addWidget(multicut_box)
        drawer_layout.setSpacing(2)
        drawer_layout.setContentsMargins(5, 5, 5, 5)
        drawer_layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self._drawer = QWidget(parent=self)
        self._drawer.setLayout(drawer_layout)

        # GUI will be initialized in _after_init()
        # self.configure_gui_from_operator()

    def appletDrawer(self):
        return self._drawer

    def secondaryControlsWidget(self):
        return None

    @guiutil.threadRouted
    def _handle_train_edge_clf_box_clicked(self, checked):
        self._training_box.setEnabled(checked)
        op = self.topLevelOperatorView
        op.TrainRandomForest.setValue(checked)
        if not checked:
            op.FreezeClassifier.setValue(True)
        self.updateAllLayers()
        # optimize rendering - showing multiple perfectly overlaying superpixel
        # edge layers, noticeably slows down rendering.
        # -> Show segmentation edges layer only when no RF is trained as it will
        # have the perfectly overlapping edgelabels layer.
        segmentation_edges_layer = self.getLayerByName("Superpixel Edges")
        if segmentation_edges_layer:
            segmentation_edges_layer.visible = not checked

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base classes
        super().stopAndCleanUp()

    def setupLayers(self):
        layers = []
        edgeTrainingLayers = EdgeTrainingMixin.setupLayers(self)

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

    def configure_gui_from_operator(self, *args):
        EdgeTrainingMixin.configure_gui_from_operator(self)
        MulticutGuiMixin.configure_gui_from_operator(self)
        self.train_edge_clf_box.setChecked(self.topLevelOperatorView.TrainRandomForest.value)

    def configure_operator_from_gui(self):
        EdgeTrainingMixin.configure_operator_from_gui(self)
        MulticutGuiMixin.configure_operator_from_gui(self)

    # TODO More elegant way to make multicut compute upon pressing Update button.
    def _update_multicut_views(self):
        """
        Overrides from MulticutGuiMixin. FreezeClassifier is unfrozen
        here, because the mixin should not be modified to require more
        slots than the ones available from OpMulticut. which
        FreezeClassifier is not).
        """

        with valueContext(self.topLevelOperatorView.FreezeClassifier, False):
            super()._update_multicut_views()

        self.multicutUpdated.emit()
