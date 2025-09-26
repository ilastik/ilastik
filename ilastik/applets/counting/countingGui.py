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
import importlib
import logging
import os

import numpy

from ilastik.applets.counting.countingGuiBoxesInterface import BoxController, BoxInterpreter, Tool
from ilastik.applets.counting.countingGuiDotsInterface import DotCrosshairController, DotInterpreter
from ilastik.applets.labeling.labelingGui import LabelingGui, LabelingSlots
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.utility import bind
from ilastik.utility.gui import roi2rect, threadRouted
from ilastik.widgets.boxListModel import BoxListModel
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.utility import traceLogged
from qtpy import uic
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QColor, QIcon
from qtpy.QtWidgets import QApplication, QFileDialog, QMessageBox
from volumina.api import ColortableLayer, LazyflowSinkSource, createDataSource
from volumina.navigationController import NavigationInterpreter
from volumina.utility import ShortcutManager
from volumina.colortables import matplotlib_to_qt4_colortable

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)


def _countingColorTable():
    """
    Create a colortable for the counting applet with gradual alpha increase
    for the first third, then two thirds red, max alpha.
    """
    n_total = 256
    n_gradual = 84
    colortable = matplotlib_to_qt4_colortable("jet", N=n_gradual, asLong=False)
    weights = numpy.tanh(numpy.linspace(0, 1.0, n_gradual))
    for w, c in zip(weights, colortable):
        c.setAlpha(int(w * 255))
    colortable = [c.rgba() for c in colortable]

    return [*colortable, *[colortable[-1]] * (n_total - n_gradual)]


countingColorTable = _countingColorTable()


def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new) :]
    else:
        return new


class CallToGui(object):
    def __init__(self, opslot, setfun):
        """
        Helper class which registers a simple callback between an operator and a gui
        element so that gui elements can be kept in sync across different images
        :param opslot:
        :param setfun:
        :param defaultval:

        """

        self.val = None
        self.opslot = opslot
        self.setfun = setfun
        self._exec()
        self.opslot.notifyDirty(bind(self._exec))

    def _exec(self):
        if self.opslot.ready():
            self.val = self.opslot.value

        if self.val != None:
            # FXIME: workaround for recently introduced bug when setting
            # sigma box as spindoublebox
            if type(self.val) == list:
                val = self.val[0]
            else:
                val = self.val
            self.setfun(val)


class CountingGui(LabelingGui):
    _FILE_DIALOG_FILTER = "CSV (*.csv)"

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget(self):
        return self

    def stopAndCleanUp(self):
        # Base class
        super(CountingGui, self).stopAndCleanUp()

    def viewerControlWidget(self):
        return self._viewerControlUi

    ###########################################
    ###########################################

    @traceLogged(traceLogger)
    def __init__(self, parentApplet, topLevelOperatorView):
        self.isInitialized = (
            False  # need this flag in countingApplet where initialization is terminated with label selection
        )
        self.parentApplet = parentApplet

        # Tell our base class which slots to monitor
        labelSlots = LabelingSlots(
            labelInput=topLevelOperatorView.LabelInputs,
            labelOutput=topLevelOperatorView.LabelImages,
            labelEraserValue=topLevelOperatorView.opLabelPipeline.opLabelArray.eraser,
            labelDelete=topLevelOperatorView.opLabelPipeline.opLabelArray.deleteLabel,
            labelNames=topLevelOperatorView.LabelNames,
        )

        labelSlots.nonzeroLabelBlocks = topLevelOperatorView.NonzeroLabelBlocks

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + "/countingDrawer.ui"

        # Base class init
        super(CountingGui, self).__init__(
            parentApplet, labelSlots, topLevelOperatorView, labelingDrawerUiPath, topLevelOperatorView.InputImages
        )

        self.op = topLevelOperatorView

        self.topLevelOperatorView = topLevelOperatorView
        self.shellRequestSignal = parentApplet.shellRequestSignal
        self.predictionSerializer = parentApplet.predictionSerializer

        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

        #        self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)
        #        self.labelingDrawerUi.savePredictionsButton.setIcon( QIcon(ilastikIcons.Save) )

        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.toggleInteractive)
        self.topLevelOperatorView.MaxLabelValue.notifyDirty(bind(self.handleLabelSelectionChange))

        self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)

        self.initCounting()
        # personal debugging code
        try:
            from sitecustomize import Shortcuts
        except Exception as e:
            self.labelingDrawerUi.DebugButton.setVisible(False)

        self._initShortcuts()

    def initCounting(self):

        # =======================================================================
        # Init Dotting interface
        # =======================================================================

        self.dotcrosshairController = DotCrosshairController(self.editor.brushingModel, self.editor.imageViews)
        self.editor.crosshairController = self.dotcrosshairController
        # self.dotController=DotController(self.editor.imageScenes[2],self.editor.brushingController)
        self.editor.brushingInterpreter = DotInterpreter(self.editor.navCtrl, self.editor.brushingController)
        self.dotInterpreter = self.editor.brushingInterpreter

        # =======================================================================
        # Init Label Control Ui Custom  setup
        # =======================================================================

        self._viewerControlUi.label.setVisible(False)
        self._viewerControlUi.checkShowPredictions.setVisible(False)
        self._viewerControlUi.checkShowSegmentation.setVisible(False)

        self._addNewLabel()
        self._addNewLabel()
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)

        # =======================================================================
        # Init labeling Drawer Ui Custom  setup
        # =======================================================================

        # labels for foreground and background
        self.labelingDrawerUi.labelListModel.makeRowPermanent(0)
        self.labelingDrawerUi.labelListModel.makeRowPermanent(1)
        self.labelingDrawerUi.labelListModel[0].name = "Foreground"
        self.labelingDrawerUi.labelListModel[1].name = "Background"
        self.labelingDrawerUi.labelListView.shrinkToMinimum()

        self.labelingDrawerUi.CountText.setReadOnly(True)

        # =======================================================================
        # Init Boxes Interface
        # =======================================================================

        # if not hasattr(self._labelControlUi, "boxListModel"):
        self.labelingDrawerUi.boxListModel = BoxListModel()
        self.labelingDrawerUi.boxListView.setModel(self.labelingDrawerUi.boxListModel)
        self.labelingDrawerUi.boxListModel.elementSelected.connect(self._onBoxSelected)
        # self.labelingDrawerUi.boxListModel.boxRemoved.connect(self._removeBox)

        self.labelingDrawerUi.DensityButton.clicked.connect(self.updateSum)

        self.density5d = OpReorderAxes(graph=self.op.graph, parent=self.op.parent)  #

        self.density5d.Input.connect(self.op.Density)
        self.boxController = BoxController(self.editor, self.density5d.Output, self.labelingDrawerUi.boxListModel)
        self.boxInterpreter = BoxInterpreter(self.editor.navInterpret, self.editor.posModel, self.centralWidget())
        self.boxInterpreter.boxDrawn.connect(self.boxController.addNewBox)

        self.navigationInterpreterDefault = self.editor.navInterpret

        self._setUIParameters()
        self._connectUIParameters()

        self._loadViewBoxes()

        self.boxController.fixedBoxesChanged.connect(self._handleBoxConstraints)
        self.boxController.viewBoxesChanged.connect(self._changeViewBoxes)

        self.op.LabelPreviewer.sigma.setValue(self.op.opTrain.Sigma.value)
        self.op.opTrain.fixClassifier.setValue(False)

        # TODO: check if defer makes sense here!
        self.op.Density.notifyDirty(self._normalizePrediction, defer=True)
        self.op.LabelImages.notifyDirty(self._normalizeLayers, defer=True)

        self._updateSVROptions()

    def _connectUIParameters(self):

        # =======================================================================
        # Gui to operator connections
        # =======================================================================

        # Debug interface only available to advanced users
        self.labelingDrawerUi.DebugButton.pressed.connect(self._debug)

        self.labelingDrawerUi.boxListView.resetEmptyMessage("no boxes defined yet")
        self.labelingDrawerUi.boxListView.importTriggered.connect(self._importBoxes)
        self.labelingDrawerUi.boxListView.exportTriggered.connect(self._exportBoxes)

        self.labelingDrawerUi.SVROptions.currentIndexChanged.connect(self._updateSVROptions)
        self.labelingDrawerUi.CBox.valueChanged.connect(self._updateC)

        self.labelingDrawerUi.SigmaBox.valueChanged.connect(self._updateSigma)
        self.labelingDrawerUi.EpsilonBox.valueChanged.connect(self._updateEpsilon)
        self.labelingDrawerUi.MaxDepthBox.valueChanged.connect(self._updateMaxDepth)
        self.labelingDrawerUi.NtreesBox.valueChanged.connect(self._updateNtrees)

        # =======================================================================
        # Operators to Gui connections
        # =======================================================================

        self._registerOperatorsToGuiCallbacks()

        # =======================================================================
        # Initialize Values
        # =======================================================================

        self._updateSigma()
        self._updateNtrees()
        self._updateMaxDepth()

    def _importBoxes(self) -> None:
        """Show file dialog and import boxes from the selected file."""
        filename, _filter = QFileDialog.getOpenFileName(
            self, "Import Boxes", self.get_cwd(), self._FILE_DIALOG_FILTER, self._FILE_DIALOG_FILTER
        )

        if not filename:
            return

        try:
            with open(filename) as f:
                self.boxController.csvRead(f)
        except Exception as e:
            msg = "Box import error"
            logger.exception(msg)
            QMessageBox.critical(self, msg.title(), str(e))

    def _exportBoxes(self) -> None:
        """Show file dialog and export boxes to the selected file."""
        filename, _filter = QFileDialog.getSaveFileName(
            self, "Export Boxes", self.get_cwd(), self._FILE_DIALOG_FILTER, self._FILE_DIALOG_FILTER
        )

        if not filename:
            return

        filename, ext = os.path.splitext(filename)
        filename += ext or ".csv"

        try:
            with open(filename, "w") as f:
                self.boxController.csvWrite(f)
        except Exception as e:
            msg = "Box export error"
            logger.exception(msg)
            QMessageBox.critical(self, msg.title(), str(e))
            os.remove(filename)

    def get_cwd(self) -> str:
        """Current working directory, or user's home directory if the real cwd is unavailable."""
        home = os.path.expanduser("~")

        if not self.op.WorkingDirectory.ready():
            return home

        value = self.op.WorkingDirectory.value
        if value is None:
            return home

        value = value.strip()
        if not value:
            return home

        return value

    def _registerOperatorsToGuiCallbacks(self):

        op = self.op.opTrain
        gui = self.labelingDrawerUi

        CallToGui(op.Ntrees, gui.NtreesBox.setValue)
        CallToGui(op.MaxDepth, gui.MaxDepthBox.setValue)
        CallToGui(op.C, gui.CBox.setValue)
        CallToGui(op.Sigma, gui.SigmaBox.setValue)
        CallToGui(op.Epsilon, gui.EpsilonBox.setValue)

        def _setoption(option):
            index = gui.SVROptions.findText(option)
            gui.SVROptions.setCurrentIndex(index)

        CallToGui(op.SelectedOption, _setoption)
        idx = self.op.current_view_index()

    def _setUIParameters(self):

        self.labelingDrawerUi.SigmaBox.setKeyboardTracking(False)
        self.labelingDrawerUi.CBox.setRange(0, 1000)
        self.labelingDrawerUi.CBox.setKeyboardTracking(False)
        self.labelingDrawerUi.EpsilonBox.setKeyboardTracking(False)
        self.labelingDrawerUi.EpsilonBox.setDecimals(6)
        self.labelingDrawerUi.NtreesBox.setKeyboardTracking(False)
        self.labelingDrawerUi.MaxDepthBox.setKeyboardTracking(False)

        for option in self.op.options:
            if "req" in list(option.keys()):
                try:
                    for req in option["req"]:
                        importlib.import_module(req)
                except Exception as e:
                    continue
            # values=[v for k,v in option.items() if k not in ["gui", "req"]]
            self.labelingDrawerUi.SVROptions.addItem(option["method"], (option,))

        cache = self.op.classifier_cache
        if hasattr(cache._value, "__iter__") and len(self.op.classifier_cache._value) > 0:
            # if self.op.classifier_cache._value!=None and len(self.op.classifier_cache._value) > 0:
            # use parameters from cached classifier
            params = cache._value[0].get_params()
            Sigma = params["Sigma"]
            Epsilon = params["epsilon"]
            C = params["C"]
            Ntrees = params["ntrees"]
            MaxDepth = params["maxdepth"]
            _ind = self.labelingDrawerUi.SVROptions.findText(params["method"])

            # set opTrain from parameters
            self.op.opTrain.initInputs(params)

        else:
            # read parameters from opTrain Operator
            Sigma = self.op.opTrain.Sigma.value
            Epsilon = self.op.opTrain.Epsilon.value
            C = self.op.opTrain.C.value
            Ntrees = self.op.opTrain.Ntrees.value
            MaxDepth = self.op.opTrain.MaxDepth.value
            _ind = self.labelingDrawerUi.SVROptions.findText(self.op.opTrain.SelectedOption.value)

        # FIXME: quick fix recently introduced bug
        if type(Sigma) == list:
            Sigma = Sigma[0]
        self.labelingDrawerUi.SigmaBox.setValue(Sigma)
        self.labelingDrawerUi.EpsilonBox.setValue(Epsilon)
        self.labelingDrawerUi.CBox.setValue(C)
        self.labelingDrawerUi.NtreesBox.setValue(Ntrees)
        self.labelingDrawerUi.MaxDepthBox.setValue(MaxDepth)
        if _ind == -1:
            self.labelingDrawerUi.SVROptions.setCurrentIndex(0)
            self._updateSVROptions()
        else:
            self.labelingDrawerUi.SVROptions.setCurrentIndex(_ind)

        self._hideParameters()

    def _updateMaxDepth(self):
        self.op.opTrain.MaxDepth.setValue(self.labelingDrawerUi.MaxDepthBox.value())

    def _updateNtrees(self):
        self.op.opTrain.Ntrees.setValue(self.labelingDrawerUi.NtreesBox.value())

    def _hideParameters(self):
        _ind = self.labelingDrawerUi.SVROptions.currentIndex()
        option = self.labelingDrawerUi.SVROptions.itemData(_ind)[0]
        if "svr" not in option["gui"]:
            self.labelingDrawerUi.gridLayout_2.setVisible(False)
        else:
            self.labelingDrawerUi.gridLayout_2.setVisible(True)

        if "rf" not in option["gui"]:
            self.labelingDrawerUi.rf_panel.setVisible(False)
        else:
            self.labelingDrawerUi.rf_panel.setVisible(True)

    # def _updateOverMult(self):
    #    self.op.opTrain.OverMult.setValue(self.labelingDrawerUi.OverBox.value())
    # def _updateUnderMult(self):
    #    self.op.opTrain.UnderMult.setValue(self.labelingDrawerUi.UnderBox.value())
    def _updateC(self):
        self.op.opTrain.C.setValue(self.labelingDrawerUi.CBox.value())

    def _updateSigma(self):
        # if self._changedSigma:

        sigma = self._labelControlUi.SigmaBox.value()

        self.editor.crosshairController.setSigma(sigma)
        # 2 * the maximal value of a gaussian filter, to allow some leeway for overlapping
        self.op.opTrain.Sigma.setValue(sigma)
        self.op.opUpperBound.Sigma.setValue(sigma)
        self.op.LabelPreviewer.sigma.setValue(sigma)

        #    self._changedSigma = False
        self._normalizeLayers()

    def _normalizeLayers(self, *args):
        upperBound = self.op.UpperBound.value
        self.upperBound = upperBound

        if hasattr(self, "labelPreviewLayer"):
            self.labelPreviewLayer.set_normalize(0, (0, upperBound))
        return

    def _normalizePrediction(self, *args):
        if hasattr(self, "predictionLayer") and hasattr(self, "upperBound"):
            self.predictionLayer.set_normalize(0, (0, self.upperBound))
        if hasattr(self, "uncertaintyLayer") and hasattr(self, "upperBound"):
            self.uncertaintyLayer.set_normalize(0, (0, self.upperBound))

    def _updateEpsilon(self):
        self.op.opTrain.Epsilon.setValue(self.labelingDrawerUi.EpsilonBox.value())

    def _updateSVROptions(self):
        index = self.labelingDrawerUi.SVROptions.currentIndex()
        option = self.labelingDrawerUi.SVROptions.itemData(index)[0]
        self.op.opTrain.SelectedOption.setValue(option["method"])

        self._hideFixable(option)

        self._hideParameters()

    def _hideFixable(self, option):
        if "boxes" in option and option["boxes"] == False:
            self.labelingDrawerUi.boxListView.allowFixIcon = False
            self.labelingDrawerUi.boxListView.allowFixValues = False
        elif "boxes" in option and option["boxes"] == True:
            self.labelingDrawerUi.boxListView.allowFixIcon = True

    def _handleBoxConstraints(self, constr):
        opTrain = self.op.opTrain
        id = self.op.current_view_index()
        vals = constr["values"]
        rois = constr["rois"]
        fixedClassifier = opTrain.fixClassifier.value
        assert len(vals) == len(rois)
        if opTrain.BoxConstraintRois.ready() and opTrain.BoxConstraintValues.ready():
            if opTrain.BoxConstraintValues[id].value != vals or opTrain.BoxConstraintRois[id].value != rois:
                opTrain.fixClassifier.setValue(True)
                opTrain.BoxConstraintRois[id].setValue(rois)
                # at this position so the change of a value can trigger a recomputation
                opTrain.fixClassifier.setValue(fixedClassifier)
                opTrain.BoxConstraintValues[id].setValue(vals)

        # boxes = self.boxController._currentBoxesList

    def _changeViewBoxes(self, boxes):
        id = self.op.current_view_index()
        self.op.boxViewer.rois[id].setValue(boxes["rois"])

    def _loadViewBoxes(self):
        op = self.op.opTrain
        fix = op.fixClassifier.value
        op.fixClassifier.setValue(True)

        idx = self.op.current_view_index()
        axes = self.density5d.Output.meta.getAxisKeys()
        boxCounter = 0

        if self.op.boxViewer.rois.ready() and len(self.op.boxViewer.rois[idx].value) > 0:
            # if fixed boxes are existent, make column visible
            # self.labelingDrawerUi.boxListView._table.setColumnHidden(self.boxController.boxListModel.ColumnID.Fix, False)
            for roi in self.op.boxViewer.rois[idx].value:
                if not isinstance(roi, list) or len(roi) != 2:
                    continue
                self.boxController.addNewBox(roi2rect(*roi, axes))
                # boxIndex = self.boxController.boxListModel.index(boxCounter, self.boxController.boxListModel.ColumnID.Fix)
                # iconIndex = self.boxController.boxListModel.index(boxCounter, self.boxController.boxListModel.ColumnID.FixIcon)
                # self.boxController.boxListModel.setData(boxIndex,val)
                boxCounter = boxCounter + 1

        if op.BoxConstraintRois.ready() and len(op.BoxConstraintRois[idx].value) > 0:
            # if fixed boxes are existent, make column visible
            self.labelingDrawerUi.boxListView._table.setColumnHidden(
                self.boxController.boxListModel.ColumnID.Fix, False
            )
            for constr in zip(op.BoxConstraintRois[idx].value, op.BoxConstraintValues[idx].value):
                roi, val = constr
                if not isinstance(roi, list) or len(roi) != 2:
                    continue
                self.boxController.addNewBox(roi2rect(*roi, axes))
                boxIndex = self.boxController.boxListModel.index(
                    boxCounter, self.boxController.boxListModel.ColumnID.Fix
                )
                iconIndex = self.boxController.boxListModel.index(
                    boxCounter, self.boxController.boxListModel.ColumnID.FixIcon
                )
                self.boxController.boxListModel.setData(boxIndex, val)
                boxCounter = boxCounter + 1

        op.fixClassifier.setValue(fix)

    def _debug(self):
        go.db

    @traceLogged(traceLogger)
    def initViewerControlUi(self):
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi(os.path.join(localDir, "viewerControls.ui"))

        # Connect checkboxes
        def nextCheckState(checkbox):
            checkbox.setChecked(not checkbox.isChecked())

        self._viewerControlUi.checkShowPredictions.clicked.connect(self.handleShowPredictionsClicked)
        self._viewerControlUi.checkShowSegmentation.clicked.connect(self.handleShowSegmentationClicked)

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        self._viewerControlUi.viewerControls.setupConnections(model)

        def _monkey_contextMenuEvent(s, event):
            from volumina.widgets.layercontextmenu import layercontextmenu

            idx = s.indexAt(event.pos())
            layer = s.model()[idx.row()]
            if layer.name == "Boxes":
                pass
                # FIXME: for the moment we do nothing here
            else:
                layercontextmenu(layer, s.mapToGlobal(event.pos()), s)

        import types

        self._viewerControlUi.viewerControls.layerWidget.contextMenuEvent = types.MethodType(
            _monkey_contextMenuEvent, self._viewerControlUi.viewerControls.layerWidget
        )

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
                "Toggle Segmentation",
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
                "Toggle Live Prediction Mode",
                "Toggle Live",
                self.labelingDrawerUi.liveUpdateButton.toggle,
                self.labelingDrawerUi.liveUpdateButton,
                self.labelingDrawerUi.liveUpdateButton,
            ),
        )

        shortcutGroupName = "Counting"

        mgr.register(
            "Del",
            ActionInfo(
                shortcutGroupName, "Delete a Box", "Delete a Box", self.boxController.deleteSelectedItems, self, None
            ),
        )

        try:
            from sitecustomize import Shortcuts

            mgr.register(
                "F5",
                ActionInfo(shortcutGroupName, "Activate Debug Mode", "Activate Debug Mode", self._debug, self, None),
            )
        except ImportError as e:
            pass

    @traceLogged(traceLogger)
    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer and the raw layer.
        layers = super(CountingGui, self).setupLayers()

        slots = {
            "Prediction": (self.op.Density, 0.5),
            "LabelPreview": (self.op.LabelPreview, 1.0),
            "Uncertainty": (self.op.UncertaintyEstimate, 1.0),
        }

        for name, (slot, opacity) in list(slots.items()):
            if slot.ready():
                layer = ColortableLayer(
                    createDataSource(slot), colorTable=countingColorTable, normalize=(0, self.upperBound)
                )
                layer.name = name
                layer.opacity = opacity
                layer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                layers.append(layer)

        # Set LabelPreview-layer to True

        boxlabelsrc = LazyflowSinkSource(self.op.BoxLabelImages, self.op.BoxLabelInputs)
        boxlabellayer = ColortableLayer(boxlabelsrc, colorTable=self._colorTable16, direct=False)
        boxlabellayer.name = "Boxes"
        boxlabellayer.opacity = 1.0
        boxlabellayer.boxListModel = self.labelingDrawerUi.boxListModel
        boxlabellayer.visibleChanged.connect(self.boxController.changeBoxesVisibility)
        boxlabellayer.opacityChanged.connect(self.boxController.changeBoxesOpacity)

        layers.append(boxlabellayer)
        self.boxlabelsrc = boxlabelsrc

        self.handleLabelSelectionChange()
        return layers

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        """
        If enable
        """
        logger.debug("toggling interactive mode to '%r'" % checked)

        if checked:
            if (
                not self.topLevelOperatorView.FeatureImages.ready()
                or self.topLevelOperatorView.FeatureImages.meta.shape is None
            ):
                self.labelingDrawerUi.liveUpdateButton.setChecked(False)
                self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))
                mexBox = QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        if self.interactiveModeActive != checked:
            self.interactiveModeActive = checked
            self.labelingDrawerUi.labelListView.allowDelete = not checked
            self.labelingDrawerUi.liveUpdateButton.setChecked(checked)
            if checked:
                self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Pause))
            else:
                self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))

        self.topLevelOperatorView.FreezePredictions.setValue(not checked)

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self._viewerControlUi.checkShowPredictions.setChecked(True)
            self.handleShowPredictionsClicked()

        # If we're changing modes, enable/disable our controls and other applets accordingly
        self.parentApplet.appletStateUpdateRequested()

    @traceLogged(traceLogger)
    def updateAllLayers(self, slot=None):
        super(CountingGui, self).updateAllLayers()
        for layer in self.layerstack:
            if layer.name == "LabelPreview":
                layer.visible = True
                self.labelPreviewLayer = layer
            if layer.name == "Prediction":
                self.predictionLayer = layer
            if layer.name == "Uncertainty":
                self.uncertaintyLayer = layer

    @Slot()
    @traceLogged(traceLogger)
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

    @Slot()
    @traceLogged(traceLogger)
    def handleShowSegmentationClicked(self):
        checked = self._viewerControlUi.checkShowSegmentation.isChecked()
        for layer in self.layerstack:
            if "Segmentation" in layer.name:
                layer.visible = checked

    @Slot()
    @traceLogged(traceLogger)
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
    @traceLogged(traceLogger)
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

    @Slot()
    @threadRouted
    @traceLogged(traceLogger)
    def handleLabelSelectionChange(self):
        enabled = False
        if self.topLevelOperatorView.MaxLabelValue.ready():
            value = self.topLevelOperatorView.MaxLabelValue.value
            shape = self.topLevelOperatorView.CachedFeatureImages.meta.shape
            enabled = enabled = value >= 2 and all(d > 0 for d in shape)
            # FIXME: also check that each label has scribbles?

        # self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self.labelingDrawerUi.liveUpdateButton.setEnabled(enabled)
        self._viewerControlUi.checkShowPredictions.setEnabled(enabled)
        self._viewerControlUi.checkShowSegmentation.setEnabled(enabled)

    #    @Slot()
    #    @traceLogged(traceLogger)
    #    def onSavePredictionsButtonClicked(self):
    #        """
    #        The user clicked "Train and Predict".
    #        Handle this event by asking the topLevelOperatorView for a prediction over the entire output region.
    #        """
    #        import warnings
    #        warnings.warn("FIXME: Remove this function and just use the data export applet.")
    #        # The button does double-duty as a cancel button while predictions are being stored
    #        if self._currentlySavingPredictions:
    #            self.predictionSerializer.cancel()
    #        else:
    #            # Compute new predictions as needed
    #            predictionsFrozen = self.topLevelOperatorView.FreezePredictions.value
    #            self.topLevelOperatorView.FreezePredictions.setValue(False)
    #            self._currentlySavingPredictions = True
    #
    #            originalButtonText = "Full Volume Predict and Save"
    #            #self.labelingDrawerUi.savePredictionsButton.setText("Cancel Full Predict")
    #
    #            @traceLogged(traceLogger)
    #            def saveThreadFunc():
    #                logger.info("Starting full volume save...")
    #                # Disable all other applets
    #                def disableAllInWidgetButName(widget, exceptName):
    #                    for child in widget.children():
    #                        if child.findChild( QPushButton, exceptName) is None:
    #                            child.setEnabled(False)
    #                        else:
    #                            disableAllInWidgetButName(child, exceptName)
    #
    #                # Disable everything in our drawer *except* the cancel button
    #                disableAllInWidgetButName(self.labelingDrawerUi, "savePredictionsButton")
    #
    #                # But allow the user to cancel the save
    #                self.labelingDrawerUi.savePredictionsButton.setEnabled(True)
    #
    #                # First, do a regular save.
    #                # During a regular save, predictions are not saved to the project file.
    #                # (It takes too much time if the user only needs the classifier.)
    #                self.shellRequestSignal(ShellRequest.RequestSave)
    #
    #                # Enable prediction storage and ask the shell to save the project again.
    #                # (This way the second save will occupy the whole progress bar.)
    #                self.predictionSerializer.predictionStorageEnabled = True
    #                self.shellRequestSignal(ShellRequest.RequestSave)
    #                self.predictionSerializer.predictionStorageEnabled = False
    #
    #                # Restore original states (must use events for UI calls)
    #                self.thunkEventHandler.post(self.labelingDrawerUi.savePredictionsButton.setText, originalButtonText)
    #                self.topLevelOperatorView.FreezePredictions.setValue(predictionsFrozen)
    #                self._currentlySavingPredictions = False
    #
    #                # Re-enable our controls
    #                def enableAll(widget):
    #                    for child in widget.children():
    #                        if isinstance( child, QWidget ):
    #                            child.setEnabled(True)
    #                            enableAll(child)
    #                enableAll(self.labelingDrawerUi)
    #
    #                # Re-enable all other applets
    #                logger.info("Finished full volume save.")
    #
    #            saveThread = threading.Thread(target=saveThreadFunc)
    #            saveThread.start()

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
        super(CountingGui, self)._onLabelRemoved(parent, start, end)
        op = self.topLevelOperatorView
        for slot in (op.LabelNames, op.LabelColors, op.PmapColors):
            value = slot.value
            value.pop(start)
            slot.setValue(value)

    def _clearLabelListGui(self):
        """Remove rows until we have the right number"""
        while self._labelControlUi.labelListModel.rowCount() > 2:
            self._removeLastLabel()

    def getNextLabelName(self):
        return self._getNext(self.topLevelOperatorView.LabelNames, super(CountingGui, self).getNextLabelName)

    def getNextLabelColor(self):
        return self._getNext(
            self.topLevelOperatorView.LabelColors, super(CountingGui, self).getNextLabelColor, lambda x: QColor(*x)
        )

    def getNextPmapColor(self):
        return self._getNext(
            self.topLevelOperatorView.PmapColors, super(CountingGui, self).getNextPmapColor, lambda x: QColor(*x)
        )

    def onLabelNameChanged(self):
        self._onLabelChanged(
            super(CountingGui, self).onLabelNameChanged, lambda l: l.name, self.topLevelOperatorView.LabelNames
        )

    def onLabelColorChanged(self):
        self._onLabelChanged(
            super(CountingGui, self).onLabelColorChanged,
            lambda l: (l.brushColor().red(), l.brushColor().green(), l.brushColor().blue()),
            self.topLevelOperatorView.LabelColors,
        )

    def onPmapColorChanged(self):
        self._onLabelChanged(
            super(CountingGui, self).onPmapColorChanged,
            lambda l: (l.pmapColor().red(), l.pmapColor().green(), l.pmapColor().blue()),
            self.topLevelOperatorView.PmapColors,
        )

    def _gui_setNavigation(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(True)

    def _gui_setBrushing(self):
        self._labelControlUi.paintToolButton.setChecked(True)

    def _gui_setBox(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(False)

        # self._labelControlUi.boxToolButton.setChecked(True)

    def _onBoxChanged(self, parentFun, mapf):

        parentFun()
        new = list(map(mapf, self.labelListData))

    def _changeInteractionMode(self, toolId):
        """
        Implement the GUI's response to the user selecting a new tool.
        """
        QApplication.restoreOverrideCursor()
        for v in self.editor.crosshairController._imageViews:
            v._crossHairCursor.enabled = True

        # Uncheck all the other buttons
        for tool, button in list(self.toolButtons.items()):
            if tool != toolId:
                button.setChecked(False)

        # If we have no editor, we can't do anything yet
        if self.editor is None:
            return

        # The volume editor expects one of two specific names
        modeNames = {
            Tool.Navigation: "navigation",
            Tool.Paint: "brushing",
            Tool.Erase: "brushing",
            Tool.Threshold: "thresholding",
            Tool.Box: "navigation",
        }

        if hasattr(self._labelControlUi, "AddLabelButton"):
            self._labelControlUi.AddLabelButton.setEnabled(
                self.maxLabelNumber > self._labelControlUi.labelListModel.rowCount()
            )
            self._labelControlUi.AddLabelButton.setText("Add Label")

        e = self._labelControlUi.labelListModel.rowCount() > 0
        self._gui_enableLabeling(e)

        # Update the applet bar caption
        if toolId == Tool.Navigation:
            # update GUI
            # self.editor.brushingModel.setBrushSize(0)
            self.editor.setNavigationInterpreter(NavigationInterpreter(self.editor.navCtrl))
            self._gui_setNavigation()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Paint:
            # If necessary, tell the brushing model to stop erasing
            if self.editor.brushingModel.erasing:
                self.editor.brushingModel.disableErasing()
            # Set the brushing size
            # this is done at the wrong time, drawnNumber has to be changed first before changing
            # interaction mode
            if self.editor.brushingModel.drawnNumber == 1:
                brushSize = 1
                self.editor.brushingModel.setBrushSize(brushSize)

            # update GUI
            self._gui_setBrushing()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Erase:

            # If necessary, tell the brushing model to start erasing
            if not self.editor.brushingModel.erasing:
                self.editor.brushingModel.setErasing()
            # Set the brushing size
            eraserSize = self.brushSizes[self.eraserSizeIndex]
            self.editor.brushingModel.setBrushSize(eraserSize)
            # update GUI
            self._gui_setErasing()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Threshold:
            # If necessary, tell the brushing model to stop erasing
            if self.editor.brushingModel.erasing:
                self.editor.brushingModel.disableErasing()
            # display a cursor that is static while moving arrow
            self.editor.brushingModel.setBrushSize(1)
            self._gui_setThresholding()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Box:

            self.setCursor(Qt.CrossCursor)
            self._labelControlUi.labelListModel.clearSelectionModel()
            for v in self.editor.crosshairController._imageViews:
                v._crossHairCursor.enabled = False

            # self.setOverrideCursor(Qt.CrossCursor)
            # QApplication.setOverrideCursor(Qt.CrossCursor)
            self.editor.brushingModel.setBrushSize(0)
            self.editor.setNavigationInterpreter(self.boxInterpreter)
            self._gui_setBox()

        self.editor.setInteractionMode(modeNames[toolId])
        self._toolId = toolId

    def _initLabelUic(self, drawerUiPath):
        super(CountingGui, self)._initLabelUic(drawerUiPath)
        # self._labelControlUi.boxToolButton.setCheckable(True)
        # self._labelControlUi.boxToolButton.clicked.connect( lambda checked: self._handleToolButtonClicked(checked,
        #                                                                                                  Tool.Box) )
        # self.toolButtons[Tool.Box] = self._labelControlUi.boxToolButton
        if hasattr(self._labelControlUi, "AddBoxButton"):

            self._labelControlUi.AddBoxButton.setIcon(QIcon(ilastikIcons.AddSel))
            self._labelControlUi.AddBoxButton.clicked.connect(bind(self.onAddNewBoxButtonClicked))

    def onAddNewBoxButtonClicked(self):

        self._changeInteractionMode(Tool.Box)
        self.labelingDrawerUi.boxListView.resetEmptyMessage("Draw the box on the image")

    def _onBoxSelected(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.boxListModel[row]))

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Box)

        self.boxController.selectBoxItem(row)

    def _onLabelSelected(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.labelListModel[row]))

        self.toolButtons[Tool.Paint].setEnabled(True)
        # elf.toolButtons[Tool.Box].setEnabled(False)
        self.toolButtons[Tool.Paint].click()

        # +1 because first is transparent
        # FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row + 1)
        brushColor = self._labelControlUi.labelListModel[row].brushColor()
        self.editor.brushingModel.setBrushColor(brushColor)

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Paint)

        if row == 0:  # foreground
            self._cachedBrushSizeIndex = self._labelControlUi.brushSizeComboBox.currentIndex()
            self._labelControlUi.SigmaBox.setEnabled(True)
            self._labelControlUi.brushSizeComboBox.setEnabled(False)
            self._labelControlUi.brushSizeComboBox.setCurrentIndex(0)
        else:
            if not hasattr(self, "_cachedBrushSizeIndex"):
                self._cachedBrushSizeIndex = 0

            self._labelControlUi.SigmaBox.setEnabled(False)
            self._labelControlUi.brushSizeComboBox.setCurrentIndex(self._cachedBrushSizeIndex)

    def updateSum(self, *args, **kw):
        state = self.labelingDrawerUi.liveUpdateButton.isChecked()
        self.labelingDrawerUi.liveUpdateButton.setChecked(True)
        self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Pause))
        density = self.op.OutputSum[...].wait()
        strdensity = "{0:.2f}".format(density[0])
        self._labelControlUi.CountText.setText(strdensity)
        self.labelingDrawerUi.liveUpdateButton.setChecked(state)
        if state:
            self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Pause))
        else:
            self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))
