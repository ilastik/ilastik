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
# 		   http://ilastik.org/license.html
###############################################################################
# Built-in
import os
from typing import Optional
import logging
from collections import OrderedDict
from functools import partial

# Third-party
import numpy
from qtpy import uic
from qtpy.QtCore import Qt, Slot, QSize
from qtpy.QtWidgets import (
    QMessageBox,
    QVBoxLayout,
    QDialogButtonBox,
    QListWidget,
    QListWidgetItem,
    QAction,
    QPushButton,
    QLineEdit,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QSizePolicy,
    QMenu,
)
from qtpy.QtGui import QColor


# HCI
from ilastik.applets.pixelClassification.opPixelClassification import OpPixelClassification
from volumina.api import createDataSource, AlphaModulatedLayer, GrayscaleLayer, ColortableLayer
from volumina.utility import ShortcutManager

from lazyflow.utility import PathComponents
from lazyflow.roi import slicing_to_string
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow.operators import OpFeatureMatrixCache

# ilastik
from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted, silent_qobject
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.labeling.labelingGui import LabelingGui, LabelingSlots
from ilastik.applets.dataSelection.dataSelectionGui import DataSelectionGui, SubvolumeSelectionDlg
from ilastik.widgets.ImageFileDialog import ImageFileDialog
from ilastik.shell.gui.variableImportanceDialog import VariableImportanceDialog
from ilastik.applets.dataSelection import DatasetInfo

# import IPython
from .suggestFeaturesDialog import SuggestFeaturesDialog

try:
    from volumina.view3d.volumeRendering import RenderingManager
except ImportError:
    pass

# Loggers
logger = logging.getLogger(__name__)


def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new) :]
    else:
        return new


class ClassifierSelectionDlg(QDialog):
    """
    A simple window to let the user select a classifier type.
    """

    def __init__(self, opPixelClassification, parent):
        super(QDialog, self).__init__(parent=parent)
        self._op = opPixelClassification
        classifier_listwidget = QListWidget(parent=self)
        classifier_listwidget.setSelectionMode(QListWidget.SingleSelection)

        classifier_factories = self._get_available_classifier_factories()
        for name, classifier_factory in list(classifier_factories.items()):
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, classifier_factory)
            classifier_listwidget.addItem(item)

        buttonbox = QDialogButtonBox(Qt.Horizontal, parent=self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(classifier_listwidget)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        self.setWindowTitle("Select Classifier Type")

        # Save members
        self._classifier_listwidget = classifier_listwidget

    def _get_available_classifier_factories(self):
        # FIXME: Replace this logic with a proper plugin mechanism
        from lazyflow.classifiers import (
            VigraRfLazyflowClassifierFactory,
            SklearnLazyflowClassifierFactory,
            ParallelVigraRfLazyflowClassifierFactory,
            VigraRfPixelwiseClassifierFactory,
            LazyflowVectorwiseClassifierFactoryABC,
            LazyflowPixelwiseClassifierFactoryABC,
        )

        classifiers = OrderedDict()
        classifiers["Parallel Random Forest (VIGRA)"] = ParallelVigraRfLazyflowClassifierFactory(100)

        try:
            from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
            from sklearn.naive_bayes import GaussianNB
            from sklearn.tree import DecisionTreeClassifier
            from sklearn.neighbors import KNeighborsClassifier
            from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
            from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
            from sklearn.svm import SVC, NuSVC

            classifiers["Random Forest (scikit-learn)"] = SklearnLazyflowClassifierFactory(RandomForestClassifier, 100)
            classifiers["Gaussian Naive Bayes (scikit-learn)"] = SklearnLazyflowClassifierFactory(GaussianNB)
            classifiers["AdaBoost (scikit-learn)"] = SklearnLazyflowClassifierFactory(
                AdaBoostClassifier, n_estimators=100
            )
            classifiers["Single Decision Tree (scikit-learn)"] = SklearnLazyflowClassifierFactory(
                DecisionTreeClassifier, max_depth=5
            )
            classifiers["K-Neighbors (scikit-learn)"] = SklearnLazyflowClassifierFactory(KNeighborsClassifier)
            classifiers["LDA (scikit-learn)"] = SklearnLazyflowClassifierFactory(LDA)
            classifiers["QDA (scikit-learn)"] = SklearnLazyflowClassifierFactory(QDA)
            classifiers["SVM C-Support (scikit-learn)"] = SklearnLazyflowClassifierFactory(SVC, probability=True)
            classifiers["SVM Nu-Support (scikit-learn)"] = SklearnLazyflowClassifierFactory(NuSVC, probability=True)
        except ImportError as e:
            import warnings

            warnings.warn(f"Couldn't import sklearn. Scikit-learn classifiers not available. Error encountered at {e}")

        # Debug classifiers
        classifiers["Parallel Random Forest with Variable Importance (VIGRA)"] = (
            ParallelVigraRfLazyflowClassifierFactory(100, variable_importance_enabled=True)
        )
        classifiers["(debug) Single-threaded Random Forest (VIGRA)"] = VigraRfLazyflowClassifierFactory(100)
        classifiers["(debug) Pixelwise Random Forest (VIGRA)"] = VigraRfPixelwiseClassifierFactory(100)

        return classifiers

    def accept(self):
        # Configure the operator with the newly selected classifier factory
        selected_item = self._classifier_listwidget.selectedItems()[0]
        selected_factory = selected_item.data(Qt.UserRole)
        self._op.ClassifierFactory.setValue(selected_factory)

        # Close the dlg
        super(ClassifierSelectionDlg, self).accept()


class BookmarksWindow(QDialog):
    """
    A simple UI for showing bookmarks and navigating to them.

    FIXME: For now, this window is tied to a particular lane.
           If your project has more than one lane, then each one
           will have it's own bookmark window, which is kinda dumb.
    """

    def __init__(self, parent, topLevelOperatorView):
        super(BookmarksWindow, self).__init__(parent)
        self.setWindowTitle("Bookmarks")
        self.topLevelOperatorView = topLevelOperatorView
        self.bookmark_tree = QTreeWidget(self)
        self.bookmark_tree.setHeaderLabels(["Location", "Notes"])
        self.bookmark_tree.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.bookmark_tree.setColumnWidth(0, 200)
        self.bookmark_tree.setColumnWidth(1, 300)

        self.note_edit = QLineEdit(self)
        self.add_bookmark_button = QPushButton("Add Bookmark", self, clicked=self.add_bookmark)

        geometry = self.geometry()
        geometry.setSize(QSize(520, 520))
        self.setGeometry(geometry)

        layout = QVBoxLayout()
        layout.addWidget(self.bookmark_tree)
        layout.addWidget(self.note_edit)
        layout.addWidget(self.add_bookmark_button)
        self.setLayout(layout)

        self._load_bookmarks()

        self.bookmark_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmark_tree.customContextMenuRequested.connect(self.showContextMenu)

        self.bookmark_tree.itemDoubleClicked.connect(self._handle_doubleclick)

    def _handle_doubleclick(self, item, col):
        """
        Navigate to the bookmark
        """
        data = item.data(0, Qt.UserRole).toPyObject()
        if data is None:
            return

        (coord, notes) = data
        axes = self.topLevelOperatorView.InputImages.meta.getAxisKeys()
        axes = axes[:-1]  # drop channel
        axes = sorted(axes)
        assert len(axes) == len(coord)
        tagged_coord = dict(list(zip(axes, coord)))
        tagged_location = OrderedDict(list(zip("txyzc", (0, 0, 0, 0, 0))))
        tagged_location.update(tagged_coord)
        t = list(tagged_location.values())[0]
        coord3d = list(tagged_location.values())[1:4]

        self.parent().editor.posModel.time = t
        self.parent().editor.navCtrl.panSlicingViews(coord3d, [0, 1, 2])
        self.parent().editor.posModel.slicingPos = coord3d

    def showContextMenu(self, pos):
        item = self.bookmark_tree.itemAt(pos)
        data = item.data(0, Qt.UserRole).toPyObject()
        if data is None:
            return

        def delete_bookmark():
            (coord, notes) = data
            bookmarks = list(self.topLevelOperatorView.Bookmarks.value)
            i = bookmarks.index((coord, notes))
            bookmarks.pop(i)
            self.topLevelOperatorView.Bookmarks.setValue(bookmarks)
            self._load_bookmarks()

        menu = QMenu(parent=self)
        menu.addAction(QAction("Delete", menu, triggered=delete_bookmark))
        globalPos = self.bookmark_tree.viewport().mapToGlobal(pos)
        menu.exec_(globalPos)
        # selection = menu.exec_( globalPos )
        # if selection is removeLanesAction:
        #    self.removeLanesRequested.emit( self._selectedLanes )

    def add_bookmark(self):
        coord_txyzc = self.parent().editor.posModel.slicingPos5D
        tagged_coord_txyzc = dict(list(zip("txyzc", coord_txyzc)))
        axes = self.topLevelOperatorView.InputImages.meta.getAxisKeys()
        axes = axes[:-1]  # drop channel
        axes = sorted(axes)
        coord = tuple(tagged_coord_txyzc[c] for c in axes)

        notes = str(self.note_edit.text())
        bookmarks = list(self.topLevelOperatorView.Bookmarks.value)
        bookmarks.append((coord, notes))
        self.topLevelOperatorView.Bookmarks.setValue(bookmarks)

        self._load_bookmarks()

    def _load_bookmarks(self):
        self.bookmark_tree.clear()
        lane_index = self.topLevelOperatorView.current_view_index()
        lane_nickname = self.topLevelOperatorView.InputImages.meta.nickname or "Lane {}".format(lane_index)
        bookmarks = self.topLevelOperatorView.Bookmarks.value
        group_item = QTreeWidgetItem(self.bookmark_tree, [lane_nickname])

        for coord, notes in bookmarks:
            item = QTreeWidgetItem(group_item, [])
            item.setText(0, str(coord))
            item.setData(0, Qt.UserRole, (coord, notes))
            item.setText(1, notes)

        self.bookmark_tree.expandAll()


class PixelClassificationGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget(self):
        return self

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super(PixelClassificationGui, self).stopAndCleanUp()

    def viewerControlWidget(self):
        return self._viewerControlUi

    def menus(self):
        menus = super(PixelClassificationGui, self).menus()

        advanced_menu = QMenu("Advanced", parent=self)

        def handleClassifierAction():
            dlg = ClassifierSelectionDlg(self.topLevelOperatorView, parent=self)
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
            fileNames = ImageFileDialog(
                self, preferences_group="DataSelection", preferences_setting="recent image"
            ).getSelectedPaths()
            fileNames = list(map(str, fileNames))

            # For now, we require a single hdf5 file
            if len(fileNames) > 1:
                QMessageBox.critical(self, "Too many files", "Labels must be contained in a single hdf5 volume.")
                return
            if len(fileNames) == 0:
                # user cancelled
                return

            file_path = fileNames[0]
            internal_paths = DatasetInfo.getPossibleInternalPathsFor(file_path)
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
                print(line)

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

        menus += [advanced_menu]

        return menus

    ###########################################
    ###########################################

    def __init__(self, parentApplet, topLevelOperatorView: OpPixelClassification, labelingDrawerUiPath=None):
        self.parentApplet = parentApplet
        self.isInitialized = (
            False  # need this flag in pixelClassificationApplet where initialization is terminated with label selection
        )
        # Tell our base class which slots to monitor
        labelSlots = LabelingSlots(
            labelInput=topLevelOperatorView.LabelInputs,
            labelOutput=topLevelOperatorView.LabelImages,
            labelEraserValue=topLevelOperatorView.opLabelPipeline.opLabelArray.eraser,
            labelDelete=topLevelOperatorView.opLabelPipeline.DeleteLabel,
            labelNames=topLevelOperatorView.LabelNames,
            nonzeroLabelBlocks=topLevelOperatorView.NonzeroLabelBlocks,
        )

        self.__cleanup_fns = []

        # We provide our own UI file (which adds an extra control for interactive mode)
        if labelingDrawerUiPath is None:
            labelingDrawerUiPath = os.path.split(__file__)[0] + "/labelingDrawer.ui"

        # Base class init
        super(PixelClassificationGui, self).__init__(
            parentApplet, labelSlots, topLevelOperatorView, labelingDrawerUiPath, topLevelOperatorView.InputImages
        )

        self.topLevelOperatorView = topLevelOperatorView

        self._currentlySavingPredictions = False

        self.labelingDrawerUi.labelListView.support_merges = True

        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.setLiveUpdateEnabled)

        self.labelingDrawerUi.suggestFeaturesButton.clicked.connect(self.show_suggest_features_dialog)
        self.labelingDrawerUi.suggestFeaturesButton.setEnabled(False)

        # Always force at least two labels because it makes no sense to have less here
        self.forceAtLeastTwoLabels(True)

        self._initShortcuts()

        self._bookmarks_window = BookmarksWindow(self, self.topLevelOperatorView)

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
            try:
                self._renderMgr = RenderingManager(self.editor.view3d)
            except:
                self.render = False

        # listen to freezePrediction changes
        unsub_callback = self.topLevelOperatorView.FreezePredictions.notifyDirty(
            lambda *args: self.setLiveUpdateEnabled()
        )
        self.__cleanup_fns.append(unsub_callback)

        self.setLiveUpdateEnabled()

    def initSuggestFeaturesDialog(self):
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

        return SuggestFeaturesDialog(thisOpFeatureSelection, self, self.labelListData, self)

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
        thisOpFeatureSelection.SelectionMatrix.setValue(feature_matrix)

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

    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer and the raw layer
        layers = super(PixelClassificationGui, self).setupLayers()

        ActionInfo = ShortcutManager.ActionInfo

        if ilastik_config.getboolean("ilastik", "debug"):

            # Add the label projection layer.
            labelProjectionSlot = self.topLevelOperatorView.opLabelPipeline.opLabelArray.Projection2D
            if labelProjectionSlot.ready():
                projectionSrc = createDataSource(labelProjectionSlot)
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
            uncertaintySrc = createDataSource(uncertaintySlot)
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

        labels = self.labelListData

        # Add each of the segmentations
        for channel, segmentationSlot in enumerate(self.topLevelOperatorView.SegmentationChannels):
            if segmentationSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                segsrc = createDataSource(segmentationSlot)
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
                predictsrc = createDataSource(predictionSlot)
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

        if self.topLevelOperatorView.AutocontextInput.ready():
            layer = self.createStandardLayerFromSlot(self.topLevelOperatorView.AutocontextInput)
            layer.name = "Autocontext Input"
            layer.visible = False
            layers.append(layer)

        return layers

    def hasFeatures(self) -> bool:
        feature_images_slot = self.topLevelOperatorView.FeatureImages
        return feature_images_slot.ready() and feature_images_slot.meta.shape is not None

    def isLiveUpdateEnabled(self):
        return not self.topLevelOperatorView.FreezePredictions.value

    def setLiveUpdateEnabled(self, checked: Optional[bool] = None):
        checked = checked if checked is not None else self.isLiveUpdateEnabled()
        with silent_qobject(self.labelingDrawerUi.liveUpdateButton) as w:
            w.setChecked(checked)
        if checked:
            self._viewerControlUi.checkShowPredictions.setChecked(True)
            self.handleShowPredictionsClicked()

        num_label_classes = self._labelControlUi.labelListModel.rowCount()
        self.labelingDrawerUi.labelListView.allowDelete = not checked and num_label_classes > self.minLabelNumber
        self.labelingDrawerUi.AddLabelButton.setEnabled(not checked and num_label_classes < self.maxLabelNumber)
        self.topLevelOperatorView.FreezePredictions.setValue(not checked)
        self.labelingDrawerUi.suggestFeaturesButton.setEnabled(not checked)

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested()

    @Slot()
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

    @Slot()
    def handleShowSegmentationClicked(self):
        checked = self._viewerControlUi.checkShowSegmentation.isChecked()
        for layer in self.layerstack:
            if "Segmentation" in layer.name:
                layer.visible = checked

    @Slot()
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

    @Slot()
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
        slot.setValue(_listReplace(old, new))

    def _onLabelRemoved(self, parent, start, end):
        # Call the base class to update the operator.
        super(PixelClassificationGui, self)._onLabelRemoved(parent, start, end)

        # Keep colors in sync with names
        # (If we deleted a name, delete its corresponding colors, too.)
        op = self.topLevelOperatorView
        if len(op.PmapColors.value) > len(op.LabelNames.value):
            for slot in (op.LabelColors, op.PmapColors):
                value = slot.value
                value.pop(start)
                # Force dirty propagation even though the list id is unchanged.
                slot.setValue(value, check_changed=False)

    def _clearLabelListGui(self):
        """Remove rows until we have the right number"""
        while self._labelControlUi.labelListModel.rowCount() > 2:
            self._removeLastLabel()

    def getNextLabelName(self):
        return self._getNext(self.topLevelOperatorView.LabelNames, super(PixelClassificationGui, self).getNextLabelName)

    def getNextLabelColor(self):
        return self._getNext(
            self.topLevelOperatorView.LabelColors,
            super(PixelClassificationGui, self).getNextLabelColor,
            lambda x: QColor(*x),
        )

    def getNextPmapColor(self):
        return self._getNext(
            self.topLevelOperatorView.PmapColors,
            super(PixelClassificationGui, self).getNextPmapColor,
            lambda x: QColor(*x),
        )

    def onLabelNameChanged(self):
        self._onLabelChanged(
            super(PixelClassificationGui, self).onLabelNameChanged,
            lambda l: l.name,
            self.topLevelOperatorView.LabelNames,
        )

    def onLabelColorChanged(self):
        self._onLabelChanged(
            super(PixelClassificationGui, self).onLabelColorChanged,
            lambda l: (l.brushColor().red(), l.brushColor().green(), l.brushColor().blue()),
            self.topLevelOperatorView.LabelColors,
        )

    def onPmapColorChanged(self):
        self._onLabelChanged(
            super(PixelClassificationGui, self).onPmapColorChanged,
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

        assert self._renderMgr is not None
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
            color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            assert self._renderMgr is not None
            self._renderMgr.setColor(label, color)
