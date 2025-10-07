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
from qtpy import uic
from qtpy.QtCore import Slot, Qt
from qtpy.QtGui import QColor, QIcon
from qtpy.QtWidgets import (
    QAction,
    QDialog,
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QUndoCommand,
)

from ilastik.applets.objectClassification.opObjectClassification import InvalidObjectIndex
from ilastik.applets.objectExtraction.opObjectExtraction import default_features_key

import os
import copy
import vigra

import numpy
import numpy.typing as npt
import weakref
from functools import partial

from ilastik.config import cfg as ilastik_config
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.plugins.manager import pluginManager

from lazyflow.request import Request, RequestPool

import logging

from lazyflow.slot import InputSlot

logger = logging.getLogger(__name__)

from ilastik.applets.labeling.labelingGui import LabelingGui, LabelingSlots
from ilastik.shell.gui.iconMgr import ilastikIcons

import volumina.colortables as colortables
from volumina.api import createDataSource, ColortableLayer, AlphaModulatedLayer, LazyflowSinkSource

from volumina.interpreter import ClickInterpreter
from volumina.utility import ShortcutManager


def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new) :]
    else:
        return new


from ilastik.applets.objectExtraction.objectExtractionGui import FeatureSelectionDialog


class FeatureSubSelectionDialog(FeatureSelectionDialog):
    def __init__(self, featureDict, selectedFeatures=None, parent=None, ndim=3):
        super(FeatureSubSelectionDialog, self).__init__(featureDict, selectedFeatures, parent, ndim)
        self.setObjectName("FeatureSubSelectionDialog")
        self.ui.spinBox_X.setEnabled(False)
        self.ui.spinBox_Y.setEnabled(False)
        self.ui.spinBox_Z.setEnabled(False)
        self.ui.spinBox_X.setVisible(False)
        self.ui.spinBox_Y.setVisible(False)
        self.ui.spinBox_Z.setVisible(False)
        self.ui.marginLabel.setVisible(False)
        self.ui.label.setVisible(False)
        self.ui.label_2.setVisible(False)
        self.ui.label_z.setVisible(False)


class LabelObjectCommand(QUndoCommand):
    """Redo/Undo for object labelings

    Note: the undo is not 100% true: In object classification the labeling dictionary
    is somewhat sparse - it will only contain entries up to the labeled object with
    the highest object id. The undo here will not revert the potential increase
    in dictionary size.
    Clearing a label in object classification will also not touch the length of
    this label array, so that's in a way consistent.
    """

    def __init__(
        self,
        parent=None,
        *,
        slot: InputSlot,
        labelsdict: dict[int, npt.NDArray],
        old_value: int,
        new_value: int,
        dirty_key,
    ):
        super().__init__(parent)
        self.__labels = labelsdict
        self.__old_value = old_value
        self.__new_value = new_value
        self.__dirty_key = dirty_key
        self.__slot = slot

    def _update_label(self, value):
        time_index, object_index = self.__dirty_key
        self.__labels[time_index][object_index] = value
        self.__slot.setValue(self.__labels)
        self.__slot.setDirty(self.__dirty_key)

    def redo(self):
        self._update_label(self.__new_value)

    def undo(self):
        self._update_label(self.__old_value)


class ObjectClassificationGui(LabelingGui):
    """A subclass of LabelingGui for labeling objects.

    Handles labeling objects, viewing the predicted results, and
    displaying warnings from the top level operator. Also provides a
    dialog for choosing subsets of the precalculated features provided
    by the object extraction applet.

    """

    def centralWidget(self):
        return self

    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super(ObjectClassificationGui, self).stopAndCleanUp()

    PREDICTION_LAYER_NAME = "Prediction"

    # FIXME
    # temporary place for this operator, move somewhere else later
    _knime_exporter = None

    def __init__(self, parentApplet, op):
        self.parentApplet = parentApplet
        self.isInitialized = False  # Need this flag in objectClassificationApplet where initialization is terminated with label selection
        self.__cleanup_fns = []
        # Tell our base class which slots to monitor
        labelSlots = LabelingSlots(
            labelInput=op.LabelInputs,
            labelOutput=op.LabelImages,
            labelEraserValue=op.Eraser,
            labelDelete=op.DeleteLabel,
            labelNames=op.LabelNames,
        )

        # We provide our own UI file (which adds an extra control for
        # interactive mode) This UI file is copied from
        # pixelClassification pipeline
        #
        labelingDrawerUiPath = os.path.split(__file__)[0] + "/labelingDrawer.ui"

        # button handlers
        self._interactiveMode = False
        self._showPredictions = False
        self._labelMode = True

        self.op = op
        self.applet = parentApplet

        # Base class init
        super(ObjectClassificationGui, self).__init__(
            parentApplet, labelSlots, op, labelingDrawerUiPath, op.RawImages, crosshair=False
        )

        self.interactiveMode = False  # This calls the setter function: interactiveMode(self, val)

        self.threadRouter = ThreadRouter(self)
        op.Warnings.notifyDirty(self.handleWarnings)
        self.__cleanup_fns.append(partial(op.Warnings.unregisterDirty, self.handleWarnings))

        self._retained_weakrefs = []

        # unused
        self.labelingDrawerUi.savePredictionsButton.setEnabled(False)
        self.labelingDrawerUi.savePredictionsButton.setVisible(False)

        self.labelingDrawerUi.brushSizeComboBox.setEnabled(False)
        self.labelingDrawerUi.brushSizeComboBox.setVisible(False)

        self.labelingDrawerUi.brushSizeCaption.setVisible(False)

        self._colorTable_forpmaps = list(colortables.default16_new)

        self.labelingDrawerUi.subsetFeaturesButton.clicked.connect(self.handleSubsetFeaturesClicked)
        self.labelingDrawerUi.labelAssistButton.clicked.connect(self.handleLabelAssistClicked)

        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect(self.handleInteractiveModeClicked)

        # Always force at least two labels because it makes no sense to have less here
        self.forceAtLeastTwoLabels(True)

        # select all the features in the beginning
        cfn = None
        already_selected = None
        if self.op.ComputedFeatureNames.ready():
            cfn = self.op.ComputedFeatureNames[:].wait()

        if self.op.SelectedFeatures.ready():
            already_selected = self.op.SelectedFeatures[:].wait()

        if already_selected is None or len(already_selected) == 0:
            if cfn is not None:
                already_selected = cfn

        self.op.SelectedFeatures.setValue(already_selected)

        nfeatures = 0

        if already_selected is not None:
            for plugin_features in already_selected.values():
                nfeatures += len(plugin_features)
        self.labelingDrawerUi.featuresSubset.setText(
            "{} features selected,\nsome may have multiple channels".format(nfeatures)
        )

        # enable/disable buttons logic
        self.op.ObjectFeatures.notifyDirty(bind(self.checkEnableButtons))
        self.__cleanup_fns.append(partial(op.ObjectFeatures.unregisterDirty, bind(self.checkEnableButtons)))

        self.op.NumLabels.notifyReady(bind(self.checkEnableButtons))
        self.__cleanup_fns.append(partial(op.NumLabels.unregisterReady, bind(self.checkEnableButtons)))

        self.op.NumLabels.notifyDirty(bind(self.checkEnableButtons))
        self.__cleanup_fns.append(partial(op.NumLabels.unregisterDirty, bind(self.checkEnableButtons)))

        self.op.SelectedFeatures.notifyDirty(bind(self.checkEnableButtons))
        self.__cleanup_fns.append(partial(op.SelectedFeatures.unregisterDirty, bind(self.checkEnableButtons)))

        if not self.op.AllowAddLabel([]).wait()[0]:
            self.labelingDrawerUi.AddLabelButton.hide()
            self.labelingDrawerUi.AddLabelButton.clicked.disconnect()

        self.badObjectBox = None

        self.checkEnableButtons()

        self._labelAssistDialog = None

        self._undoStack = self.editor._undoStack
        fn = self.op.SegmentationImages.notifyDirty(lambda *_, **__: self._undoStack.clear())
        self.__cleanup_fns.append(fn)

    def secondaryControlsWidget(self):
        return None

    def menus(self):
        m = QMenu("&Export", self.volumeEditorWidget)
        # m.addAction("Export Object Information").triggered.connect(self.show_export_dialog)
        if ilastik_config.getboolean("ilastik", "debug"):
            m.addAction("Export All Label Info").triggered.connect(self.exportLabelInfo)
            m.addAction("Import New Label Info").triggered.connect(self.importLabelInfo)
        return [m] if len(m.actions()) > 0 else []

    def exportLabelInfo(self):
        file_path, _filter = QFileDialog.getSaveFileName(
            parent=self, caption="Export Label Info as JSON", filter="*.json"
        )
        if file_path:
            topLevelOp = self.topLevelOperatorView.viewed_operator()
            topLevelOp.exportLabelInfo(file_path)

    def importLabelInfo(self):
        file_path, _filter = QFileDialog.getOpenFileName(
            parent=self, caption="Export Label Info as JSON", filter="*.json"
        )
        if file_path:
            topLevelOp = self.topLevelOperatorView.viewed_operator()
            topLevelOp.importLabelInfo(file_path)

    @property
    def labelMode(self):
        return self._labelMode

    @labelMode.setter
    def labelMode(self, val):
        self.labelingDrawerUi.labelListView.allowDelete = val and self.op.AllowDeleteLabels([]).wait()[0]
        self.labelingDrawerUi.AddLabelButton.setEnabled(val)
        self._labelMode = val

    @property
    def interactiveMode(self):
        return self._interactiveMode

    @interactiveMode.setter
    def interactiveMode(self, val):
        logger.debug("setting interactive mode to '%r'" % val)
        self._interactiveMode = val
        self.labelingDrawerUi.liveUpdateButton.setChecked(val)
        if val:
            self.showPredictions = True
            self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Pause))
        else:
            self.labelingDrawerUi.liveUpdateButton.setIcon(QIcon(ilastikIcons.Play))

        self.labelMode = not val
        self.op.FreezePredictions.setValue(not val)
        self.parentApplet.appletStateUpdateRequested()

    @Slot()
    def handleInteractiveModeClicked(self):
        self.interactiveMode = self.labelingDrawerUi.liveUpdateButton.isChecked()

    @property
    def showPredictions(self):
        return self._showPredictions

    @showPredictions.setter
    def showPredictions(self, val):
        self._showPredictions = val
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = val

        if self.labelMode and not val:
            self.labelMode = False
            # And hide all segmentation layers
            for layer in self.layerstack:
                if "Segmentation" in layer.name:
                    layer.visible = False

    @Slot()
    def handleShowPredictionsClicked(self):
        self.showPredictions = self.labelingDrawerUi.checkShowPredictions.isChecked()

    @Slot()
    def handleSubsetFeaturesClicked(self):
        mainOperator = self.topLevelOperatorView
        computedFeatures = copy.deepcopy(mainOperator.ComputedFeatureNames([]).wait())
        # do NOT show default features, the user did not want them for classification
        # the key for the fake plugin of default features is taken from the top of opObjectExtraction file
        if mainOperator.SelectedFeatures.ready():
            selectedFeatures = copy.deepcopy(mainOperator.SelectedFeatures([]).wait())
        else:
            selectedFeatures = computedFeatures

        plugins = pluginManager.getPluginsOfCategory("ObjectFeatures")
        taggedShape = mainOperator.RawImages.meta.getTaggedShape()
        fakeimgshp = [taggedShape["x"], taggedShape["y"]]
        fakelabelsshp = [taggedShape["x"], taggedShape["y"]]

        if "z" in taggedShape and taggedShape["z"] > 1:
            fakeimgshp.append(taggedShape["z"])
            fakelabelsshp.append(taggedShape["z"])
            ndim = 3
        else:
            ndim = 2
        if "c" in taggedShape and taggedShape["c"] > 1:
            fakeimgshp.append(taggedShape["c"])

        fakeimg = numpy.empty(fakeimgshp, dtype=numpy.float32)
        fakelabels = numpy.empty(fakelabelsshp, dtype=numpy.uint32)

        if ndim == 3:
            fakelabels = vigra.taggedView(fakelabels, "xyz")
            if len(fakeimgshp) == 4:
                fakeimg = vigra.taggedView(fakeimg, "xyzc")
            else:
                fakeimg = vigra.taggedView(fakeimg, "xyz")
        if ndim == 2:
            fakelabels = vigra.taggedView(fakelabels, "xy")
            if len(fakeimgshp) == 3:
                fakeimg = vigra.taggedView(fakeimg, "xyc")
            else:
                fakeimg = vigra.taggedView(fakeimg, "xy")

        for pluginInfo in plugins:
            availableFeatures = pluginInfo.plugin_object.availableFeatures(fakeimg, fakelabels)
            if len(availableFeatures) > 0:
                if pluginInfo.name in list(self.applet._selectedFeatures.keys()):
                    assert pluginInfo.name in list(
                        computedFeatures.keys()
                    ), "Object Classification: {} not found in available (computed) object features".format(
                        pluginInfo.name
                    )

                if not pluginInfo.name in selectedFeatures and pluginInfo.name in self.applet._selectedFeatures:
                    selectedFeatures[pluginInfo.name] = dict()

                    for feature in list(self.applet._selectedFeatures[pluginInfo.name].keys()):
                        if feature in list(availableFeatures.keys()):
                            selectedFeatures[pluginInfo.name][feature] = availableFeatures[feature]

        dlg = FeatureSubSelectionDialog(computedFeatures, selectedFeatures=selectedFeatures, ndim=ndim)
        dlg.exec_()
        if dlg.result() == QDialog.Accepted:
            if len(dlg.selectedFeatures) == 0:
                self.interactiveMode = False

            mainOperator.SelectedFeatures.setValue(dlg.selectedFeatures)
            nfeatures = 0
            for plugin_features in dlg.selectedFeatures.values():
                nfeatures += len(plugin_features)
            self.labelingDrawerUi.featuresSubset.setText(
                "{} features selected,\nsome may have multiple channels".format(nfeatures)
            )
        mainOperator.ComputedFeatureNames.setDirty(())

    @Slot()
    def handleLabelAssistClicked(self):
        if self._labelAssistDialog is None:
            self._labelAssistDialog = LabelAssistDialog(self, self.topLevelOperatorView)
        self._labelAssistDialog.show()

    @Slot()
    def checkEnableButtons(self):
        feats_enabled = True
        predict_enabled = True
        labels_enabled = True

        if self.op.ComputedFeatureNames.ready():
            featnames = self.op.ComputedFeatureNames([]).wait()
            if len(featnames) == 0:
                feats_enabled = False
        else:
            feats_enabled = False

        if feats_enabled:
            if self.op.SelectedFeatures.ready():
                featnames = self.op.SelectedFeatures([]).wait()
                if len(featnames) == 0:
                    predict_enabled = False
            else:
                predict_enabled = False

            if self.op.NumLabels.ready():
                if self.op.NumLabels.value < 2:
                    predict_enabled = False
            else:
                predict_enabled = False
        else:
            predict_enabled = False

        if not predict_enabled:
            self.interactiveMode = False
            self.showPredictions = False

        self.labelingDrawerUi.subsetFeaturesButton.setEnabled(feats_enabled)
        self.labelingDrawerUi.AddLabelButton.setEnabled(labels_enabled)
        self.labelingDrawerUi.liveUpdateButton.setEnabled(predict_enabled)
        self.labelingDrawerUi.labelListView.allowDelete = True and self.op.AllowDeleteLabels([]).wait()[0]
        self.allowDeleteLastLabelOnly(False or self.op.AllowDeleteLastLabelOnly([]).wait()[0])

        self.op._predict_enabled = predict_enabled
        self.applet.appletStateUpdateRequested()

    def initAppletDrawerUi(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]

        # We don't pass self here because we keep the drawer ui in a
        # separate object.
        self.drawer = uic.loadUi(localDir + "/drawer.ui")

    ### Function dealing with label name and color consistency
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

    def _getNextSuggestedLabelName(self):
        row_idx = self._labelControlUi.labelListModel.rowCount()
        return self.topLevelOperatorView.SuggestedLabelNames([]).wait()[row_idx]

    def getNextLabelName(self):
        try:
            return self._getNext(self.topLevelOperatorView.LabelNames, self._getNextSuggestedLabelName)
        except IndexError:
            return self._getNext(self.topLevelOperatorView.LabelNames, super().getNextLabelName)

    def getNextLabelColor(self):
        return self._getNext(
            self.topLevelOperatorView.LabelColors,
            super(ObjectClassificationGui, self).getNextLabelColor,
            lambda x: QColor(*x),
        )

    def getNextPmapColor(self):
        return self._getNext(
            self.topLevelOperatorView.PmapColors,
            super(ObjectClassificationGui, self).getNextPmapColor,
            lambda x: QColor(*x),
        )

    def onLabelNameChanged(self):
        self._onLabelChanged(
            super(ObjectClassificationGui, self).onLabelNameChanged,
            lambda l: l.name,
            self.topLevelOperatorView.LabelNames,
        )

    def onLabelColorChanged(self):
        self._onLabelChanged(
            super(ObjectClassificationGui, self).onLabelColorChanged,
            lambda l: (l.brushColor().red(), l.brushColor().green(), l.brushColor().blue()),
            self.topLevelOperatorView.LabelColors,
        )

    def onPmapColorChanged(self):
        self._onLabelChanged(
            super(ObjectClassificationGui, self).onPmapColorChanged,
            lambda l: (l.pmapColor().red(), l.pmapColor().green(), l.pmapColor().blue()),
            self.topLevelOperatorView.PmapColors,
        )

    def _onLabelRemoved(self, parent, start, end):
        # Don't respond unless this actually came from the GUI
        if self._programmaticallyRemovingLabels:
            return

        # Base class
        super(ObjectClassificationGui, self)._onLabelRemoved(parent, start, end)
        """
        # update the pmap colors. copied from labelingGui._onLabelRemoved
        # Remove the deleted label's color from the color table so that renumbered labels keep their colors.
        oldcount = self._labelControlUi.labelListModel.rowCount() + 1
        oldColor = self._colorTable_forpmaps.pop(start+1)
        # Recycle the deleted color back into the table (for the next label to be added)
        self._colorTable_forpmaps.insert(oldcount, oldColor)

        # Find the prediction layer and update its colortable
        layer_index = self.layerstack.findMatchingIndex(lambda x: x.name == self.PREDICTION_LAYER_NAME)
        predictLayer = self.layerstack[layer_index]
        predictLayer.colorTable = self._colorTable_forpmaps
        """
        op = self.topLevelOperatorView
        op.removeLabel(start)
        # Keep colors in sync with names
        # (If we deleted a name, delete its corresponding colors, too.)
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

    def createLabelLayer(self, direct=False):
        """Return a colortable layer that displays the label slot
        data, along with its associated label source.

        direct: whether this layer is drawn synchronously by volumina

        """
        labelInput = self._labelingSlots.labelInput
        labelOutput = self._labelingSlots.labelOutput

        if not labelOutput.ready():
            return (None, None)
        else:

            labelsrc = LazyflowSinkSource(labelOutput, labelInput)
            labellayer = ColortableLayer(labelsrc, colorTable=self._colorTable16, direct=direct)

            labellayer.segmentationImageSlot = self.op.SegmentationImagesOut
            labellayer.name = "Labels"
            labellayer.ref_object = None
            labellayer.zeroIsTransparent = False
            labellayer.colortableIsRandom = True

            clickInt = ClickInterpreter(self.editor, labellayer, self.onClick, right=False, double=False)
            self.editor.brushingInterpreter = clickInt

            return labellayer, labelsrc

    def setupLayers(self):
        # Base class provides the label layer and the raw layer
        layers = super(ObjectClassificationGui, self).setupLayers()

        atlas_slot = self.op.Atlas
        segmentedSlot = self.op.SegmentationImages
        # This is just for colors
        labels = self.labelListData

        for channel, probSlot in enumerate(self.op.PredictionProbabilityChannels):
            if probSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                probsrc = createDataSource(probSlot)
                probLayer = AlphaModulatedLayer(probsrc, tintColor=ref_label.pmapColor(), normalize=(0.0, 1.0))
                probLayer.opacity = 0.25
                # probLayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()
                # False, because it's much faster to draw predictions without these layers below
                probLayer.visible = False
                probLayer.setToolTip("Probability that the object belongs to class {}".format(channel + 1))

                def setLayerColor(c, predictLayer_=probLayer, ch=channel, initializing=False):
                    if not initializing and predictLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    predictLayer_.tintColor = c

                def setLayerName(n, predictLayer_=probLayer, initializing=False):
                    if not initializing and predictLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    newName = "Prediction for %s" % n
                    predictLayer_.name = newName

                setLayerName(ref_label.name, initializing=True)
                ref_label.pmapColorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setLayerName)
                layers.append(probLayer)

        predictionSlot = self.op.PredictionImages
        if predictionSlot.ready():
            predictsrc = createDataSource(predictionSlot)
            self._colorTable_forpmaps[0] = 0
            predictLayer = ColortableLayer(predictsrc, colorTable=self._colorTable_forpmaps)

            predictLayer.name = self.PREDICTION_LAYER_NAME
            predictLayer.ref_object = None
            predictLayer.opacity = 0.5
            predictLayer.setToolTip("Classification results, assigning a label to each object")

            # This weakref stuff is a little more fancy than strictly necessary.
            # The idea is to use the weakref's callback to determine when this layer instance is destroyed by the garbage collector,
            #  and then we disconnect the signal that updates that layer.
            weak_predictLayer = weakref.ref(predictLayer)
            colortable_changed_callback = bind(self._setPredictionColorTable, weak_predictLayer)
            self._labelControlUi.labelListModel.dataChanged.connect(colortable_changed_callback)
            weak_predictLayer2 = weakref.ref(
                predictLayer, partial(self._disconnect_dataChange_callback, colortable_changed_callback)
            )
            # We have to make sure the weakref isn't destroyed because it is responsible for calling the callback.
            # Therefore, we retain it by adding it to a list.
            self._retained_weakrefs.append(weak_predictLayer2)

            # Ensure we're up-to-date (in case this is the first time the prediction layer is being added.
            for row in range(self._labelControlUi.labelListModel.rowCount()):
                self._setPredictionColorTableForRow(predictLayer, row)

            # put right after Labels, so that it is visible after hitting "live
            # predict".
            layers.insert(1, predictLayer)

        badObjectsSlot = self.op.BadObjectImages
        if badObjectsSlot.ready():
            ct_black = [0, QColor(Qt.black).rgba()]
            badSrc = createDataSource(badObjectsSlot)
            badLayer = ColortableLayer(badSrc, colorTable=ct_black)
            badLayer.name = "Ambiguous objects"
            badLayer.setToolTip("Objects with infinite or invalid values in features")
            badLayer.visible = False
            layers.append(badLayer)

        if segmentedSlot.ready():
            ct = colortables.create_default_16bit()
            objectssrc = createDataSource(segmentedSlot)
            ct[0] = QColor(0, 0, 0, 0).rgba()  # make 0 transparent
            objLayer = ColortableLayer(objectssrc, ct)
            objLayer.name = "Object Identities"
            objLayer.opacity = 0.5
            objLayer.visible = False
            objLayer.setToolTip("Segmented objects, shown in different colors")
            objLayer.colortableIsRandom = True
            layers.append(objLayer)

        uncertaintySlot = self.op.UncertaintyEstimateImage
        if uncertaintySlot.ready():
            uncertaintySrc = createDataSource(uncertaintySlot)
            uncertaintyLayer = AlphaModulatedLayer(uncertaintySrc, tintColor=QColor(Qt.cyan), normalize=(0.0, 1.0))
            uncertaintyLayer.name = "Uncertainty"
            uncertaintyLayer.visible = False
            uncertaintyLayer.opacity = 1.0
            ActionInfo = ShortcutManager.ActionInfo
            uncertaintyLayer.shortcutRegistration = (
                "u",
                ActionInfo(
                    "Uncertainty Layers",
                    "Uncertainty",
                    "Show/Hide Uncertainty",
                    uncertaintyLayer.toggleVisible,
                    self.viewerControlWidget(),
                    uncertaintyLayer,
                ),
            )
            layers.append(uncertaintyLayer)

        if segmentedSlot.ready():
            # white foreground on transparent background, even for labeled images
            binct = [0, QColor(255, 255, 255, 255).rgba()]
            binaryimagesrc = createDataSource(segmentedSlot)
            binLayer = ColortableLayer(binaryimagesrc, binct)
            binLayer.name = "Binary image"
            binLayer.visible = True
            binLayer.opacity = 1.0
            binLayer.setToolTip("Segmented objects, binary mask")
            layers.append(binLayer)

        if atlas_slot.ready():
            layers.append(self.createStandardLayerFromSlot(atlas_slot, name="Atlas", opacity=0.5))

        # since we start with existing labels, it makes sense to start
        # with the first one selected. This would make more sense in
        # __init__(), but it does not take effect there.
        # self.selectLabel(0)

        return layers

    def _disconnect_dataChange_callback(self, colortable_changed_callback, *args):
        """
        When instances of the prediction layer are garbage collected, we no longer want the list model to call them back.
        This function disconnects the signal that was connected in setupLayers, above.
        """
        self._labelControlUi.labelListModel.dataChanged.disconnect(colortable_changed_callback)

    def _setPredictionColorTable(self, weak_predictLayer, index1, index2):
        predictLayer = weak_predictLayer()
        if predictLayer is None:
            return
        row = index1.row()
        self._setPredictionColorTableForRow(predictLayer, row)

    def _setPredictionColorTableForRow(self, predictLayer, row):

        if row >= 0 and row < self._labelControlUi.labelListModel.rowCount():
            element = self._labelControlUi.labelListModel[row]
            try:
                oldcolor = self._colorTable_forpmaps[row + 1]
            except IndexError:
                self._colorTable_forpmaps.append(element.pmapColor().rgba())
                predictLayer.colorTable = self._colorTable_forpmaps
                return

            if oldcolor != element.pmapColor().rgba():
                self._colorTable_forpmaps[row + 1] = element.pmapColor().rgba()
                predictLayer.colorTable = self._colorTable_forpmaps

    @staticmethod
    def _getObject(slot, pos5d):
        slicing = tuple(slice(i, i + 1) for i in pos5d)
        arr = slot[slicing].wait()
        return arr.flat[0]

    def _updateObjLabel(self, imageIndex, pos5d, label):
        try:
            new_labels, old_label, dirty_key = self.topLevelOperatorView.prepareObjectLabels(imageIndex, pos5d)
        except InvalidObjectIndex:
            return

        self._undoStack.push(
            LabelObjectCommand(
                slot=self.topLevelOperatorView.LabelInputs,
                labelsdict=new_labels,
                old_value=old_label,
                new_value=label,
                dirty_key=dirty_key,
            )
        )

    def onClick(self, layer, pos5d, pos):
        """Extracts the object index that was clicked on and updates
        that object's label.

        """
        label = self.editor.brushingModel.drawnNumber
        if label == self.editor.brushingModel.erasingNumber:
            label = 0

        topLevelOp = self.topLevelOperatorView.viewed_operator()
        imageIndex = topLevelOp.LabelInputs.index(self.topLevelOperatorView.LabelInputs)

        operatorAxisOrder = self.topLevelOperatorView.SegmentationImagesOut.meta.getAxisKeys()
        assert operatorAxisOrder == list(
            "txyzc"
        ), "Need to update onClick() if the operator no longer expects volumina axis order.  Operator wants: {}".format(
            operatorAxisOrder
        )
        self._updateObjLabel(imageIndex, pos5d, label)

    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        layer = self.getLayer("Labels")
        obj = self._getObject(layer.segmentationImageSlot, position5d)
        if obj == 0:
            return

        menu = QMenu(self)
        text = "Print info for object {} in the terminal".format(obj)
        menu.addAction(text)

        menu.addSeparator()
        clearlabel = "Clear label for object {}".format(obj)
        menu.addAction(clearlabel)
        numLabels = self.labelListData.rowCount()
        label_actions = []
        for l in range(numLabels):
            color_icon = self.labelListData.createIconForLabel(l)
            act_text = 'Label object {} as "{}"'.format(obj, self.labelListData[l].name)
            act = QAction(color_icon, act_text, menu)
            act.setIconVisibleInMenu(True)
            label_actions.append(act_text)
            menu.addAction(act)

        action = menu.exec_(globalWindowCoordinate)
        if action is None:
            return
        if action.text() == text:
            numpy.set_printoptions(precision=4)
            print("------------------------------------------------------------")
            print("object:         {}".format(obj))

            t = position5d[0]
            labels = self.op.LabelInputs([t]).wait()[t]
            if len(labels) > obj:
                label = int(labels[obj])
            else:
                label = "none"
            print("label:          {}".format(label))
            feats = self.op.ObjectFeatures[t].wait()[t]

            if "original_oid" in feats.get(default_features_key, {}):
                print(f"original_oid: {feats[default_features_key]['original_oid'][obj][0]}")

            if "AtlasMapping" in feats.get(default_features_key, {}):
                print(f"AtlasMapping:     {feats[default_features_key]['AtlasMapping'][obj][0]}")

            print("features:")

            selected = self.op.SelectedFeatures([]).wait()
            for plugin in sorted(feats.keys()):
                if plugin == default_features_key or plugin not in selected:
                    continue
                print("Feature category: {}".format(plugin))
                for featname in sorted(feats[plugin].keys()):
                    if featname not in selected[plugin]:
                        continue
                    value = feats[plugin][featname]
                    ft = numpy.asarray(value.squeeze())[obj]
                    print("{}: {}".format(featname, ft))

            if len(selected) > 0:
                pred = "none"
                if self.op.Predictions.ready():
                    preds = self.op.Predictions([t]).wait()[t]
                    if len(preds) >= obj:
                        pred = int(preds[obj])

                prob = "none"
                if self.op.Probabilities.ready():
                    probs = self.op.Probabilities([t]).wait()[t]
                    if len(probs) >= obj:
                        prob = probs[obj]

                print("probabilities:  {}".format(prob))
                print("prediction:     {}".format(pred))

                uncertainty = "none"
                if self.op.UncertaintyEstimate.ready():
                    uncertainties = self.op.UncertaintyEstimate([t]).wait()[t]
                    if len(uncertainties) >= obj:
                        uncertainty = uncertainties[obj]

                print("uncertainty:    {}".format(uncertainty))

            print("------------------------------------------------------------")
        elif action.text() == clearlabel:
            topLevelOp = self.topLevelOperatorView.viewed_operator()
            imageIndex = topLevelOp.LabelInputs.index(self.topLevelOperatorView.LabelInputs)
            self._updateObjLabel(imageIndex, position5d, 0)

        # todo: remove old
        elif self.applet.connected_to_knime:
            if action.text() == knime_hilite:
                data = {"command": 0, "objectid": "Row" + str(obj)}
                self.applet.sendMessageToServer("knime", data)
            elif action.text() == knime_unhilite:
                data = {"command": 1, "objectid": "Row" + str(obj)}
                self.applet.sendMessageToServer("knime", data)
            elif action.text() == knime_clearhilite:
                data = {"command": 2}
                self.applet.sendMessageToServer("knime", data)

        else:
            try:
                label = label_actions.index(action.text())
            except ValueError:
                return
            topLevelOp = self.topLevelOperatorView.viewed_operator()
            imageIndex = topLevelOp.LabelInputs.index(self.topLevelOperatorView.LabelInputs)
            self._updateObjLabel(imageIndex, position5d, label + 1)

    def setVisible(self, visible):
        super(ObjectClassificationGui, self).setVisible(visible)

        if visible:
            subslot_index = self.op.current_view_index()
            if subslot_index == -1:
                return
            # just clears all labels atm.
            self.op.triggerTransferLabelsAll()
            # FIXME: this needs to be revived once transferLabels is fixed
            # if temp is not None:
            #     new_labels, old_labels_lost, new_labels_lost = temp
            #     labels_lost = dict(list(old_labels_lost.items()) + list(new_labels_lost.items()))
            #     if sum(len(v) for v in labels_lost.values()) > 0:
            #         self.warnLost(labels_lost)

    @threadRouted
    def warnLost(self, labels_lost):
        box = QMessageBox(
            QMessageBox.Warning, "Warning", "Some of your labels could not be transferred", QMessageBox.NoButton, self
        )
        messages = {
            "full": "These labels were lost completely:",
            "partial": "These labels were lost partially:",
            "conflict": "These new labels conflicted:",
        }
        default_message = "These labels could not be transferred:"

        _sep = "\t"
        cases = []
        for k, val in labels_lost.items():
            if len(val) > 0:
                msg = messages.get(k, default_message)
                axis = _sep.join(["X", "Y", "Z"])
                coords = "\n".join([_sep.join(["{:<8.1f}".format(i) for i in item]) for item in val])
                cases.append("\n".join([msg, axis, coords]))
        box.setDetailedText("\n\n".join(cases))
        self.logBox(box)
        box.show()

    @threadRouted
    def handleWarnings(self, *args, **kwargs):
        """
        handle incoming warning messages by opening a pop-up window
        """
        # FIXME: dialog should not steal focus

        # get warning from operator
        warning = self.op.Warnings[:].wait()

        # log the warning message in any case
        logger.warning(warning["text"])

        # create dialog only once to prevent a pop-up window cascade
        if self.badObjectBox is None:
            box = BadObjectsDialog(warning, self)
            box.move(self.geometry().width(), 0)
            self.badObjectBox = box
        box = self.badObjectBox
        box.setWindowTitle(warning["title"])
        box.setText(warning["text"])
        box.setInformativeText(warning.get("info", ""))
        box.setDetailedText(warning.get("details", ""))

        box.show()

    def get_gui_applet(self):
        return self.applet

    def get_export_dialog_title(self):
        return "Export Object Information"


# Overload QTableWidgetItem class to allow comparisons of float instead of strings
class QTableWidgetItemWithFloatSorting(QTableWidgetItem):
    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):

            my_value = float(self.data(Qt.EditRole))
            other_value = float(other.data(Qt.EditRole))

            if my_value is not None and other_value is not None:
                return my_value < other_value

        return super(QTableWidgetItemWithFloatSorting, self).__lt__(other)


class LabelAssistDialog(QDialog):
    """
    A simple UI for showing bookmarks and navigating to them.

    FIXME: For now, this window is tied to a particular lane.
           If your project has more than one lane, then each one
           will have it's own bookmark window, which is kinda dumb.
    """

    def __init__(self, parent, topLevelOperatorView):
        super(LabelAssistDialog, self).__init__(parent)

        # Create thread router to populate table on main thread
        self.threadRouter = ThreadRouter(self)

        # Set object classification operator view
        self.topLevelOperatorView = topLevelOperatorView

        self.setWindowTitle("Label Assist")
        self.setMinimumWidth(500)
        self.setMinimumHeight(700)

        layout = QGridLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Show variable importance table
        rows = 0
        columns = 4
        self.table = QTableWidget(rows, columns)
        self.table.setHorizontalHeaderLabels(["Frame", "Max Area", "Min Area", "Labels"])
        self.table.verticalHeader().setVisible(False)

        # Select full row on-click and call capture double click
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.doubleClicked.connect(self._captureDoubleClick)

        layout.addWidget(self.table, 1, 0, 3, 2)

        # Create progress bar
        self.progressBar = QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.hide()
        layout.addWidget(self.progressBar, 4, 0, 1, 2)

        # Create button to populate table
        self.computeButton = QPushButton("Compute object info")
        self.computeButton.clicked.connect(self._triggerTableUpdate)
        layout.addWidget(self.computeButton, 5, 0)

        # Create close button
        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.close)
        layout.addWidget(closeButton, 5, 1)

        # Set dialog layout
        self.setLayout(layout)

    def _triggerTableUpdate(self):
        # Check that object area is included in selected features
        featureNames = self.topLevelOperatorView.SelectedFeatures.value

        if "Standard Object Features" not in featureNames or "Count" not in featureNames["Standard Object Features"]:
            box = QMessageBox(
                QMessageBox.Warning,
                "Warning",
                'Object area is not a selected feature. Please select this feature on: "Standard Object Features > Shape > Size in pixels"',
                QMessageBox.NoButton,
                self,
            )
            box.show()
            return

        # Clear table
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        self.progressBar.show()
        self.computeButton.setEnabled(False)

        def compute_features_for_frame(tIndex, t, features):
            # Compute features and labels (called in parallel from request pool)
            roi = [slice(None) for i in range(len(self.topLevelOperatorView.LabelImages.meta.shape))]
            roi[tIndex] = slice(t, t + 1)
            roi = tuple(roi)

            frame = self.topLevelOperatorView.SegmentationImages(roi).wait()
            frame = frame.squeeze().astype(numpy.uint32, copy=False)

            # Dirty trick: We don't care what we're passing here for the 'image' parameter,
            # but vigra insists that we pass *something*, so we'll cast the label image as float32.
            features[t] = vigra.analysis.extractRegionFeatures(
                frame.view(numpy.float32), frame, ["Count"], ignoreLabel=0
            )

        tIndex = self.topLevelOperatorView.SegmentationImages.meta.axistags.index("t")
        tMax = self.topLevelOperatorView.SegmentationImages.meta.shape[tIndex]

        features = {}
        labels = {}

        def compute_all_features():
            # Compute features in parallel
            pool = RequestPool()
            for t in range(tMax):
                pool.add(Request(partial(compute_features_for_frame, tIndex, t, features)))
            pool.wait()

        # Compute labels
        labels = self.topLevelOperatorView.LabelInputs([]).wait()

        req = Request(compute_all_features)
        req.notify_finished(partial(self._populateTable, features, labels))
        req.submit()

    @threadRouted
    def _populateTable(self, features, labels, *args):
        self.progressBar.hide()
        self.computeButton.setEnabled(True)

        for time, feature in features.items():
            # Insert row
            rowNum = self.table.rowCount()
            self.table.insertRow(self.table.rowCount())

            # Get max and min object areas
            areas = feature["Count"]  # objectFeatures['Standard Object Features']['Count']
            maxObjArea = numpy.max(areas[numpy.nonzero(areas)])
            minObjArea = numpy.min(areas[numpy.nonzero(areas)])

            # Get number of labeled objects
            labelNum = numpy.count_nonzero(labels[time])

            # Load fram number
            item = QTableWidgetItem(str(time))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(rowNum, 0, item)

            # Load max object areas
            item = QTableWidgetItemWithFloatSorting(str("{: .02f}".format(maxObjArea)))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(rowNum, 1, item)

            # Load min object areas
            item = QTableWidgetItemWithFloatSorting(str("{: .02f}".format(minObjArea)))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(rowNum, 2, item)

            # Load label numbers
            item = QTableWidgetItemWithFloatSorting(str("{: .01f}".format(labelNum)))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(rowNum, 3, item)

        # Resize column size to fit dialog size
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Sort by max object area
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.DescendingOrder)

    def _captureDoubleClick(self):
        # Navigate to selected frame
        index = self.table.selectedIndexes()[0]
        frameStr = self.table.item(index.row(), 0).text()

        if frameStr:
            frameNum = int(frameStr)
            self.parent().editor.posModel.time = frameNum


class BadObjectsDialog(QMessageBox):
    def __init__(self, warning, parent):
        super(BadObjectsDialog, self).__init__(
            QMessageBox.Warning, warning["title"], warning["text"], QMessageBox.NoButton, parent
        )
        self.setWindowModality(Qt.NonModal)
        # make a button to connect to the logging callback
        button = QPushButton(parent=self)
        button.setText("Print Details To Log...")

        self.addButton(QMessageBox.Close)
        self.addButton(button, QMessageBox.ActionRole)
        # do not close the dialog when print is clicked
        # => remove the 'close' callback
        button.clicked.disconnect()
        button.clicked.connect(self._printToLog)

    def _printToLog(self, *args, **kwargs):
        parts = []
        for s in (self.text(), self.informativeText(), self.detailedText()):
            if len(s) > 0:
                parts.append(s)
        msg = "\n".join(parts)
        logger.warning(msg)
