from PyQt4.QtGui import QWidget, QColor, QProgressDialog, QTreeWidgetItem, QMessageBox
from PyQt4 import uic
from PyQt4.QtCore import Qt, QString, QVariant, pyqtSignal, QObject

from lazyflow.rtype import SubRegion
import os
from collections import defaultdict

from ilastik.applets.base.appletGuiInterface import AppletGuiInterface
from functools import partial

try:
    from ilastik.plugins import pluginManager
except:
    print "Warning: could not import pluginManager"

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ConstantSource, \
                         LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables

import vigra
import numpy as np

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from PyQt4.QtGui import QDialog, QFileDialog, QAbstractItemView
from PyQt4 import uic

class FeatureSelectionDialog(QDialog):

    def __init__(self, featureDict, selectedFeatures=None, parent=None):
        QDialog.__init__(self, parent)
        self.featureDict = featureDict
        if selectedFeatures is None or len(selectedFeatures) == 0:
            selectedFeatures = defaultdict(list)
        self.selectedFeatures = selectedFeatures
        self.setWindowTitle("Object Features")
        ui_class, widget_class = uic.loadUiType(os.path.split(__file__)[0] + "/featureSelection.ui")
        self.ui = ui_class()
        self.ui.setupUi(self)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        self.ui.allButton.pressed.connect(self.handleAll)
        self.ui.noneButton.pressed.connect(self.handleNone)

        self.ui.treeWidget.clicked.connect(self.handleClick)

        self.ui.treeWidget.setColumnCount(1)
        for pluginName, features in featureDict.iteritems():
            parent = QTreeWidgetItem(self.ui.treeWidget)
            parent.setText(0, pluginName)
            parent.setExpanded(True)
            for name in sorted(features):
                item = QTreeWidgetItem(parent)
                item.setText(0, name)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                if name in self.selectedFeatures[pluginName]:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)

    def handleClick(self, index):
        item = self.ui.treeWidget.itemFromIndex(index)
        state = item.checkState(0)
        if state == Qt.Checked:
            item.setCheckState(0, Qt.Unchecked)
        else:
            item.setCheckState(0, Qt.Checked)

    def accept(self):
        QDialog.accept(self)
        selectedFeatures = defaultdict(list)
        root = self.ui.treeWidget.invisibleRootItem()
        for parent in root.takeChildren():
            feats = list(str(item.text(0)) for item in parent.takeChildren()
                         if item.checkState(0) == Qt.Checked)
            if len(feats) > 0:
                selectedFeatures[str(parent.text(0))] = feats
        self.selectedFeatures = selectedFeatures

    def _setAll(self, val):
        root = self.ui.treeWidget.invisibleRootItem()
        for parent_id in range(root.childCount()):
            parent = root.child(parent_id)
            for child_id in range(parent.childCount()):
                child = parent.child(child_id)
                child.setCheckState(0, val)

    def handleAll(self):
        self._setAll(Qt.Checked)

    def handleNone(self):
        self._setAll(Qt.Unchecked)


class ObjectExtractionGui(QWidget):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget(self):
        """ Return the widget that will be displayed in the main viewer area. """
        return self.volumeEditorWidget

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        return []

    def viewerControlWidget(self):
        return self._viewerControlWidget

    def stopAndCleanUp(self):
        pass

    ###########################################
    ###########################################

    def __init__(self, topLevelOperatorView):
        super(ObjectExtractionGui, self).__init__()
        self.mainOperator = topLevelOperatorView
        self.layerstack = LayerStackModel()

        self._viewerControlWidget = None
        self._initViewerControlUi()

        self.editor = None
        self._initEditor()

        self._initAppletDrawerUi()
        assert(self.appletDrawer() is not None)
        self._initViewer()

    def _onMetaChanged(self, slot):
        if slot is self.mainOperator.BinaryImage:
            if slot.meta.shape:
                self.editor.dataShape = slot.meta.shape

        if slot is self.mainOperator.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource(self.mainOperator.RawImage)
                layerraw = GrayscaleLayer(self.rawsrc)
                layerraw.name = "Raw"
                self.layerstack.append(layerraw)

    def _onReady(self, slot):
        if slot is self.mainOperator.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource(self.mainOperator.RawImage)
                layerraw = GrayscaleLayer(self.rawsrc)
                layerraw.name = "Raw"
                self.layerstack.append(layerraw)

    def _initViewer(self):
        mainOperator = self.mainOperator

        # white foreground on transparent background
        ct = [QColor(0, 0, 0, 0).rgba(),
              QColor(255, 255, 255, 255).rgba()]
        self.binaryimagesrc = LazyflowSource(mainOperator.BinaryImage)
        self.binaryimagesrc.setObjectName("Binary LazyflowSrc")
        layer = ColortableLayer(self.binaryimagesrc, ct)
        layer.name = "Binary Image"
        self.layerstack.append(layer)

        ct = colortables.create_default_16bit()
        self.objectssrc = LazyflowSource(mainOperator.LabelImage)
        self.objectssrc.setObjectName("LabelImage LazyflowSrc")
        ct[0] = QColor(0, 0, 0, 0).rgba() # make 0 transparent
        layer = ColortableLayer(self.objectssrc, ct)
        layer.name = "Label Image"
        layer.visible = False
        layer.opacity = 0.5
        self.layerstack.append(layer)

        self.centerimagesrc = LazyflowSource(mainOperator.ObjectCenterImage)
        layer = RGBALayer(red=ConstantSource(255), alpha=self.centerimagesrc)
        layer.name = "Object Centers"
        layer.visible = False
        self.layerstack.append(layer)

        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource(self.mainOperator.RawImage)
        self.rawsrc.setObjectName("Raw Lazyflow Src")
        layerraw = GrayscaleLayer(self.rawsrc)
        layerraw.name = "Raw"
        self.layerstack.insert(len(self.layerstack), layerraw)

        mainOperator.RawImage.notifyReady(self._onReady)
        mainOperator.RawImage.notifyMetaChanged(self._onMetaChanged)

        if mainOperator.BinaryImage.meta.shape:
            self.editor.dataShape = mainOperator.BinaryImage.meta.shape
        mainOperator.BinaryImage.notifyMetaChanged(self._onMetaChanged)

    def _initEditor(self):
        """Initialize the Volume Editor GUI."""

        self.editor = VolumeEditor(self.layerstack, crosshair=False)

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
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        self._drawer.selectFeaturesButton.pressed.connect(self._selectFeaturesButtonPressed)

    def _initViewerControlUi(self):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def _selectFeaturesButtonPressed(self):
        featureDict = {}
        slot = self.mainOperator.Features
        if slot.ready():
            selectedFeatures = self.mainOperator.Features([]).wait()
        else:
            selectedFeatures = None

        try:
            plugins = pluginManager.getPluginsOfCategory('ObjectFeatures')
        except:
            QMessageBox.warning(self,
                                'object features unavailable',
                                'Object features plugins failed. Perhaps Yapsy is not installed?',
                                QMessageBox.Ok)
            return

        for pluginInfo in plugins:
            featureDict[pluginInfo.name] = pluginInfo.plugin_object.availableFeatures()
        dlg = FeatureSelectionDialog(featureDict=featureDict,
                                     selectedFeatures=selectedFeatures)
        dlg.exec_()

        if dlg.result() == QDialog.Accepted:
            self.mainOperator.Features.setValue(dlg.selectedFeatures)
            self._calculateFeatures()

    def _calculateFeatures(self):
        self.mainOperator.ObjectCenterImage.setDirty(SubRegion(self.mainOperator.ObjectCenterImage))

        maxt = self.mainOperator.LabelImage.meta.shape[0]
        progress = QProgressDialog("Calculating features...", "Cancel", 0, maxt)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        # We will use notify_finished() to update the progress bar.
        # However, the callback will be called from a non-gui thread,
        # which cannot access gui elements directly. Therefore we use
        # this callback object to send signals back to this thread.
        class Callback(QObject):
            ndone = 0
            timestep_done = pyqtSignal(int)
            all_finished = pyqtSignal()

            def __call__(self, *args, **kwargs):
                self.ndone += 1
                self.timestep_done.emit(self.ndone)
                if self.ndone == len(reqs):
                    self.all_finished.emit()
        callback = Callback()

        def updateProgress(progress, n):
            progress.setValue(n)
        callback.timestep_done.connect(partial(updateProgress, progress))

        def finished():
            self.mainOperator._opRegFeats.fixed = True
            print 'Object Extraction: done.'
        callback.all_finished.connect(finished)

        self.mainOperator._opRegFeats.fixed = False
        reqs = []
        for t in range(maxt):
            req = self.mainOperator.RegionFeatures([t])
            req.submit()
            reqs.append(req)

        for i, req in enumerate(reqs):
            req.notify_finished(callback)

        # handle cancel button
        def cancel():
            for req in reqs:
                req.cancel()
        progress.canceled.connect(cancel)
