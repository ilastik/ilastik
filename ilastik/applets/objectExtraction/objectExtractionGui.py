from PyQt4.QtGui import QWidget, QColor, QProgressDialog, QTreeWidgetItem, QMessageBox, QIntValidator
from PyQt4 import uic
from PyQt4.QtCore import Qt, QString, QVariant, pyqtSignal, QObject

from lazyflow.rtype import SubRegion
import os
from collections import defaultdict

from ilastik.applets.base.appletGuiInterface import AppletGuiInterface
from ilastik.applets.layerViewer import LayerViewerGui
from functools import partial
from ilastik.applets.objectExtraction.opObjectExtraction import max_margin

from ilastik.plugins import pluginManager

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ConstantSource, \
                         LayerStackModel, VolumeEditor, VolumeEditorWidget, ColortableLayer
import volumina.colortables as colortables
from ilastik.widgets.viewerControls import ViewerControls

import vigra
import numpy as np

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from PyQt4.QtGui import QDialog, QFileDialog, QAbstractItemView
from PyQt4 import uic

class FeatureSelectionDialog(QDialog):
    # for now all features get the same margin parameter. In the
    # future this should be selectable per feature, and only for
    # global features.
    default_margin = (30, 30, 1)

    def __init__(self, featureDict, selectedFeatures=None, parent=None, ndim=3):
        """
        Parameters:
        * featureDict: a nested dictionary. {plugin name : {feature name : {parameter name : parameter}}
        * selectedDict: like featureDict. entries will be checked and their parameters populated.

        """
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

        self.populate()
        self.ndim = ndim
        self.set_margin()

    def populate(self):
        self.ui.treeWidget.setColumnCount(1)
        for pluginName, features in self.featureDict.iteritems():
            parent = QTreeWidgetItem(self.ui.treeWidget)
            parent.setText(0, pluginName)
            parent.setExpanded(True)
            for name in sorted(features.keys()):
                parameters = features[name]
                item = QTreeWidgetItem(parent)
                item.setText(0, name)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

                # hack to ensure checkboxes visible
                item.setCheckState(0, Qt.Checked)
                item.setCheckState(0, Qt.Unchecked)

                if pluginName in self.selectedFeatures:
                    if name in self.selectedFeatures[pluginName]:
                        item.setCheckState(0, Qt.Checked)

    def set_margin(self):
        if self.ndim>3 or self.ndim<2:
            print "wrong dimensions setting for feature selection dialog"
            return
        default = [-1]*self.ndim
        margin = max_margin(self.selectedFeatures, default)
        
        if -1 in margin:
            margin = self.default_margin
        #self.ui.marginEdit.setText(str(margin))
        self.ui.spinBox_X.setValue(margin[0])
        self.ui.spinBox_Y.setValue(margin[1])
        if self.ndim==3:
            self.ui.spinBox_Z.setValue(margin[2])
        else:
            self.ui.spinBox_Z.setEnabled(False)

    def accept(self):
        QDialog.accept(self)
        selectedFeatures = defaultdict(list)
        
        margin = [self.ui.spinBox_X.value(), self.ui.spinBox_Y.value()]
        if self.ndim==3:
            margin.append(self.ui.spinBox_Z.value())
        root = self.ui.treeWidget.invisibleRootItem()
        for parent in root.takeChildren():
            plugin = str(parent.text(0))
            featnames = list(str(item.text(0)) for item in parent.takeChildren()
                         if item.checkState(0) == Qt.Checked)
            if len(featnames) > 0:
                features = {}
                for f in featnames:
                    features[f] = {}
                    if 'margin' in self.featureDict[plugin][f]:
                        features[f]['margin'] = margin
                selectedFeatures[plugin] = features
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


class ObjectExtractionGui(LayerViewerGui):

    def setupLayers(self):
        mainOperator = self.topLevelOperatorView
        layers = []

        if mainOperator.ObjectCenterImage.ready():
            self.centerimagesrc = LazyflowSource(mainOperator.ObjectCenterImage)
            #layer = RGBALayer(red=ConstantSource(255), alpha=self.centerimagesrc)
            redct = [0, QColor(255, 0, 0).rgba()]
            layer = ColortableLayer(self.centerimagesrc, redct)
            layer.name = "Object Centers"
            layer.visible = False
            layers.append(layer)

        ct = colortables.create_default_16bit()
        if mainOperator.LabelImage.ready():
            self.objectssrc = LazyflowSource(mainOperator.LabelImage)
            self.objectssrc.setObjectName("LabelImage LazyflowSrc")
            ct[0] = QColor(0, 0, 0, 0).rgba() # make 0 transparent
            layer = ColortableLayer(self.objectssrc, ct)
            layer.name = "Label Image"
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)

        # white foreground on transparent background
        binct = [QColor(0, 0, 0, 0).rgba(), QColor(255, 255, 255, 255).rgba()]
        if mainOperator.BinaryImage.ready():
            self.binaryimagesrc = LazyflowSource(mainOperator.BinaryImage)
            self.binaryimagesrc.setObjectName("Binary LazyflowSrc")
            layer = ColortableLayer(self.binaryimagesrc, binct)
            layer.name = "Binary Image"
            layers.append(layer)

        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource(mainOperator.RawImage)
        self.rawsrc.setObjectName("Raw Lazyflow Src")
        layerraw = GrayscaleLayer(self.rawsrc)
        layerraw.name = "Raw"
        layers.insert(len(layers), layerraw)

        mainOperator.RawImage.notifyReady(self._onReady)
        mainOperator.RawImage.notifyMetaChanged(self._onMetaChanged)

        if mainOperator.BinaryImage.meta.shape:
            self.editor.dataShape = mainOperator.BinaryImage.meta.shape
        mainOperator.BinaryImage.notifyMetaChanged(self._onMetaChanged)

        return layers

    def _onMetaChanged(self, slot):
        #FiXME: why do we need that?
        if slot is self.topLevelOperatorView.BinaryImage:
            if slot.meta.shape:
                self.editor.dataShape = slot.meta.shape

        if slot is self.topLevelOperatorView.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource(self.topLevelOperatorView.RawImage)
                layerraw = GrayscaleLayer(self.rawsrc)
                layerraw.name = "Raw"
                self.layerstack.append(layerraw)

    def _onReady(self, slot):
        if slot is self.topLevelOperatorView.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource(self.topLevelOperatorView.RawImage)
                layerraw = GrayscaleLayer(self.rawsrc)
                layerraw.name = "Raw"
                self.layerstack.append(layerraw)


    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        self._drawer.selectFeaturesButton.pressed.connect(self._selectFeaturesButtonPressed)

    def _selectFeaturesButtonPressed(self):
        featureDict = {}
        mainOperator = self.topLevelOperatorView
        slot = mainOperator.Features
        if slot.ready():
            selectedFeatures = mainOperator.Features([]).wait()
        else:
            selectedFeatures = None

        plugins = pluginManager.getPluginsOfCategory('ObjectFeatures')

        imgshape = list(mainOperator.RawImage.meta.shape)
        axistags = mainOperator.RawImage.meta.axistags
        imgshape.pop(axistags.index('t'))
        fakeimg = np.empty(imgshape, dtype=np.float32)

        labelshape = list(mainOperator.BinaryImage.meta.shape)
        axistags = mainOperator.BinaryImage.meta.axistags
        labelshape.pop(axistags.index('t'))
        labelshape.pop(axistags.index('c') - 1)
        fakelabels = np.empty(labelshape, dtype=np.uint32)
        
        ndim = 3
        zIndex = axistags.index('z')
        if len(labelshape)==2 or (zIndex<len(mainOperator.RawImage.meta.shape) and mainOperator.RawImage.meta.shape[zIndex]==1):
            ndim=2
        

        for pluginInfo in plugins:
            featureDict[pluginInfo.name] = pluginInfo.plugin_object.availableFeatures(fakeimg, fakelabels)
        dlg = FeatureSelectionDialog(featureDict=featureDict,
                                     selectedFeatures=selectedFeatures, ndim=ndim)
        dlg.exec_()

        if dlg.result() == QDialog.Accepted:
            mainOperator.Features.setValue(dlg.selectedFeatures)
            self._calculateFeatures()

    def _calculateFeatures(self):
        mainOperator = self.topLevelOperatorView
        mainOperator.ObjectCenterImage.setDirty(SubRegion(mainOperator.ObjectCenterImage))

        maxt = mainOperator.LabelImage.meta.shape[0]
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
            self.topLevelOperatorView._opRegFeats.fixed = True
            print 'Object Extraction: done.'
        callback.all_finished.connect(finished)

        mainOperator._opRegFeats.fixed = False
        reqs = []
        for t in range(maxt):
            req = mainOperator.RegionFeatures([t])
            req.submit()
            reqs.append(req)

        for i, req in enumerate(reqs):
            req.notify_finished(callback)

        # handle cancel button
        def cancel():
            for req in reqs:
                req.cancel()
        progress.canceled.connect(cancel)


class ObjectExtractionGuiNonInteractive(ObjectExtractionGui):
    def _selectFeaturesButtonPressed(self):
        self.topLevelOperatorView.Features.setValue({})
        self._calculateFeatures()

    def initAppletDrawerUi(self):
        super(ObjectExtractionGuiNonInteractive, self).initAppletDrawerUi()
        self._drawer.selectFeaturesButton.setText('Calculate features')
