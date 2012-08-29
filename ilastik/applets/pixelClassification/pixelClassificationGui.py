# Built-in
import os
import logging
import warnings
import threading

# Third-party
import numpy
from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4.QtGui import QMessageBox

# HCI
from lazyflow.tracer import Tracer, traceLogged
from volumina.api import LazyflowSource, AlphaModulatedLayer

# ilastik
from ilastik.utility import bind
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
        self.labelingDrawerUi.checkInteractive.setChecked(False)

    ###########################################
    ###########################################

    @traceLogged(traceLogger)
    def __init__(self, pipeline, guiControlSignal, shellRequestSignal, predictionSerializer ):
        # Tell our base class which slots to monitor
        slots = LabelingGui.LabelingGuiSlots()
        slots.labelInput = pipeline.LabelInputs
        slots.labelOutput = pipeline.LabelImages
        slots.labelEraserValue = pipeline.opLabelArray.eraser
        slots.labelDelete = pipeline.opLabelArray.deleteLabel
        slots.maxLabelValue = pipeline.MaxLabelValue
        slots.labelsAllowed = pipeline.LabelsAllowedFlags
        slots.displaySlots = [ pipeline.InputImages,
                               pipeline.PredictionProbabilityChannels ]

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'
        
        # Base class init
        super(PixelClassificationGui, self).__init__( slots, labelingDrawerUiPath )
        
        self.pipeline = pipeline
        self.guiControlSignal = guiControlSignal
        self.shellRequestSignal = shellRequestSignal
        self.predictionSerializer = predictionSerializer
        
        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

        self.labelingDrawerUi.checkInteractive.setEnabled(True)
        self.labelingDrawerUi.checkInteractive.toggled.connect(self.toggleInteractive)
        self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)

        self.labelingDrawerUi.checkShowPredictions.clicked.connect(self.handleShowPredictionsClicked)
        def nextCheckState():
            if not self.labelingDrawerUi.checkShowPredictions.isChecked():
                self.labelingDrawerUi.checkShowPredictions.setChecked(True)
            else:
                self.labelingDrawerUi.checkShowPredictions.setChecked(False)
        self.labelingDrawerUi.checkShowPredictions.nextCheckState = nextCheckState
        
        self.pipeline.MaxLabelValue.notifyDirty( bind(self.handleLabelSelectionChange) )

    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(PixelClassificationGui, self).setupLayers(currentImageIndex)

        labels = self.labelListData

        # Add each of the predictions
        for channel, predictionSlot in enumerate(self.pipeline.PredictionProbabilityChannels[currentImageIndex]):
            ref_label = labels[channel]
            if predictionSlot.ready():
                predictsrc = LazyflowSource(predictionSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=ref_label.color,
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
                predictLayer.opacity = 0.25
                predictLayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()
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

        # Add the raw data last (on the bottom)
        inputDataSlot = self.pipeline.InputImages[currentImageIndex]
        if inputDataSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputDataSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)
        
        return layers

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        logger.debug("toggling interactive mode to '%r'" % checked)
        
        if checked==True:
            if len(self.pipeline.FeatureImages) == 0 \
            or self.pipeline.FeatureImages[self.imageIndex].meta.shape==None:
                self.labelingDrawerUi.checkInteractive.setChecked(False)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        self.labelingDrawerUi.savePredictionsButton.setEnabled(not checked)
        self.pipeline.FreezePredictions.setValue( not checked )

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self.labelingDrawerUi.checkShowPredictions.setChecked( True )
            self.handleShowPredictionsClicked()

        # If we're changing modes, enable/disable other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.guiControlSignal.emit( ControlCommand.DisableUpstream )
                self.guiControlSignal.emit( ControlCommand.DisableDownstream )
            else:
                self.guiControlSignal.emit( ControlCommand.Pop )                
                self.guiControlSignal.emit( ControlCommand.Pop )
        self.interactiveModeActive = checked    

    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleShowPredictionsClicked(self):
        checked = self.labelingDrawerUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked
        
        # If we're being turned off, turn off live prediction mode, too.
        if not checked and self.labelingDrawerUi.checkInteractive.isChecked():
            self.labelingDrawerUi.checkInteractive.setChecked(False)

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
            self.labelingDrawerUi.checkShowPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self.labelingDrawerUi.checkShowPredictions.setCheckState(Qt.Checked)
        else:
            self.labelingDrawerUi.checkShowPredictions.setCheckState(Qt.PartiallyChecked)

    def handleLabelSelectionChange(self):
        enabled = False
        if self.pipeline.MaxLabelValue.ready():
            enabled = True
            enabled &= self.pipeline.MaxLabelValue.value >= 2
            enabled &= numpy.prod(self.pipeline.CachedFeatureImages[self.imageIndex].meta.shape) > 0
        
        self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self.labelingDrawerUi.checkInteractive.setEnabled(enabled)
        self.labelingDrawerUi.checkShowPredictions.setEnabled(enabled)
    
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
            
            originalButtonText = "Save Predictions Now"
            self.labelingDrawerUi.savePredictionsButton.setText("Cancel Save")

            def saveThreadFunc():
                with Tracer(traceLogger):
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

            saveThread = threading.Thread(target=saveThreadFunc)
            saveThread.start()

































