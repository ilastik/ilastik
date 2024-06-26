from functools import partial
import logging
from past.utils import old_div
import os

import numpy
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QAction, QDialog, QMenu
from PyQt5.QtGui import QColor, QIcon

# HCI
from volumina.api import LazyflowSource, AlphaModulatedLayer, GrayscaleLayer, ColortableLayer
from volumina.utility import ShortcutManager, preferences

from lazyflow.utility import PathComponents
from lazyflow.roi import slicing_to_string
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.ioOperators import OpInputDataReader

from ilastik.applets.labeling.labelingGui import LabelingGui
from ilastik.applets.pixelClassification import pixelClassificationGui
from ilastik.applets.pixelClassification.suggestFeaturesDialog import SuggestFeaturesDialog
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility import bind

# ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.utility.gui import threadRouted
from ilastik.widgets.stackFileSelectionWidget import SubvolumeSelectionDlg
from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui, SubvolumeSelectionDlg
from ilastik.shell.gui.variableImportanceDialog import VariableImportanceDialog

# Loggers
logger = logging.getLogger(__name__)

try:
    from volumina.view3d.volumeRendering import RenderingManager
except ImportError:
    logger.debug("Can't import volumina.view3d.volumeRendering.RenderingManager")


class VoxelSegmentationGui(LabelingGui):
    def __init__(self, parentApplet, topLevelOperatorView, labelingDrawerUiPath=None):
        self.parentApplet = parentApplet
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = topLevelOperatorView.LabelInputs
        labelSlots.labelOutput = topLevelOperatorView.LabelImages
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelPipeline.DeleteLabel
        labelSlots.labelNames = topLevelOperatorView.LabelNames

        self.__cleanup_fns = []

        # We provide our own UI file (which adds an extra control for interactive mode)
        if labelingDrawerUiPath is None:
            labelingDrawerUiPath = os.path.dirname(__file__) + "/labelingDrawer.ui"

        # Base class init
        super(VoxelSegmentationGui, self).__init__(parentApplet, labelSlots, topLevelOperatorView, labelingDrawerUiPath)

        self.topLevelOperatorView = topLevelOperatorView

        self.interactiveModeActive = False
        # Immediately update our interactive state
        self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)

        self._currentlySavingPredictions = False

        self._showSegmentationIn3D = False

        self.labelingDrawerUi.labelListView.support_merges = True

        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.toggleInteractive)

        self.labelingDrawerUi.suggestFeaturesButton.clicked.connect(self.show_suggest_features_dialog)
        self.labelingDrawerUi.suggestFeaturesButton.setEnabled(False)

        # Always force at least two labels because it makes no sense to have less here
        self.forceAtLeastTwoLabels(True)

        self.topLevelOperatorView.LabelNames.notifyDirty(bind(self.handleLabelSelectionChange))
        self.__cleanup_fns.append(
            partial(self.topLevelOperatorView.LabelNames.unregisterDirty, bind(self.handleLabelSelectionChange))
        )

        self._initShortcuts()

        self._bookmarks_window = pixelClassificationGui.BookmarksWindow(self, self.topLevelOperatorView)

        # FIXME: We MUST NOT enable the render manager by default,
        #        since it will drastically slow down the app for large volumes.
        #        For now, we leave it off by default.
        #        To re-enable rendering, we need to allow the user to render a segmentation
        #        and then initialize the render manager on-the-fly.
        #        (We might want to warn the user if her volume is not small.)
        self.render = False
        self._renderMgr = None
        self._renderedLayers = {}  # (layer name, label number)

        # Always off for now (see note above)
        if self.render:
            # try:
            self._renderMgr = RenderingManager(self.editor.view3d)
            # except:
            # self.render = False

        # toggle interactive mode according to freezePredictions.value
        self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)

        def FreezePredDirty():
            self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)

        # listen to freezePrediction changes
        # self.topLevelOperatorView.FreezePredictions.notifyDirty(bind(FreezePredDirty))
        self.__cleanup_fns.append(
            partial(self.topLevelOperatorView.FreezePredictions.unregisterDirty, bind(FreezePredDirty))
        )

        def SelectBestAnnotationPlane():
            if self.mostUncertainPlanes is None and self.mostUncertainAxis is None:
                axis, indices = self.topLevelOperatorView.BestAnnotationPlane.value
                # Axes from the classifiation operator are in the order z y x while volumina has x y z
                axis = [2, 1, 0][axis]

                self.mostUncertainAxis = axis
                self.mostUncertainPlanes = indices

            # Pop most uncertain plane from list
            index, self.mostUncertainPlanes = self.mostUncertainPlanes[-1], self.mostUncertainPlanes[:-1]
            # Display the plane
            self.editor.navCtrl.changeSliceAbsolute(index, self.mostUncertainAxis)

        def resetBestPlanes():
            logger.info("resetting planes")
            self.mostUncertainPlanes = None
            self.mostUncertainAxis = None

        resetBestPlanes()
        self.topLevelOperatorView.FreezePredictions.notifyDirty(bind(resetBestPlanes))
        self.topLevelOperatorView.LabelImages.notifyDirty(bind(resetBestPlanes))
        self.labelingDrawerUi.bestAnnotationPlaneButton.clicked.connect(SelectBestAnnotationPlane)

    def initSuggestFeaturesDialog(self):
        thisOpFeatureSelection = (
            self.topLevelOperatorView.parent.featureSelectionApplet.topLevelOperator.innerOperators[0]
        )
        return SuggestFeaturesDialog(thisOpFeatureSelection, self, self.labelListData, self)

    def menus(self):
        menus = super().menus()

        advanced_menu = QMenu("Advanced", parent=self)

        def handleClassifierAction():
            dlg = pixelClassificationGui.ClassifierSelectionDlg(self.topLevelOperatorView, parent=self)
            dlg.exec_()

        classifier_action = advanced_menu.addAction("Classifier...")
        classifier_action.triggered.connect(handleClassifierAction)

        def showVarImpDlg():
            varImpDlg = VariableImportanceDialog(
                self.topLevelOperatorView.Classifier.value.named_importances, parent=self
            )
            varImpDlg.exec_()

        advanced_menu.addAction("Variable Importance Table").triggered.connect(showVarImpDlg)

        def handleImportLabelsAction():
            # Find the directory of the most recently opened image file
            mostRecentImageFile = preferences.get("DataSelection", "recent image")
            if mostRecentImageFile is not None:
                defaultDirectory = os.path.split(mostRecentImageFile)[0]
            else:
                defaultDirectory = os.path.expanduser("~")
            fileNames = DataSelectionGui.getImageFileNamesToOpen(self, defaultDirectory)
            fileNames = list(map(str, fileNames))

            # For now, we require a single hdf5 file
            if len(fileNames) > 1:
                QMessageBox.critical(self, "Too many files", "Labels must be contained in a single hdf5 volume.")
                return
            if len(fileNames) == 0:
                # user cancelled
                return

            file_path = fileNames[0]
            internal_paths = DataSelectionGui.getPossibleInternalPaths(file_path)
            if len(internal_paths) == 0:
                QMessageBox.critical(self, "No volumes in file", "Couldn't find a suitable dataset in your hdf5 file.")
                return
            if len(internal_paths) == 1:
                internal_path = internal_paths[0]
            else:
                dlg = SubvolumeSelectionDlg(internal_paths, self)
                if dlg.exec_() == QDialog.Rejected:
                    return
                selected_index = dlg.combo.currentIndex()
                internal_path = str(internal_paths[selected_index])

            path_components = PathComponents(file_path)
            path_components.internalPath = str(internal_path)

            try:
                top_op = self.topLevelOperatorView
                opReader = OpInputDataReader(parent=top_op.parent)
                opReader.FilePath.setValue(path_components.totalPath())

                # Reorder the axes
                op5 = OpReorderAxes(parent=top_op.parent)
                op5.AxisOrder.setValue(top_op.LabelInputs.meta.getAxisKeys())
                op5.Input.connect(opReader.Output)

                # Finally, import the labels
                top_op.importLabels(top_op.current_view_index(), op5.Output)

            finally:
                op5.cleanUp()
                opReader.cleanUp()

        def print_label_blocks(sorted_axis):
            sorted_column = self.topLevelOperatorView.InputImages.meta.getAxisKeys().index(sorted_axis)

            input_shape = self.topLevelOperatorView.InputImages.meta.shape
            label_block_slicings = self.topLevelOperatorView.NonzeroLabelBlocks.value

            sorted_block_slicings = sorted(label_block_slicings, key=lambda s: s[sorted_column])

            for slicing in sorted_block_slicings:
                # Omit channel
                order = "".join(self.topLevelOperatorView.InputImages.meta.getAxisKeys())
                line = order[:-1].upper() + ": "
                line += slicing_to_string(slicing[:-1], input_shape)

        labels_submenu = QMenu("Labels")
        self.labels_submenu = labels_submenu  # Must retain this reference or else it gets auto-deleted.

        import_labels_action = labels_submenu.addAction("Import Labels...")
        import_labels_action.triggered.connect(handleImportLabelsAction)

        self.print_labels_submenu = QMenu("Print Label Blocks")
        labels_submenu.addMenu(self.print_labels_submenu)

        for axis in self.topLevelOperatorView.InputImages.meta.getAxisKeys()[:-1]:
            self.print_labels_submenu.addAction("Sort by {}".format(axis.upper())).triggered.connect(
                partial(print_label_blocks, axis)
            )

        advanced_menu.addMenu(labels_submenu)

        if ilastik_config.getboolean("ilastik", "debug"):

            def showBookmarksWindow():
                self._bookmarks_window.show()

            advanced_menu.addAction("Bookmarks...").triggered.connect(showBookmarksWindow)

        if self.render:
            showSeg3DAction = advanced_menu.addAction("Show Supervoxel Segmentation in 3D")
            showSeg3DAction.setCheckable(True)
            showSeg3DAction.setChecked(self._showSegmentationIn3D)
            showSeg3DAction.triggered.connect(self._toggleSegmentation3D)

        menus += [advanced_menu]
        return menus

    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super().setupLayers()

        ActionInfo = ShortcutManager.ActionInfo

        if ilastik_config.getboolean("ilastik", "debug"):

            # Add the label projection layer.
            labelProjectionSlot = self.topLevelOperatorView.opLabelPipeline.opLabelArray.Projection2D
            if labelProjectionSlot.ready():
                projectionSrc = LazyflowSource(labelProjectionSlot)
                try:
                    # This colortable requires matplotlib
                    from volumina.colortables import jet

                    projectionLayer = ColortableLayer(
                        projectionSrc, colorTable=[QColor(0, 0, 0, 128).rgba()] + jet(N=255), normalize=(0.0, 1.0)
                    )
                except (ImportError, RuntimeError):
                    pass
                else:
                    projectionLayer.name = "Label Projection"
                    projectionLayer.visible = False
                    projectionLayer.opacity = 1.0
                    layers.append(projectionLayer)

        # Show the mask over everything except labels
        maskSlot = self.topLevelOperatorView.PredictionMasks
        if maskSlot.ready():
            maskLayer = self._create_binary_mask_layer_from_slot(maskSlot)
            maskLayer.name = "Mask"
            maskLayer.visible = True
            maskLayer.opacity = 1.0
            layers.append(maskLayer)

        # Add the uncertainty estimate layer
        uncertaintySlot = self.topLevelOperatorView.UncertaintyEstimate
        if uncertaintySlot.ready():
            uncertaintySrc = LazyflowSource(uncertaintySlot)
            uncertaintyLayer = AlphaModulatedLayer(uncertaintySrc, tintColor=QColor(Qt.cyan), normalize=(0.0, 1.0))
            uncertaintyLayer.name = "Uncertainty"
            uncertaintyLayer.visible = False
            uncertaintyLayer.opacity = 1.0
            uncertaintyLayer.shortcutRegistration = (
                "u",
                ActionInfo(
                    "Prediction Layers",
                    "Uncertainty",
                    "Show/Hide Uncertainty",
                    uncertaintyLayer.toggleVisible,
                    self.viewerControlWidget(),
                    uncertaintyLayer,
                ),
            )
            layers.append(uncertaintyLayer)

        # Add the top uncertainty estimate layer
        topUncertaintySlot = self.topLevelOperatorView.TopUncertaintyEstimate
        if topUncertaintySlot.ready():
            topUncertaintySrc = LazyflowSource(topUncertaintySlot)
            topUncertaintyLayer = AlphaModulatedLayer(
                topUncertaintySrc, tintColor=QColor(Qt.cyan), normalize=(0.0, 1.0)
            )
            topUncertaintyLayer.name = "topUncertainty"
            topUncertaintyLayer.visible = True
            topUncertaintyLayer.opacity = 1.0
            topUncertaintyLayer.shortcutRegistration = (
                "u",
                ActionInfo(
                    "Prediction Layers",
                    "topUncertainty",
                    "Show/Hide topUncertainty",
                    topUncertaintyLayer.toggleVisible,
                    self.viewerControlWidget(),
                    topUncertaintyLayer,
                ),
            )
            layers.insert(0, topUncertaintyLayer)

        labels = self.labelListData

        # Add each of the segmentations
        for channel, segmentationSlot in enumerate(self.topLevelOperatorView.SegmentationChannels):
            if segmentationSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                segsrc = LazyflowSource(segmentationSlot)
                segLayer = AlphaModulatedLayer(segsrc, tintColor=ref_label.pmapColor(), normalize=(0.0, 1.0))

                segLayer.opacity = 1
                segLayer.visible = False  # self.labelingDrawerUi.liveUpdateButton.isChecked()
                segLayer.visibleChanged.connect(self.updateShowSegmentationCheckbox)

                def setLayerColor(c, segLayer_=segLayer, initializing=False):
                    if not initializing and segLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    segLayer_.tintColor = c
                    self._update_rendering()

                def setSegLayerName(n, segLayer_=segLayer, initializing=False):
                    if not initializing and segLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    oldname = segLayer_.name
                    newName = "Segmentation (%s)" % n
                    segLayer_.name = newName
                    if not self.render:
                        return
                    if oldname in self._renderedLayers:
                        label = self._renderedLayers.pop(oldname)
                        self._renderedLayers[newName] = label

                setSegLayerName(ref_label.name, initializing=True)

                ref_label.pmapColorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setSegLayerName)
                # check if layer is 3d before adding the "Toggle 3D" option
                # this check is done this way to match the VolumeRenderer, in
                # case different 3d-axistags should be rendered like t-x-y
                # _axiskeys = segmentationSlot.meta.getAxisKeys()
                if len(segmentationSlot.meta.shape) == 4:
                    # the Renderer will cut out the last shape-dimension, so
                    # we're checking for 4 dimensions
                    self._setup_contexts(segLayer)
                layers.append(segLayer)

        # Add each of the predictions
        for channel, predictionSlot in enumerate(self.topLevelOperatorView.PredictionProbabilityChannels):
            if predictionSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                predictsrc = LazyflowSource(predictionSlot)
                predictLayer = AlphaModulatedLayer(predictsrc, tintColor=ref_label.pmapColor(), normalize=(0.0, 1.0))
                predictLayer.opacity = 0.25
                predictLayer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                predictLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                def setLayerColor(c, predictLayer_=predictLayer, initializing=False):
                    if not initializing and predictLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    predictLayer_.tintColor = c

                def setPredLayerName(n, predictLayer_=predictLayer, initializing=False):
                    if not initializing and predictLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    newName = "Prediction for %s" % n
                    predictLayer_.name = newName

                setPredLayerName(ref_label.name, initializing=True)
                ref_label.pmapColorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setPredLayerName)
                layers.append(predictLayer)

        # Add the raw data last (on the bottom)
        inputDataSlot = self.topLevelOperatorView.InputImages
        if inputDataSlot.ready():
            inputLayer = self.createStandardLayerFromSlot(inputDataSlot)
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            # the flag window_leveling is used to determine if the contrast
            # of the layer is adjustable
            if isinstance(inputLayer, GrayscaleLayer):
                inputLayer.window_leveling = True
            else:
                inputLayer.window_leveling = False

            inputLayer.shortcutRegistration = (
                "i",
                ActionInfo(
                    "Prediction Layers",
                    "Bring Input To Top/Bottom",
                    "Bring Input To Top/Bottom",
                    partial(self.layerstack.toggleTopToBottom, inputLayer),
                    self.viewerControlWidget(),
                    inputLayer,
                ),
            )
            layers.append(inputLayer)

            # The thresholding button can only be used if the data is displayed as grayscale.
            if inputLayer.window_leveling:
                self.labelingDrawerUi.thresToolButton.show()
            else:
                self.labelingDrawerUi.thresToolButton.hide()

        self.handleLabelSelectionChange()

        superVoxelSlot = self.topLevelOperatorView.SupervoxelBoundaries
        if superVoxelSlot.ready():
            layer = AlphaModulatedLayer(
                LazyflowSource(superVoxelSlot), tintColor=QColor(Qt.black), normalize=(0.0, 1.0)
            )
            layer.name = "SLIC segmentation"
            layer.visible = True
            layer.opacity = 0.3
            layers.insert(1, layer)
        return layers

    def _toggleSegmentation3D(self):
        self._showSegmentationIn3D = not self._showSegmentationIn3D
        if self._showSegmentationIn3D:
            self._segmentation_3d_label = self._renderMgr.addObject()
        else:
            self._renderMgr.removeObject(self._segmentation_3d_label)
            self._segmentation_3d_label = None
        self._update_rendering()

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super().stopAndCleanUp()

    # methods below copy pasted from pixelclassificationgui

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget(self):
        return self

    def viewerControlWidget(self):
        return self._viewerControlUi

    ###########################################
    ###########################################

    def show_suggest_features_dialog(self):
        suggestFeaturesDialog = self.initSuggestFeaturesDialog()
        suggestFeaturesDialog.resultSelected.connect(self.update_features_from_dialog)
        suggestFeaturesDialog.open()

    def update_features_from_dialog(self, feature_matrix, compute_in_2d):
        if self.topLevelOperatorView.name == "OpPixelClassification":
            thisOpFeatureSelection = (
                self.topLevelOperatorView.parent.featureSelectionApplet.topLevelOperator.innerOperators[0]
            )
        elif self.topLevelOperatorView.name == "OpPixelClassification0":
            thisOpFeatureSelection = self.topLevelOperatorView.parent.featureSelectionApplets[
                0
            ].topLevelOperator.innerOperators[0]
        elif self.topLevelOperatorView.name == "OpPixelClassification1":
            thisOpFeatureSelection = self.topLevelOperatorView.parent.featureSelectionApplets[
                1
            ].topLevelOperator.innerOperators[0]
        elif self.topLevelOperatorView.name == "OpPixelClassification2":
            thisOpFeatureSelection = self.topLevelOperatorView.parent.featureSelectionApplets[
                2
            ].topLevelOperator.innerOperators[0]
        elif self.topLevelOperatorView.name == "OpPixelClassification3":
            thisOpFeatureSelection = self.topLevelOperatorView.parent.featureSelectionApplets[
                3
            ].topLevelOperator.innerOperators[0]
        else:
            raise NotImplementedError

        thisOpFeatureSelection.ComputeIn2d.setValue(compute_in_2d)
        thisOpFeatureSelection.SelectionMatrix.setValue(self.featSelDlg.selected_features_matrix)

    def initViewerControlUi(self):
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi(os.path.join(localDir, "viewerControls.ui"))

        # Connect checkboxes
        def nextCheckState(checkbox):
            checkbox.setChecked(not checkbox.isChecked())

        self._viewerControlUi.checkShowPredictions.nextCheckState = partial(
            nextCheckState, self._viewerControlUi.checkShowPredictions
        )
        self._viewerControlUi.checkShowSegmentation.nextCheckState = partial(
            nextCheckState, self._viewerControlUi.checkShowSegmentation
        )

        self._viewerControlUi.checkShowPredictions.clicked.connect(self.handleShowPredictionsClicked)
        self._viewerControlUi.checkShowSegmentation.clicked.connect(self.handleShowSegmentationClicked)

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        self._viewerControlUi.viewerControls.setupConnections(model)

    def _initShortcuts(self):
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcutGroupName = "Predictions"

        mgr.register(
            "p",
            ActionInfo(
                shortcutGroupName,
                "Toggle Prediction",
                "Toggle Prediction Layer Visibility",
                self._viewerControlUi.checkShowPredictions.click,
                self._viewerControlUi.checkShowPredictions,
                self._viewerControlUi.checkShowPredictions,
            ),
        )

        mgr.register(
            "s",
            ActionInfo(
                shortcutGroupName,
                "Toggle Segmentaton",
                "Toggle Segmentaton Layer Visibility",
                self._viewerControlUi.checkShowSegmentation.click,
                self._viewerControlUi.checkShowSegmentation,
                self._viewerControlUi.checkShowSegmentation,
            ),
        )

        mgr.register(
            "l",
            ActionInfo(
                shortcutGroupName,
                "Live Prediction",
                "Toggle Live Prediction Mode",
                self.labelingDrawerUi.liveUpdateButton.toggle,
                self.labelingDrawerUi.liveUpdateButton,
                self.labelingDrawerUi.liveUpdateButton,
            ),
        )

    def _setup_contexts(self, layer):
        def callback(pos, clayer=layer):
            name = clayer.name
            if name in self._renderedLayers:
                label = self._renderedLayers.pop(name)
                self._renderMgr.removeObject(label)
                self._update_rendering()
            else:
                label = self._renderMgr.addObject()
                self._renderedLayers[clayer.name] = label
                self._update_rendering()

        if self.render:
            layer.contexts.append(QAction("Toggle 3D rendering", None, triggered=callback))

    def toggleInteractive(self, checked):
        logger.info("toggling interactive mode to '%r'" % checked)

        if checked == True:
            if (
                not self.topLevelOperatorView.FeatureImages.ready()
                or self.topLevelOperatorView.FeatureImages.meta.shape == None
            ):
                self.labelingDrawerUi.liveUpdateButton.setChecked(False)
                self.labelingDrawerUi.suggestFeaturesButton.setEnabled(False)
                mexBox = QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        # If we're changing modes, enable/disable our controls and other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.labelingDrawerUi.suggestFeaturesButton.setEnabled(False)
                self.labelingDrawerUi.labelListView.allowDelete = False
                self.labelingDrawerUi.AddLabelButton.setEnabled(False)
            else:
                num_label_classes = self._labelControlUi.labelListModel.rowCount()
                self.labelingDrawerUi.labelListView.allowDelete = num_label_classes > self.minLabelNumber
                self.labelingDrawerUi.AddLabelButton.setEnabled((num_label_classes < self.maxLabelNumber))
                self.labelingDrawerUi.suggestFeaturesButton.setEnabled(True)

        self.interactiveModeActive = checked

        self.topLevelOperatorView.FreezePredictions.setValue(not checked)
        self.labelingDrawerUi.liveUpdateButton.setChecked(checked)
        # self.labelingDrawerUi.suggestFeaturesButton.setEnabled(checked)
        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self._viewerControlUi.checkShowPredictions.setChecked(True)
            self.handleShowPredictionsClicked()

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested()

    @pyqtSlot()
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

    @pyqtSlot()
    def handleShowSegmentationClicked(self):
        checked = self._viewerControlUi.checkShowSegmentation.isChecked()
        for layer in self.layerstack:
            if "Segmentation" in layer.name:
                layer.visible = checked

    @pyqtSlot()
    def updateShowPredictionCheckbox(self):
        predictLayerCount = 0
        visibleCount = 0
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                predictLayerCount += 1
                if layer.visible:
                    visibleCount += 1

        if visibleCount == 0:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Checked)
        else:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.PartiallyChecked)

    @pyqtSlot()
    def updateShowSegmentationCheckbox(self):
        segLayerCount = 0
        visibleCount = 0
        for layer in self.layerstack:
            if "Segmentation" in layer.name:
                segLayerCount += 1
                if layer.visible:
                    visibleCount += 1

        if visibleCount == 0:
            self._viewerControlUi.checkShowSegmentation.setCheckState(Qt.Unchecked)
        elif segLayerCount == visibleCount:
            self._viewerControlUi.checkShowSegmentation.setCheckState(Qt.Checked)
        else:
            self._viewerControlUi.checkShowSegmentation.setCheckState(Qt.PartiallyChecked)

    @pyqtSlot()
    @threadRouted
    def handleLabelSelectionChange(self):
        enabled = False
        if self.topLevelOperatorView.LabelNames.ready():
            enabled = True
            enabled &= len(self.topLevelOperatorView.LabelNames.value) >= 2
            enabled &= numpy.all(numpy.asarray(self.topLevelOperatorView.CachedFeatureImages.meta.shape) > 0)
            # FIXME: also check that each label has scribbles?

        if not enabled:
            self.labelingDrawerUi.liveUpdateButton.setChecked(False)
            self._viewerControlUi.checkShowPredictions.setChecked(False)
            self._viewerControlUi.checkShowSegmentation.setChecked(False)
            self.handleShowPredictionsClicked()
            self.handleShowSegmentationClicked()

        self.labelingDrawerUi.liveUpdateButton.setEnabled(enabled)
        self.labelingDrawerUi.suggestFeaturesButton.setEnabled(enabled)
        self._viewerControlUi.checkShowPredictions.setEnabled(enabled)
        self._viewerControlUi.checkShowSegmentation.setEnabled(enabled)

    def _getNext(self, slot, parentFun, transform=None):
        numLabels = self.labelListData.rowCount()
        value = slot.value
        if numLabels < len(value):
            result = value[numLabels]
            if transform is not None:
                result = transform(result)
            return result
        else:
            return parentFun()

    def _onLabelChanged(self, parentFun, mapf, slot):
        parentFun()
        new = list(map(mapf, self.labelListData))
        old = slot.value
        slot.setValue(pixelClassificationGui._listReplace(old, new))

    def _onLabelRemoved(self, parent, start, end):
        # Call the base class to update the operator.
        super()._onLabelRemoved(parent, start, end)

        # Keep colors in sync with names
        # (If we deleted a name, delete its corresponding colors, too.)
        op = self.topLevelOperatorView
        if len(op.PmapColors.value) > len(op.LabelNames.value):
            for slot in (op.LabelColors, op.PmapColors):
                value = slot.value
                value.pop(start)
                # Force dirty propagation even though the list id is unchanged.
                slot.setValue(value, check_changed=False)

    def getNextLabelName(self):
        return self._getNext(self.topLevelOperatorView.LabelNames, super().getNextLabelName)

    def getNextLabelColor(self):
        return self._getNext(self.topLevelOperatorView.LabelColors, super().getNextLabelColor, lambda x: QColor(*x))

    def getNextPmapColor(self):
        return self._getNext(self.topLevelOperatorView.PmapColors, super().getNextPmapColor, lambda x: QColor(*x))

    def onLabelNameChanged(self):
        self._onLabelChanged(super().onLabelNameChanged, lambda l: l.name, self.topLevelOperatorView.LabelNames)

    def onLabelColorChanged(self):
        self._onLabelChanged(
            super().onLabelColorChanged,
            lambda l: (l.brushColor().red(), l.brushColor().green(), l.brushColor().blue()),
            self.topLevelOperatorView.LabelColors,
        )

    def onPmapColorChanged(self):
        self._onLabelChanged(
            super().onPmapColorChanged,
            lambda l: (l.pmapColor().red(), l.pmapColor().green(), l.pmapColor().blue()),
            self.topLevelOperatorView.PmapColors,
        )

    def _update_rendering(self):
        if not self.render:
            return
        shape = self.topLevelOperatorView.InputImages.meta.shape[1:4]
        if len(shape) != 5:
            # this might be a 2D image, no need for updating any 3D stuff
            return

        time = self.editor.posModel.slicingPos5D[0]
        if not self._renderMgr.ready:
            self._renderMgr.setup(shape)

        layernames = set(layer.name for layer in self.layerstack)
        self._renderedLayers = dict((k, v) for k, v in self._renderedLayers.items() if k in layernames)

        newvolume = numpy.zeros(shape, dtype=numpy.uint8)
        for layer in self.layerstack:
            try:
                label = self._renderedLayers[layer.name]
            except KeyError:
                continue
            for ds in layer.datasources:
                vol = ds.dataSlot.value[time, ..., 0]
                indices = numpy.where(vol != 0)
                newvolume[indices] = label

        self._renderMgr.volume = newvolume
        self._update_colors()
        self._renderMgr.update()

    def _update_colors(self):
        for layer in self.layerstack:
            try:
                label = self._renderedLayers[layer.name]
            except KeyError:
                continue
            color = layer.tintColor
            color = (old_div(color.red(), 255.0), old_div(color.green(), 255.0), old_div(color.blue(), 255.0))
            self._renderMgr.setColor(label, color)
