# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

# Built-in
import os
import logging
from functools import partial

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4.QtGui import QMessageBox, QColor, QShortcut, QKeySequence, QIcon

# HCI
from volumina.api import LazyflowSource, AlphaModulatedLayer
from volumina.utility import ShortcutManager

# ilastik
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.labeling.labelingGui import LabelingGui

try:
    from volumina.view3d.volumeRendering import RenderingManager
except:
    pass

# Loggers
logger = logging.getLogger(__name__)

def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new):]
    else:
        return new

class PixelClassificationGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self

    def stopAndCleanUp(self):
        for fn in self.__cleanup_fns:
            fn()

        # Base class
        super(PixelClassificationGui, self).stopAndCleanUp()

    def viewerControlWidget(self):
        return self._viewerControlUi

    ###########################################
    ###########################################

    def __init__(self, parentApplet, topLevelOperatorView ):
        self.parentApplet = parentApplet
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = topLevelOperatorView.LabelInputs
        labelSlots.labelOutput = topLevelOperatorView.LabelImages
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelPipeline.DeleteLabel
        labelSlots.labelNames = topLevelOperatorView.LabelNames
        labelSlots.labelsAllowed = topLevelOperatorView.LabelsAllowedFlags

        self.__cleanup_fns = []

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'

        # Base class init
        super(PixelClassificationGui, self).__init__( parentApplet, labelSlots, topLevelOperatorView, labelingDrawerUiPath )
        
        self.topLevelOperatorView = topLevelOperatorView

        self.interactiveModeActive = False
        # Immediately update our interactive state
        self.toggleInteractive( not self.topLevelOperatorView.FreezePredictions.value )

        self._currentlySavingPredictions = False

        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon( QIcon(ilastikIcons.Play) )
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect( self.toggleInteractive )

        self.topLevelOperatorView.LabelNames.notifyDirty( bind(self.handleLabelSelectionChange) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.LabelNames.unregisterDirty, bind(self.handleLabelSelectionChange) ) )
        
        self._initShortcuts()

        try:
            self.render = True
            self._renderedLayers = {} # (layer name, label number)
            self._renderMgr = RenderingManager(
                renderer=self.editor.view3d.qvtk.renderer,
                qvtk=self.editor.view3d.qvtk)
        except:
            self.render = False

        # toggle interactive mode according to freezePredictions.value
        self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)
        def FreezePredDirty():
            self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)
        # listen to freezePrediction changes
        self.topLevelOperatorView.FreezePredictions.notifyDirty( bind(FreezePredDirty) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.FreezePredictions.unregisterDirty, bind(FreezePredDirty) ) )

    def initViewerControlUi(self):
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi( os.path.join( localDir, "viewerControls.ui" ) )

        # Connect checkboxes
        def nextCheckState(checkbox):
            checkbox.setChecked( not checkbox.isChecked() )
        self._viewerControlUi.checkShowPredictions.nextCheckState = partial(nextCheckState, self._viewerControlUi.checkShowPredictions)
        self._viewerControlUi.checkShowSegmentation.nextCheckState = partial(nextCheckState, self._viewerControlUi.checkShowSegmentation)

        self._viewerControlUi.checkShowPredictions.clicked.connect( self.handleShowPredictionsClicked )
        self._viewerControlUi.checkShowSegmentation.clicked.connect( self.handleShowSegmentationClicked )

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        self._viewerControlUi.viewerControls.setupConnections(model)
       
    def _initShortcuts(self):
        mgr = ShortcutManager()
        shortcutGroupName = "Predictions"

        togglePredictions = QShortcut( QKeySequence("p"), self, member=self._viewerControlUi.checkShowPredictions.click )
        mgr.register( shortcutGroupName,
                      "Toggle Prediction Layer Visibility",
                      togglePredictions,
                      self._viewerControlUi.checkShowPredictions )

        toggleSegmentation = QShortcut( QKeySequence("s"), self, member=self._viewerControlUi.checkShowSegmentation.click )
        mgr.register( shortcutGroupName,
                      "Toggle Segmentaton Layer Visibility",
                      toggleSegmentation,
                      self._viewerControlUi.checkShowSegmentation )

        toggleLivePredict = QShortcut( QKeySequence("l"), self, member=self.labelingDrawerUi.liveUpdateButton.toggle )
        mgr.register( shortcutGroupName,
                      "Toggle Live Prediction Mode",
                      toggleLivePredict,
                      self.labelingDrawerUi.liveUpdateButton )

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
            layer.contexts.append(('Toggle 3D rendering', callback))

    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(PixelClassificationGui, self).setupLayers()

        # Add the uncertainty estimate layer
        uncertaintySlot = self.topLevelOperatorView.UncertaintyEstimate
        if uncertaintySlot.ready():
            uncertaintySrc = LazyflowSource(uncertaintySlot)
            uncertaintyLayer = AlphaModulatedLayer( uncertaintySrc,
                                                    tintColor=QColor( Qt.cyan ),
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
            uncertaintyLayer.name = "Uncertainty"
            uncertaintyLayer.visible = False
            uncertaintyLayer.opacity = 1.0
            uncertaintyLayer.shortcutRegistration = (
                "Prediction Layers",
                "Show/Hide Uncertainty",
                QShortcut( QKeySequence("u"), self.viewerControlWidget(), uncertaintyLayer.toggleVisible ),
                uncertaintyLayer )
            layers.append(uncertaintyLayer)

        labels = self.labelListData

        # Add each of the segmentations
        for channel, segmentationSlot in enumerate(self.topLevelOperatorView.SegmentationChannels):
            if segmentationSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                segsrc = LazyflowSource(segmentationSlot)
                segLayer = AlphaModulatedLayer( segsrc,
                                                tintColor=ref_label.pmapColor(),
                                                range=(0.0, 1.0),
                                                normalize=(0.0, 1.0) )

                segLayer.opacity = 1
                segLayer.visible = False #self.labelingDrawerUi.liveUpdateButton.isChecked()
                segLayer.visibleChanged.connect(self.updateShowSegmentationCheckbox)

                def setLayerColor(c, segLayer=segLayer):
                    segLayer.tintColor = c
                    self._update_rendering()

                def setSegLayerName(n, segLayer=segLayer):
                    oldname = segLayer.name
                    newName = "Segmentation (%s)" % n
                    segLayer.name = newName
                    if not self.render:
                        return
                    if oldname in self._renderedLayers:
                        label = self._renderedLayers.pop(oldname)
                        self._renderedLayers[newName] = label

                setSegLayerName(ref_label.name)

                ref_label.pmapColorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setSegLayerName)
                #check if layer is 3d before adding the "Toggle 3D" option
                #this check is done this way to match the VolumeRenderer, in
                #case different 3d-axistags should be rendered like t-x-y
                #_axiskeys = segmentationSlot.meta.getAxisKeys()
                if len(segmentationSlot.meta.shape) == 4:
                    #the Renderer will cut out the last shape-dimension, so
                    #we're checking for 4 dimensions
                    self._setup_contexts(segLayer)
                layers.append(segLayer)
        
        # Add each of the predictions
        for channel, predictionSlot in enumerate(self.topLevelOperatorView.PredictionProbabilityChannels):
            if predictionSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                predictsrc = LazyflowSource(predictionSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=ref_label.pmapColor(),
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
                predictLayer.opacity = 0.25
                predictLayer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                predictLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                def setLayerColor(c, predictLayer=predictLayer):
                    predictLayer.tintColor = c

                def setPredLayerName(n, predictLayer=predictLayer):
                    newName = "Prediction for %s" % n
                    predictLayer.name = newName

                setPredLayerName(ref_label.name)
                ref_label.pmapColorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setPredLayerName)
                layers.append(predictLayer)

        # Add the raw data last (on the bottom)
        inputDataSlot = self.topLevelOperatorView.InputImages
        if inputDataSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputDataSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0

            def toggleTopToBottom():
                index = self.layerstack.layerIndex( inputLayer )
                self.layerstack.selectRow( index )
                if index == 0:
                    self.layerstack.moveSelectedToBottom()
                else:
                    self.layerstack.moveSelectedToTop()

            inputLayer.shortcutRegistration = (
                "Prediction Layers",
                "Bring Input To Top/Bottom",
                QShortcut( QKeySequence("i"), self.viewerControlWidget(), toggleTopToBottom),
                inputLayer )
            layers.append(inputLayer)
        
        self.handleLabelSelectionChange()
        return layers

    def toggleInteractive(self, checked):
        logger.debug("toggling interactive mode to '%r'" % checked)

        if checked==True:
            if not self.topLevelOperatorView.FeatureImages.ready() \
            or self.topLevelOperatorView.FeatureImages.meta.shape==None:
                self.labelingDrawerUi.liveUpdateButton.setChecked(False)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        # If we're changing modes, enable/disable our controls and other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.labelingDrawerUi.labelListView.allowDelete = False
                self.labelingDrawerUi.AddLabelButton.setEnabled( False )
            else:
                self.labelingDrawerUi.labelListView.allowDelete = True
                self.labelingDrawerUi.AddLabelButton.setEnabled( True )
        self.interactiveModeActive = checked

        self.topLevelOperatorView.FreezePredictions.setValue( not checked )
        self.labelingDrawerUi.liveUpdateButton.setChecked(checked)
        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self._viewerControlUi.checkShowPredictions.setChecked( True )
            self.handleShowPredictionsClicked()

        # Notify the workflow that some applets may have changed state now.
        # (For example, the downstream pixel classification applet can 
        #  be used now that there are features selected)
        self.parentApplet.appletStateUpdateRequested.emit()

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
        new = map(mapf, self.labelListData)
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

    def getNextLabelName(self):
        return self._getNext(self.topLevelOperatorView.LabelNames,
                             super(PixelClassificationGui, self).getNextLabelName)

    def getNextLabelColor(self):
        return self._getNext(
            self.topLevelOperatorView.LabelColors,
            super(PixelClassificationGui, self).getNextLabelColor,
            lambda x: QColor(*x)
        )

    def getNextPmapColor(self):
        return self._getNext(
            self.topLevelOperatorView.PmapColors,
            super(PixelClassificationGui, self).getNextPmapColor,
            lambda x: QColor(*x)
        )

    def onLabelNameChanged(self):
        self._onLabelChanged(super(PixelClassificationGui, self).onLabelNameChanged,
                             lambda l: l.name,
                             self.topLevelOperatorView.LabelNames)

    def onLabelColorChanged(self):
        self._onLabelChanged(super(PixelClassificationGui, self).onLabelColorChanged,
                             lambda l: (l.brushColor().red(),
                                        l.brushColor().green(),
                                        l.brushColor().blue()),
                             self.topLevelOperatorView.LabelColors)


    def onPmapColorChanged(self):
        self._onLabelChanged(super(PixelClassificationGui, self).onPmapColorChanged,
                             lambda l: (l.pmapColor().red(),
                                        l.pmapColor().green(),
                                        l.pmapColor().blue()),
                             self.topLevelOperatorView.PmapColors)

    def _update_rendering(self):
        if not self.render:
            return
        shape = self.topLevelOperatorView.InputImages.meta.shape[1:4]
        if len(shape) != 5:
            #this might be a 2D image, no need for updating any 3D stuff 
            return
        
        time = self.editor.posModel.slicingPos5D[0]
        if not self._renderMgr.ready:
            self._renderMgr.setup(shape)

        layernames = set(layer.name for layer in self.layerstack)
        self._renderedLayers = dict((k, v) for k, v in self._renderedLayers.iteritems()
                                if k in layernames)

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
            color = (color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0)
            self._renderMgr.setColor(label, color)
