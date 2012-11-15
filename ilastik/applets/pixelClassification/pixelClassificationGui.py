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
from lazyflow.tracer import Tracer, traceLogged
from volumina.api import LazyflowSource, AlphaModulatedLayer
from volumina.utility import ShortcutManager

# ilastik
from ilastik.utility import bind
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.labeling import LabelingGui
from ilastik.applets.base.applet import ShellRequest, ControlCommand

# Loggers
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class PixelClassificationGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self

    def appletDrawers(self):
        # Get the labeling drawer from the base class
        labelingDrawer = super(PixelClassificationGui, self).appletDrawers()[0][1]
        return [ ("Training", labelingDrawer) ]

    def reset(self):
        # Base class first
        super(PixelClassificationGui, self).reset()

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
    def __init__(self, pipeline, shellRequestSignal, guiControlSignal, predictionSerializer ):
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = pipeline.LabelInputs
        labelSlots.labelOutput = pipeline.LabelImages
        labelSlots.labelEraserValue = pipeline.opLabelArray.eraser
        labelSlots.labelDelete = pipeline.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = pipeline.MaxLabelValue
        labelSlots.labelsAllowed = pipeline.LabelsAllowedFlags

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'
        
        # Base class init
        super(PixelClassificationGui, self).__init__( labelSlots, pipeline, labelingDrawerUiPath )
        
        self.pipeline = pipeline
        self.shellRequestSignal = shellRequestSignal
        self.guiControlSignal = guiControlSignal
        self.predictionSerializer = predictionSerializer
        
        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

        self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)
        self.labelingDrawerUi.savePredictionsButton.setIcon( QIcon(ilastikIcons.Save) )

        self.pipeline.MaxLabelValue.notifyDirty( bind(self.handleLabelSelectionChange) )
        
        self._initShortcuts()
        
    @traceLogged(traceLogger)
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

        toggleLivePredict = QShortcut( QKeySequence("l"), self, member=self._viewerControlUi.liveUpdateButton.toggle )
        mgr.register( shortcutGroupName,
                      "Toggle Live Prediction Mode",
                      toggleLivePredict,
                      self._viewerControlUi.liveUpdateButton )

    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(PixelClassificationGui, self).setupLayers(currentImageIndex)

        labels = self.labelListData

        # Add the uncertainty estimate layer
        uncertaintySlot = self.pipeline.UncertaintyEstimate[currentImageIndex]
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

        # Add each of the predictions
        for channel, predictionSlot in enumerate(self.pipeline.PredictionProbabilityChannels[currentImageIndex]):
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
                    newName = "Prediction for %s" % ref_label.name
                    predictLayer.name = newName
                setLayerName(ref_label.name)

                ref_label.colorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setLayerName)
                layers.append(predictLayer)

        # Add each of the segementations
        for channel, segmentationSlot in enumerate(self.pipeline.SegmentationChannels[currentImageIndex]):
            if segmentationSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                segsrc = LazyflowSource(segmentationSlot)
                segLayer = AlphaModulatedLayer( segsrc,
                                                tintColor=ref_label.color,
                                                range=(0.0, 1.0),
                                                normalize=(0.0, 1.0) )
                segLayer.opacity = 1
                segLayer.visible = self._viewerControlUi.liveUpdateButton.isChecked()
                segLayer.visibleChanged.connect(self.updateShowSegmentationCheckbox)

                def setLayerColor(c):
                    segLayer.tintColor = c
                def setLayerName(n):
                    newName = "Segmentation (%s)" % ref_label.name
                    segLayer.name = newName
                setLayerName(ref_label.name)

                ref_label.colorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setLayerName)
                layers.append(segLayer)

        # Add the raw data last (on the bottom)
        inputDataSlot = self.pipeline.InputImages[currentImageIndex]
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
        
        return layers

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        """
        If enable
        """
        logger.debug("toggling interactive mode to '%r'" % checked)
        
        if checked==True:
            if len(self.pipeline.FeatureImages) == 0 \
            or self.pipeline.FeatureImages[self.imageIndex].meta.shape==None:
                self._viewerControlUi.liveUpdateButton.setChecked(False)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        self.labelingDrawerUi.savePredictionsButton.setEnabled(not checked)
        self.pipeline.FreezePredictions.setValue( not checked )

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
        if self.pipeline.MaxLabelValue.ready():
            enabled = True
            enabled &= self.pipeline.MaxLabelValue.value >= 2
            enabled &= numpy.prod(self.pipeline.CachedFeatureImages[self.imageIndex].meta.shape) > 0
        
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
        Handle this event by asking the pipeline for a prediction over the entire output region.
        """
        # The button does double-duty as a cancel button while predictions are being stored
        if self._currentlySavingPredictions:
            self.predictionSerializer.cancel()
        else:
            # Compute new predictions as needed
            predictionsFrozen = self.pipeline.FreezePredictions.value
            self.pipeline.FreezePredictions.setValue(False)
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
                self.pipeline.FreezePredictions.setValue(predictionsFrozen)
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

































