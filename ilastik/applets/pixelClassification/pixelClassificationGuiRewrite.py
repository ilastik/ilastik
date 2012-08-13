# Built-in
import os
import copy
import threading
import logging

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import QRectF, Qt
from PyQt4.QtGui import *

# HCI
from lazyflow.tracer import Tracer, traceLogged
from lazyflow.operators import OpSingleChannelSelector, OpMultiArraySlicer2
from volumina.api import LazyflowSource, AlphaModulatedLayer, LayerStackModel

# ilastik
from ilastik.applets.base.applet import ShellRequest, ControlCommand
from ilastik.applets.labeling import LabelingGui

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
        labelingDrawer = super(PixelClassificationGui, self).appletDrawers()[0][1]
        return [ ("Label Marking", labelingDrawer),
                 ("Prediction", self._predictionControlUi) ]

    def reset(self):
        # Base class first
        super(PixelClassificationGui, self).reset()

        # Ensure that we are NOT in interactive mode
        logger.warn("FIX ME: Manipulate interactive checkbox correctly")
        #self._labelControlUi.checkInteractive.setChecked(False)

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

        # Base class init
        super(PixelClassificationGui, self).__init__( slots )
        
        self.pipeline = pipeline
        self.guiControlSignal = guiControlSignal
        self.shellRequestSignal = shellRequestSignal
        self.predictionSerializer = predictionSerializer

        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

        self.initPredictionControlsUic()

    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(PixelClassificationGui, self).setupLayers(currentImageIndex)

        # Add the raw data
        inputDataSlot = self.pipeline.InputImages[currentImageIndex]
        if inputDataSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputDataSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        # Add each of the predictions
        for channel, predictionSlot in enumerate(self.pipeline.PredictionProbabilityChannels[currentImageIndex]):
            if predictionSlot.ready():
                predictsrc = LazyflowSource(predictionSlot)
                logger.debug("FIX ME: Prediction colors should dynamically match label colors.")
                tintColor = self._colorTable16[channel+1]
                def setLayerColor(c):
                    predictLayer.tintColor = c
                #ref_label.colorChanged.connect(setLayerColor)

                predictLayer = AlphaModulatedLayer(predictsrc, tintColor=tintColor, normalize = None )
                predictLayer.opacity = 0.25
                predictLayer.visible = self._labelControlUi.checkInteractive.isChecked()
                
                logger.warn("FIX ME: Prediction layer names should follow label names.")
                predictLayer.name = "Prediction Channel #{}".format(channel)
                #predictLayer.nameChanged.connect(srcName)
                
#                def setLayerName(n):
#                    newName = "Prediction for %s" % ref_label.name
#                    predictLayer.name = newName
#                setLayerName(ref_label.name)
#                ref_label.nameChanged.connect(setLayerName)
                
                # Attach a new field to identify this layer so we can find it later
                #predictLayer.ref_object = ref_label
        
                #make sure that labels (index = 0) stay on top!
                #self.layerstack.insert(1, predictLayer )
                logger.warn("FIX ME: Make sure prediction layers are ABOVE input but BELOW labels.")
                layers.append(predictLayer)
        
        return layers            

    @traceLogged(traceLogger)
    def initPredictionControlsUic(self):
        # We don't know where the user is running this script from,
        #  so locate the .ui file relative to this .py file's path
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._predictionControlUi = uic.loadUi(p+"/predictionDrawer.ui") # Don't pass self: applet ui is separate from the main ui
        self._predictionControlUi.trainAndPredictButton.clicked.connect(self.onTrainAndPredictButtonClicked)

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        logger.debug("toggling interactive mode to '%r'" % checked)
        
        #Check if the number of labels in the layer stack is equals to the number of Painted labels
        if checked==True:
            nPaintedLabels = self.pipeline.MaxLabelValue.value
            if nPaintedLabels is None:
                nPaintedLabels = 0
            nLabelsLayers = self._labelControlUi.labelListModel.rowCount()
            
            if nPaintedLabels!=nLabelsLayers:
                self._labelControlUi.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("Did you forget to paint some labels?")
                mexBox.setInformativeText("Painted Labels %d \nNumber Active Labels Layers %d"%(nPaintedLabels,self._labelControlUi.labelListModel.rowCount()))
                mexBox.exec_()
                return
            if len(self.pipeline.FeatureImages) == 0 \
            or self.pipeline.FeatureImages[self.imageIndex].meta.shape==None:
                self._labelControlUi.checkInteractive.setCheckState(0)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        logger.warn("FIX ME: Can the user add/remove labels during train-and-predict?  Why not?")    
        #self._labelControlUi.AddLabelButton.setEnabled(not checked)
        #self._labelControlUi.labelListModel.allowRemove(not checked)
        
        self._predictionControlUi.trainAndPredictButton.setEnabled(not checked)
        self.pipeline.FreezePredictions.setValue( not checked )

        # Prediction layers should be switched on/off when the interactive checkbox is toggled
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

        # If we're changing modes, enable/disable other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.guiControlSignal.emit( ControlCommand.DisableUpstream )
                self.guiControlSignal.emit( ControlCommand.DisableDownstream )
            else:
                self.guiControlSignal.emit( ControlCommand.Pop )                
                self.guiControlSignal.emit( ControlCommand.Pop )
        self.interactiveModeActive = checked    
    
    @traceLogged(traceLogger)
    def onTrainAndPredictButtonClicked(self):
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
            
            originalButtonText = "Save Predictions"
            self._predictionControlUi.trainAndPredictButton.setText("Cancel Save")

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
                    self.thunkEventHandler.post(self._predictionControlUi.trainAndPredictButton.setText, originalButtonText)
                    self.pipeline.FreezePredictions.setValue(predictionsFrozen)
                    self._currentlySavingPredictions = False

            saveThread = threading.Thread(target=saveThreadFunc)
            saveThread.start()

































