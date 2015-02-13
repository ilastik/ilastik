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
#		   http://ilastik.org/license.html
###############################################################################
from PyQt4.QtGui import QColor, QTreeWidgetItem, QMessageBox
from PyQt4 import uic
from PyQt4.QtCore import Qt

from lazyflow.rtype import SubRegion
import os
from collections import defaultdict

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from functools import partial
from ilastik.applets.objectExtraction.opObjectExtraction import max_margin

from ilastik.plugins import pluginManager
from ilastik.utility.gui import threadRouted
from ilastik.utility import log_exception
from ilastik.config import cfg as ilastik_config

from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer
import volumina.colortables as colortables
from volumina.utility import encode_from_qstring

import vigra
import numpy as np

from PyQt4.QtGui import QDialog, QFileDialog

import cPickle as pickle
import threading

import logging
from _collections import defaultdict
logger = logging.getLogger(__name__)

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

        self.countChecked = {}
        self.countAll = {}
        self.populate()
        self.ui.treeWidget.itemClicked.connect(self.updateTree)
        self.ndim = ndim
        
        self.set_margin()
        self.setObjectName("FeatureSelectionDialog")

    def populate(self):
        self.ui.treeWidget.setColumnCount(1)
        for pluginName, features in self.featureDict.iteritems():
            if pluginName=="TestFeatures" and not ilastik_config.getboolean("ilastik", "debug"):
                continue
            parent = QTreeWidgetItem(self.ui.treeWidget)
            parent.setText(0, pluginName)
            parent.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            # hack to ensure checkboxes visible
            parent.setCheckState(0, Qt.Checked)
            parent.setCheckState(0, Qt.Unchecked)
            parent.setExpanded(False)
            self.countChecked[pluginName]=0
            self.countAll[pluginName]=len(self.featureDict[pluginName])
            advanced_names = []
            simple_names = []
            for name in sorted(features.keys()):
                parameters = features[name]
                if 'advanced' in parameters:
                    advanced_names.append(name)
                else:
                    simple_names.append(name)
            
            for name in simple_names+advanced_names:
                parameters = features[name]
                
                item = QTreeWidgetItem(parent)
                item.setText(0, name)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                if 'tooltip' in parameters:
                    item.setToolTip(0, parameters['tooltip'])
                # hack to ensure checkboxes visible
                item.setCheckState(0, Qt.Checked)
                item.setCheckState(0, Qt.Unchecked)
                if pluginName in self.selectedFeatures:
                    if name in self.selectedFeatures[pluginName]:
                        item.setCheckState(0, Qt.Checked)
                        self.countChecked[pluginName]+=1
            if self.countChecked[pluginName] == 0:
                parent.setCheckState(0, Qt.Unchecked)
            elif self.countChecked[pluginName] == self.countAll[pluginName]:
                parent.setCheckState(0, Qt.Checked)
            else:
                parent.setCheckState(0, Qt.PartiallyChecked)
            self.updateToolTip(parent)
        # facilitates switching of the CheckBox when clicking on the Text of a QTreeWidgetItem
        self.ui.treeWidget.setCurrentItem(None)

    def updateTree(self, item, col):
        # Clicking on the CheckBox OR Text of a QTreeWidgetItem should change the check.
        # QTreeWidget signal itemClicked gets triggered by clicking on:
        # (a) the item's CheckBox (changes the check but does NOT reset the self.ui.treeWidget.currentItem)
        # (b) the item's Text (sets the self.ui.treeWidget.currentItem but does NOT change the CheckBox automatically)
        # Because we maintain self.ui.treeWidget.currentItem @ None
        # the self.ui.treeWidget.currentItem only gets changed when the signal is triggered by clicking on the text.
        # Relies on self.ui.treeWidget.setCurrentItem(None) in populate()
        itemParent = item.parent()
        currentItem = self.ui.treeWidget.currentItem()
        if itemParent == None: # user clicked a Plugin Name
            pluginName=str(item.text(0))
            if currentItem == item: # user clicked on the text
                if item.checkState(0) == Qt.PartiallyChecked or item.checkState(0) == Qt.Unchecked:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
            self.ui.treeWidget.setCurrentItem(None)
            if not item.checkState(0) == Qt.PartiallyChecked:
                for child_id in range(item.childCount()):
                    child = item.child(child_id)
                    child.setCheckState(0, item.checkState(0))
                if item.checkState(0) == Qt.Checked:
                    self.countChecked[pluginName] = self.countAll[pluginName]
                elif item.checkState(0) == Qt.Unchecked:
                    self.countChecked[pluginName] = 0
            self.updateToolTip(item)
        else: # user clicked a Feature
            pluginName=str(itemParent.text(0))
            itemName=str(item.text(0))
            if currentItem == item: # user clicked on the text
                if item.checkState(0) == Qt.Checked:
                    item.setCheckState(0, Qt.Unchecked)
                else:
                    item.setCheckState(0, Qt.Checked)
            self.ui.treeWidget.setCurrentItem(None)
            num=0
            for child_id in range(itemParent.childCount()):
                child = itemParent.child(child_id)
                if child.checkState(0) == Qt.Checked:
                    num+=1
            self.countChecked[pluginName]=num
            if self.countChecked[pluginName] == 0:
                itemParent.setCheckState(0, Qt.Unchecked)
            elif self.countChecked[pluginName] == self.countAll[pluginName]:
                itemParent.setCheckState(0, Qt.Checked)
            else:
                itemParent.setCheckState(0, Qt.PartiallyChecked)
            self.updateToolTip(itemParent)

    def updateToolTip(self, item):
        name = str(item.text(0))
        item.setToolTip(0, name+" ("+str(self.countChecked[name])+" Features Checked / "+str(self.countAll[name])+" Features)")

    def set_margin(self):
        if self.ndim > 3 or self.ndim < 2:
            logger.warn("wrong dimensions setting for feature selection dialog")
            return
        default = [-1]*self.ndim
        margin = max_margin(self.selectedFeatures, default)
        
        if -1 in margin:
            margin = self.default_margin
        self.ui.spinBox_X.setValue(margin[0])
        self.ui.spinBox_Y.setValue(margin[1])
        if self.ndim==3:
            self.ui.spinBox_Z.setValue(margin[2])
        else:
            self.ui.spinBox_Z.setVisible(False)
            self.ui.label_z.setVisible(False)

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
                    if 'advanced' in self.featureDict[plugin][f]:
                        features[f]['advanced'] = True
                selectedFeatures[plugin] = features
        self.selectedFeatures = selectedFeatures

    def _setAll(self, val):
        root = self.ui.treeWidget.invisibleRootItem()
        for parent_id in range(root.childCount()):
            parent = root.child(parent_id)
            parent.setCheckState(0, val)
            for child_id in range(parent.childCount()):
                child = parent.child(child_id)
                child.setCheckState(0, val)
            parentName=str(parent.text(0))
            if val == Qt.Checked:
                self.countChecked[parentName]=self.countAll[parentName]
            else:
                self.countChecked[parentName]=0
            self.updateToolTip(parent)

    def handleAll(self):
        self._setAll(Qt.Checked)

    def handleNone(self):
        self._setAll(Qt.Unchecked)


class ObjectExtractionGui(LayerViewerGui):
    
    def stopAndCleanUp(self):
        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        super(ObjectExtractionGui, self).stopAndCleanUp()

    def __init__(self, *args, **kwargs):
        self.__cleanup_fns = []
        self._lock = threading.Lock()
        super( ObjectExtractionGui, self ).__init__(*args, **kwargs)

    def setupLayers(self):
        mainOperator = self.topLevelOperatorView
        layers = []

        if mainOperator.ObjectCenterImage.ready():
            self.centerimagesrc = LazyflowSource(mainOperator.ObjectCenterImage)
            redct = [0, QColor(255, 0, 0).rgba()]
            layer = ColortableLayer(self.centerimagesrc, redct)
            layer.name = "Object centers"
            layer.setToolTip("Object center positions, marked with a little red cross")
            layer.visible = False
            layers.append(layer)

        ct = colortables.create_default_16bit()
        if mainOperator.LabelImage.ready():
            self.objectssrc = LazyflowSource(mainOperator.LabelImage)
            self.objectssrc.setObjectName("LabelImage LazyflowSrc")
            ct[0] = QColor(0, 0, 0, 0).rgba() # make 0 transparent
            layer = ColortableLayer(self.objectssrc, ct)
            layer.name = "Objects (connected components)"
            layer.setToolTip("Segmented objects, shown in different colors")
            layer.visible = False
            layer.opacity = 0.5
            layers.append(layer)

        # white foreground on transparent background, even for labeled images
        binct = [QColor(255, 255, 255, 255).rgba()]*65536
        binct[0] = 0
        if mainOperator.BinaryImage.ready():
            self.binaryimagesrc = LazyflowSource(mainOperator.BinaryImage)
            self.binaryimagesrc.setObjectName("Binary LazyflowSrc")
            layer = ColortableLayer(self.binaryimagesrc, binct)
            layer.name = "Binary image"
            layer.setToolTip("Segmented objects, binary mask")
            layers.append(layer)

        ## raw data layer
        self.rawsrc = None
        self.rawsrc = LazyflowSource(mainOperator.RawImage)
        self.rawsrc.setObjectName("Raw Lazyflow Src")
        layerraw = GrayscaleLayer(self.rawsrc)
        layerraw.name = "Raw data"
        layers.insert(len(layers), layerraw)

        mainOperator.RawImage.notifyReady(self._onReady)
        self.__cleanup_fns.append( partial( mainOperator.RawImage.unregisterReady, self._onReady ) )

        mainOperator.RawImage.notifyMetaChanged(self._onMetaChanged)
        self.__cleanup_fns.append( partial( mainOperator.RawImage.unregisterMetaChanged, self._onMetaChanged ) )

        mainOperator.BinaryImage.notifyMetaChanged(self._onMetaChanged)
        self.__cleanup_fns.append( partial( mainOperator.BinaryImage.unregisterMetaChanged, self._onMetaChanged ) )

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
                layerraw.name = "Raw data"
                self.layerstack.append(layerraw)

    def _onReady(self, slot):
        if slot is self.topLevelOperatorView.RawImage:
            if slot.meta.shape and not self.rawsrc:
                self.rawsrc = LazyflowSource(self.topLevelOperatorView.RawImage)
                layerraw = GrayscaleLayer(self.rawsrc)
                layerraw.name = "Raw data"
                self.layerstack.append(layerraw)

    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        self._drawer.selectFeaturesButton.pressed.connect(self._selectFeaturesButtonPressed)
        if not ilastik_config.getboolean("ilastik", "debug"):
            self._drawer.exportButton.setVisible(False)
            
        self._drawer.exportButton.pressed.connect(self._exportFeaturesButtonPressed)
        
        slot = self.topLevelOperatorView.Features
        if slot.ready():
            selectedFeatures = self.topLevelOperatorView.Features([]).wait()
        else:
            selectedFeatures = None
        
        nfeatures = 0
        if selectedFeatures is not None:
            for plugin_features in selectedFeatures.itervalues():
                nfeatures += len(plugin_features)

        self._drawer.featuresSelected.setText("{} features computed, \nsome may have multiple channels".format(nfeatures))
        
        # get the applet reference from the workflow (needed for the progressSignal)
        self.applet = self.topLevelOperatorView.parent.parent.objectExtractionApplet

    def _selectFeaturesButtonPressed(self):
        featureDict = {}
        mainOperator = self.topLevelOperatorView
        if not mainOperator.RawImage.ready():
            mexBox=QMessageBox()
            mexBox.setText("Please add the raw data before selecting features")
            mexBox.exec_()
            return
        
        if not mainOperator.BinaryImage.ready():
            mexBox=QMessageBox()
            mexBox.setText("Please add binary (segmentation) data before selecting features ")
            mexBox.exec_()
            return
        
        slot = mainOperator.Features
        if slot.ready():
            selectedFeatures = mainOperator.Features([]).wait()
        else:
            selectedFeatures = None

        plugins = pluginManager.getPluginsOfCategory('ObjectFeatures')
        taggedShape = mainOperator.RawImage.meta.getTaggedShape()
        fakeimg = None
        fakeimgshp = [taggedShape['x'], taggedShape['y']]
        fakelabelsshp = [taggedShape['x'], taggedShape['y']]
        ndim = 3
        if 'z' in taggedShape and taggedShape['z']>1:
            fakeimgshp.append(taggedShape['z'])
            fakelabelsshp.append(taggedShape['z'])
            ndim = 3
        else:
            ndim = 2
        if 'c' in taggedShape and taggedShape['c']>1:
            fakeimgshp.append(taggedShape['c'])
        
        fakeimg = np.empty(fakeimgshp, dtype=np.float32)
        fakelabels = np.empty(fakelabelsshp, dtype=np.uint32)
        
        if ndim==3:
            fakelabels = vigra.taggedView(fakelabels, 'xyz')
            if len(fakeimgshp)==4:
                fakeimg = vigra.taggedView(fakeimg, 'xyzc')
            else:
                fakeimg = vigra.taggedView(fakeimg, 'xyz')
        if ndim==2:
            fakelabels = vigra.taggedView(fakelabels, 'xy')
            if len(fakeimgshp)==3:
                fakeimg = vigra.taggedView(fakeimg, 'xyc')
            else:
                fakeimg = vigra.taggedView(fakeimg, 'xy')
        for pluginInfo in plugins:
            availableFeatures = pluginInfo.plugin_object.availableFeatures(fakeimg, fakelabels)
            if len(availableFeatures) > 0:
                featureDict[pluginInfo.name] = availableFeatures
        dlg = FeatureSelectionDialog(featureDict=featureDict,
                                     selectedFeatures=selectedFeatures, ndim=ndim)
        dlg.exec_()

        if dlg.result() == QDialog.Accepted:
            mainOperator.Features.setValue(dlg.selectedFeatures)
            self._calculateFeatures()

    def _calculateFeatures(self, interactive=True):
        mainOperator = self.topLevelOperatorView
        mainOperator.ObjectCenterImage.setDirty(SubRegion(mainOperator.ObjectCenterImage))

        current_t = self.editor.posModel.time

        def _handle_all_finished(*args):
            self._lock.acquire()
            self.applet.progressSignal.emit(100)
            self.topLevelOperatorView._opRegFeats.fixed = True
            feats = self.topLevelOperatorView.RegionFeatures[0].wait()
            nfeatures = 0
            nchannels = 0

            try:
                for pname, pfeats in feats[0].iteritems():
                    if pname != 'Default features':
                        for featname, feat in pfeats.iteritems():
                            nchannels += feat.shape[1]
                            nfeatures += 1
                if interactive:
                    self._drawer.featuresSelected.setText("{} features computed, {} channels in total".format(nfeatures, nchannels))
                logger.info('Object Extraction: done.')
                success = True
            except AttributeError:
                if interactive:
                    self._drawer.featuresSelected.setText("Feature computation failed (most likely due to memory issues)")
                logger.error('Object Extraction: failed.')
                success = False

            self.applet.appletStateUpdateRequested.emit()
            self._lock.release()

        self.applet.progressSignal.emit(0)
        self.applet.progressSignal.emit(-1)

        reqs = []
        self.already_done = 0
        req = mainOperator.RegionFeatures([current_t])
        req.submit()
        req.notify_failed(self.handleFeatureComputationFailure)
        req.notify_finished(_handle_all_finished)
        reqs.append(req)

        
            

    @threadRouted
    def handleFeatureComputationFailure(self, exc, exc_info):
        msg = "Feature computation failed due to the following error:\n{}".format( exc )
        log_exception( logger, msg, exc_info )
        QMessageBox.critical(self, "Feature computation failed", msg)

    def _exportFeaturesButtonPressed(self):
        mainOperator = self.topLevelOperatorView
        if not mainOperator.RegionFeatures.ready():
            mexBox=QMessageBox()
            mexBox.setText("No features have been computed yet. Nothing to save.")
            mexBox.exec_()
            return
            
        fname = QFileDialog.getSaveFileName(self, caption='Export Computed Features', 
                                        filter="Pickled Objects (*.pkl);;All Files (*)")
        
        fname = encode_from_qstring( fname )
        if len(fname)>0: #not cancelled
            with open(fname, 'w') as f:
                pickle.dump(mainOperator.RegionFeatures(list()).wait(), f)
        
        
        logger.debug("Exported object features to file '{}'".format(fname))


from PyQt4.QtGui import QWidget
class ObjectExtractionGuiNonInteractive(QWidget):
    """
    In non-interactive mode, we don't use any object extraction gui at all.
    The ObjectExtraction applet is just used for its top-level operator and serializer. 
    This class is a stand-in for the normal gui, since the shell needs some placeholder. 
    """
    def __init__(self, *args, **kwargs):
        super( ObjectExtractionGuiNonInteractive, self ).__init__()
        self._drawer = QWidget(self)
        self._viewer_controls = QWidget(self)
    
    def centralWidget( self ):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus( self ):
        return []

    def viewerControlWidget(self):
        return self._viewer_controls

    def stopAndCleanUp(self):
        pass
