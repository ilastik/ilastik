# Built-in
import os
import logging
import warnings
import threading
from functools import partial

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4.QtGui import QMessageBox, QColor, QShortcut, QKeySequence, QPushButton, QWidget, QIcon

# HCI
from lazyflow.utility import Tracer, traceLogged
from volumina.api import LazyflowSource, AlphaModulatedLayer
from volumina.utility import ShortcutManager

# ilastik
from ilastik.utility import bind
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.labeling import LabelingGui
from ilastik.applets.base.applet import ShellRequest, ControlCommand

try:
    from volumina.view3d.volumeRendering import RenderingManager
except:
    pass

# Loggers
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class AutocontextClassificationGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget( self ):
        return self

    def reset(self):
        # Base class first
        super(AutocontextClassificationGui, self).reset()

        # Ensure that we are NOT in interactive mode
        self._viewerControlUi.liveUpdateButton.setChecked(False)
        self._viewerControlUi.checkShowPredictions.setChecked(False)
        self._viewerControlUi.checkShowSegmentation.setChecked(False)
        self.toggleInteractive(False)

    def viewerControlWidget(self):
        return self._viewerControlUi

    ###########################################
    ###########################################

    @traceLogged(traceLogger)
    def __init__(self, topLevelOperatorView, shellRequestSignal, guiControlSignal, predictionSerializer ):
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = topLevelOperatorView.LabelInputs
        labelSlots.labelOutput = topLevelOperatorView.LabelImages
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = topLevelOperatorView.MaxLabelValue
        labelSlots.labelsAllowed = topLevelOperatorView.LabelsAllowedFlags

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'

        # Base class init
        super(AutocontextClassificationGui, self).__init__( labelSlots, topLevelOperatorView, labelingDrawerUiPath )
        
        self.topLevelOperatorView = topLevelOperatorView
        self.shellRequestSignal = shellRequestSignal
        self.guiControlSignal = guiControlSignal
        self.predictionSerializer = predictionSerializer

        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

        self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)
        self.labelingDrawerUi.savePredictionsButton.setIcon( QIcon(ilastikIcons.Save) )

        self.topLevelOperatorView.MaxLabelValue.notifyDirty( bind(self.handleLabelSelectionChange) )
        
#        self._initShortcuts()
#
#        try:
#            self.render = True
#            self._renderedLayers = {} # (layer name, label number)
#            self._renderMgr = RenderingManager(
#                renderer=self.editor.view3d.qvtk.renderer,
#                qvtk=self.editor.view3d.qvtk)
#        except:
#            self.render = False

    @traceLogged(traceLogger)
    def initViewerControlUi(self):
        """
        This overrides the base class: LayerViewerGui.initViewerControlUi()
        """
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi( os.path.join( localDir, "viewerControls.ui" ) )

        # Connect checkboxes
        def nextCheckState(checkbox):
            checkbox.setChecked( not checkbox.isChecked() )
        self._viewerControlUi.checkShowPredictions.nextCheckState = partial(nextCheckState, self._viewerControlUi.checkShowPredictions)
        self._viewerControlUi.checkShowSegmentation.nextCheckState = partial(nextCheckState, self._viewerControlUi.checkShowSegmentation)

        self._viewerControlUi.checkShowPredictions.clicked.connect( self.handleShowPredictionsClicked )
        self._viewerControlUi.checkShowSegmentation.clicked.connect( self.handleShowSegmentationClicked )

        self._viewerControlUi.liveUpdateButton.setEnabled(True)
        self._viewerControlUi.liveUpdateButton.setIcon( QIcon(ilastikIcons.Play) )
        self._viewerControlUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._viewerControlUi.liveUpdateButton.toggled.connect( self.toggleInteractive )

        self._viewerControlUi.pauseUpdateButton.setEnabled(True)
        self._viewerControlUi.pauseUpdateButton.setIcon( QIcon(ilastikIcons.Pause) )
        self._viewerControlUi.pauseUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        model.canMoveSelectedUp.connect(self._viewerControlUi.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self._viewerControlUi.DownButton.setEnabled)
        model.canDeleteSelected.connect(self._viewerControlUi.DeleteButton.setEnabled)

        # Connect our layer movement buttons to the appropriate layerstack actions
        self._viewerControlUi.layerWidget.init(model)
        self._viewerControlUi.UpButton.clicked.connect(model.moveSelectedUp)
        self._viewerControlUi.DownButton.clicked.connect(model.moveSelectedDown)
        self._viewerControlUi.DeleteButton.clicked.connect(model.deleteSelected)

    @traceLogged(traceLogger)
    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(AutocontextClassificationGui, self).setupLayers()
        
        pixel_pred_layers = self.setupPredictionLayers(self.topLevelOperatorView.PixelOnlyPredictionChannels, "")
        layers.extend(pixel_pred_layers)
        pred_layers = self.setupPredictionLayers(self.topLevelOperatorView.PredictionProbabilityChannels, "auto")
        layers.extend(pred_layers)


        # Add the raw data last (on the bottom)
        inputDataSlot = self.topLevelOperatorView.InputImages
        if inputDataSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputDataSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)
        
        return layers
    
    @traceLogged(traceLogger)
    def setupPredictionLayers(self, predictionChannels, name_suffix):
        """
        Setup the layers for predicted class probabilities
        """
        
        labels = self.labelListData
        layers = []
        # Add each of the predictions
        for channel, predictionSlot in enumerate(predictionChannels):
            if predictionSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                predictsrc = LazyflowSource(predictionSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=ref_label.color,
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
                predictLayer.opacity = 0.25
                predictLayer.visible = self._viewerControlUi.liveUpdateButton.isChecked()
                predictLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                def setLayerColor(c):
                    predictLayer.tintColor = c
                def setLayerName(n):
                    newName = "Prediction for %s %s" % (ref_label.name, name_suffix)
                    predictLayer.name = newName
                setLayerName(ref_label.name)

                ref_label.colorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setLayerName)
                layers.append(predictLayer)
        return layers

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        """
        If enable
        """
        logger.debug("toggling interactive mode to '%r'" % checked)

        if checked==True:
            if not self.topLevelOperatorView.FeatureImages.ready() \
            or self.topLevelOperatorView.FeatureImages.meta.shape==None:
                self._viewerControlUi.liveUpdateButton.setChecked(False)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        self.labelingDrawerUi.savePredictionsButton.setEnabled(not checked)
        self.topLevelOperatorView.FreezePredictions.setValue( not checked )

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self._viewerControlUi.checkShowPredictions.setChecked( True )
            self.handleShowPredictionsClicked()

        # If we're changing modes, enable/disable our controls and other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.labelingDrawerUi.labelListView.allowDelete = False
                self.labelingDrawerUi.AddLabelButton.setEnabled( False )
            else:
                self.labelingDrawerUi.labelListView.allowDelete = True
                self.labelingDrawerUi.AddLabelButton.setEnabled( True )
        self.interactiveModeActive = checked

    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

        # If we're being turned off, turn off live prediction mode, too.
        if not checked and self._viewerControlUi.liveUpdateButton.isChecked():
            self._viewerControlUi.liveUpdateButton.setChecked(False)
            # And hide all segmentation layers
            for layer in self.layerstack:
                if "Segmentation" in layer.name:
                    layer.visible = False

    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleShowSegmentationClicked(self):
        checked = self._viewerControlUi.checkShowSegmentation.isChecked()
        for layer in self.layerstack:
            if "Segmentation" in layer.name:
                layer.visible = checked

    @pyqtSlot()
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

    @pyqtSlot()
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

    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleLabelSelectionChange(self):
        enabled = False
        if self.topLevelOperatorView.MaxLabelValue.ready():
            enabled = True
            enabled &= self.topLevelOperatorView.MaxLabelValue.value >= 2
            enabled &= numpy.prod(self.topLevelOperatorView.CachedFeatureImages.meta.shape) > 0
        
        self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self._viewerControlUi.liveUpdateButton.setEnabled(enabled)
        self._viewerControlUi.pauseUpdateButton.setEnabled(enabled)
        self._viewerControlUi.checkShowPredictions.setEnabled(enabled)
        self._viewerControlUi.checkShowSegmentation.setEnabled(enabled)

    @pyqtSlot()
    @traceLogged(traceLogger)
    def onSavePredictionsButtonClicked(self):
        """
        The user clicked "Train and Predict".
        Handle this event by asking the topLevelOperatorView for a prediction over the entire output region.
        """
        # The button does double-duty as a cancel button while predictions are being stored
        if self._currentlySavingPredictions:
            self.predictionSerializer.cancel()
        else:
            # Compute new predictions as needed
            predictionsFrozen = self.topLevelOperatorView.FreezePredictions.value
            self.topLevelOperatorView.FreezePredictions.setValue(False)
            self._currentlySavingPredictions = True

            originalButtonText = "Full Volume Predict and Save"
            self.labelingDrawerUi.savePredictionsButton.setText("Cancel Full Predict")

            @traceLogged(traceLogger)
            def saveThreadFunc():
                # Disable all other applets
                self.guiControlSignal.emit( ControlCommand.DisableUpstream )
                self.guiControlSignal.emit( ControlCommand.DisableDownstream )

                def disableAllInWidgetButName(widget, exceptName):
                    for child in widget.children():
                        if child.findChild( QPushButton, exceptName) is None:
                            child.setEnabled(False)
                        else:
                            disableAllInWidgetButName(child, exceptName)

                # Disable everything in our drawer *except* the cancel button
                disableAllInWidgetButName(self.labelingDrawerUi, "savePredictionsButton")

                # But allow the user to cancel the save
                self.labelingDrawerUi.savePredictionsButton.setEnabled(True)

                # First, do a regular save.
                # During a regular save, predictions are not saved to the project file.
                # (It takes too much time if the user only needs the classifier.)
                self.shellRequestSignal.emit( ShellRequest.RequestSave )

                # Enable prediction storage and ask the shell to save the project again.
                # (This way the second save will occupy the whole progress bar.)
                self.predictionSerializer.predictionStorageEnabled = True
                self.shellRequestSignal.emit( ShellRequest.RequestSave )
                self.predictionSerializer.predictionStorageEnabled = False

                # Restore original states (must use events for UI calls)
                self.thunkEventHandler.post(self.labelingDrawerUi.savePredictionsButton.setText, originalButtonText)
                self.topLevelOperatorView.FreezePredictions.setValue(predictionsFrozen)
                self._currentlySavingPredictions = False

                # Re-enable our controls
                def enableAll(widget):
                    for child in widget.children():
                        if isinstance( child, QWidget ):
                            child.setEnabled(True)
                            enableAll(child)
                enableAll(self.labelingDrawerUi)

                # Re-enable all other applets
                self.guiControlSignal.emit( ControlCommand.Pop )
                self.guiControlSignal.emit( ControlCommand.Pop )

            saveThread = threading.Thread(target=saveThreadFunc)
            saveThread.start()

    def getNextLabelName(self):
        numLabels = self.labelListData.rowCount()
        labelNames = self.topLevelOperatorView.LabelNames.value
        if numLabels < len(labelNames):
            return labelNames[numLabels]
        else:
            return super( AutocontextClassificationGui, self ).getNextLabelName()

    def onLabelNameChanged(self):
        super( AutocontextClassificationGui, self ).onLabelNameChanged()
        labelNames = map( lambda l: l.name, self.labelListData )
        self.topLevelOperatorView.LabelNames.setValue( labelNames )

    def getNextLabelColor(self):
        numLabels = self.labelListData.rowCount()
        labelColors = self.topLevelOperatorView.LabelColors.value
        if numLabels < len(labelColors):
            return QColor( *labelColors[numLabels] )
        else:
            return super( AutocontextClassificationGui, self ).getNextLabelColor()

    def onLabelColorChanged(self):
        super( AutocontextClassificationGui, self ).onLabelColorChanged()
        labelColors = map( lambda l: (l.color.red(), l.color.green(), l.color.blue()), self.labelListData )
        self.topLevelOperatorView.LabelColors.setValue( labelColors )

    def _update_rendering(self):
        if not self.render:
            return
        shape = self.topLevelOperatorView.InputImages.meta.shape[1:4]
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
