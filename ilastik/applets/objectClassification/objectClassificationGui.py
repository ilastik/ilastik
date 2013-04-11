from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot

from ilastik.widgets.featureTableWidget import FeatureEntry
from ilastik.widgets.featureDlg import FeatureDlg
from ilastik.applets.objectExtraction.opObjectExtraction import OpRegionFeatures3d

import os
import numpy
from ilastik.utility import bind
from lazyflow.operators import OpSubRegion

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.applets.labeling import LabelingGui

import volumina.colortables as colortables
from volumina.api import \
    LazyflowSource, GrayscaleLayer, ColortableLayer, AlphaModulatedLayer, \
    ClickableColortableLayer, LazyflowSinkSource

from volumina.interpreter import ClickInterpreter

class ObjectClassificationGui(LabelingGui):

    def centralWidget(self):
        return self

    def appletDrawers(self):
        # Get the labeling drawer from the base class
        labelingDrawer = super(ObjectClassificationGui, self).appletDrawers()[0][1]
        return [("Training", labelingDrawer)]

    def reset(self):
        # Base class first
        super(ObjectClassificationGui, self).reset()

        # Ensure that we are NOT in interactive mode
        self.labelingDrawerUi.checkInteractive.setChecked(False)
        self.labelingDrawerUi.checkShowPredictions.setChecked(False)

    def __init__(self, op, shellRequestSignal, guiControlSignal):
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = op.LabelInputs
        labelSlots.labelOutput = op.LabelImages

        labelSlots.labelEraserValue = op.Eraser
        labelSlots.labelDelete = op.DeleteLabel

        labelSlots.maxLabelValue = op.NumLabels
        labelSlots.labelsAllowed = op.LabelsAllowedFlags

        # We provide our own UI file (which adds an extra control for
        # interactive mode) This UI file is copied from
        # pixelClassification pipeline
        #
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'

        # Base class init
        super(ObjectClassificationGui, self).__init__(labelSlots, op,
                                                      labelingDrawerUiPath,
                                                      crosshair=False)

        self.op = op
        self.guiControlSignal = guiControlSignal
        self.shellRequestSignal = shellRequestSignal

        self.interactiveModeActive = False

        self.labelingDrawerUi.checkInteractive.setEnabled(True)
        self.labelingDrawerUi.checkInteractive.toggled.connect(
            self.toggleInteractive)
        self.labelingDrawerUi.checkShowPredictions.setEnabled(True)
        self.labelingDrawerUi.checkShowPredictions.toggled.connect(
            self.handleShowPredictionsClicked)

        self.labelingDrawerUi.savePredictionsButton.setEnabled(False)
        self.labelingDrawerUi.savePredictionsButton.setVisible(False)

        self.labelingDrawerUi.brushSizeComboBox.setEnabled(False)
        self.labelingDrawerUi.brushSizeComboBox.setVisible(False)


        self.op.NumLabels.notifyDirty(bind(self.handleLabelSelectionChange))

    def initAppletDrawerUi(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]

        # We don't pass self here because we keep the drawer ui in a
        # separate object.
        self.drawer = uic.loadUi(localDir+"/drawer.ui")

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
            labelsrc = LazyflowSinkSource(labelOutput,
                                          labelInput)
            labellayer = ColortableLayer(labelsrc,
                                         colorTable=self._colorTable16,
                                         direct=direct)

            labellayer.segmentationImageSlot = self.op.SegmentationImagesOut
            labellayer.name = "Labels"
            labellayer.ref_object = None
            labellayer.zeroIsTransparent  = False
            labellayer.colortableIsRandom = True

            clickInt = ClickInterpreter(self.editor, labellayer,
                                        self.onClick, right=False,
                                        double=False)
            self.editor.brushingInterpreter = clickInt

            return labellayer, labelsrc

    def setupLayers(self):

        # Base class provides the label layer.
        layers = super(ObjectClassificationGui, self).setupLayers()

        labelOutput = self._labelingSlots.labelOutput
        binarySlot = self.op.BinaryImages
        segmentedSlot = self.op.SegmentationImages
        rawSlot = self.op.RawImages

        if segmentedSlot.ready():
            ct = colortables.create_default_16bit()
            self.objectssrc = LazyflowSource(segmentedSlot)
            ct[0] = QColor(0, 0, 0, 0).rgba() # make 0 transparent
            layer = ColortableLayer(self.objectssrc, ct)
            layer.name = "Objects"
            layer.opacity = 0.5
            layer.visible = True
            layers.append(layer)

        if binarySlot.ready():
            ct_binary = [QColor(0, 0, 0, 0).rgba(),
                         QColor(255, 255, 255, 255).rgba()]
            self.binaryimagesrc = LazyflowSource(binarySlot)
            layer = ColortableLayer(self.binaryimagesrc, ct_binary)
            layer.name = "Binary Image"
            layer.visible = False
            layers.append(layer)

        #This is just for colors
        labels = self.labelListData
        for channel, probSlot in enumerate(self.op.PredictionProbabilityChannels):
            if probSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                probsrc = LazyflowSource(probSlot)
                probLayer = AlphaModulatedLayer( probsrc,
                                                 tintColor=ref_label.pmapColor(),
                                                 range=(0.0, 1.0),
                                                 normalize=(0.0, 1.0) )
                probLayer.opacity = 0.25
                probLayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()

                def setLayerColor(c, predictLayer=probLayer):
                    predictLayer.tintColor = c

                def setLayerName(n, predictLayer=probLayer):
                    newName = "Prediction for %s" % n
                    predictLayer.name = newName

                setLayerName(ref_label.name)
                ref_label.pmapColorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setLayerName)
                layers.insert(0, probLayer)

        predictionSlot = self.op.PredictionImages
        if predictionSlot.ready():
            self.predictsrc = LazyflowSource(predictionSlot)
            self.predictlayer = ColortableLayer(self.predictsrc,
                                                colorTable=self._colorTable16)
            self.predictlayer.name = "Prediction"
            self.predictlayer.ref_object = None
            self.predictlayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()

            # put first, so that it is visible after hitting "live
            # predict".
            layers.insert(0, self.predictlayer)
        if rawSlot.ready():
            self.rawimagesrc = LazyflowSource(rawSlot)
            layer = self.createStandardLayerFromSlot(rawSlot)
            layer.name = "Raw data"
            layers.append(layer)

        # since we start with existing labels, it makes sense to start
        # with the first one selected. This would make more sense in
        # __init__(), but it does not take effect there.
        self.selectLabel(0)

        return layers

    @pyqtSlot()
    def handleLabelSelectionChange(self):
        enabled = False
        if self.op.NumLabels.ready():
            enabled = True
            enabled &= self.op.NumLabels.value >= 2

        self.labelingDrawerUi.checkInteractive.setEnabled(enabled)
        self.labelingDrawerUi.checkShowPredictions.setEnabled(enabled)

    def toggleInteractive(self, checked):
        logger.debug("toggling interactive mode to '%r'" % checked)

        # Auto-set the "show predictions" state according to what the
        # user just clicked.
        if checked:
            self.labelingDrawerUi.checkShowPredictions.setChecked(True)
            self.handleShowPredictionsClicked()

        # If we're changing modes, enable/disable our controls and
        # other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.labelingDrawerUi.labelListView.allowDelete = False
                self.labelingDrawerUi.AddLabelButton.setEnabled(False)
            else:
                self.labelingDrawerUi.labelListView.allowDelete = True
                self.labelingDrawerUi.AddLabelButton.setEnabled(True)
        self.interactiveModeActive = checked

    @pyqtSlot()
    def handleShowPredictionsClicked(self):
        checked = self.labelingDrawerUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

        # If we're being turned off, turn off live prediction mode, too.
        if not checked and self.labelingDrawerUi.checkInteractive.isChecked():
            self.labelingDrawerUi.checkInteractive.setChecked(False)
            # And hide all segmentation layers
            for layer in self.layerstack:
                if "Segmentation" in layer.name:
                    layer.visible = False

    @staticmethod
    def _getObject(slot, pos5d):
        slicing = tuple(slice(i, i+1) for i in pos5d)
        arr = slot[slicing].wait()
        return arr.flat[0]

    def onClick(self, layer, pos5d, pos):
        """Extracts the object index that was clicked on and updates
        that object's label.

        """
        label = self.editor.brushingModel.drawnNumber
        if label == self.editor.brushingModel.erasingNumber:
            label = 0

        topLevelOp = self.topLevelOperatorView.viewed_operator()
        imageIndex = topLevelOp.LabelInputs.index( self.topLevelOperatorView.LabelInputs )

        operatorAxisOrder = self.topLevelOperatorView.SegmentationImagesOut.meta.getAxisKeys()
        assert operatorAxisOrder == list('txyzc'), \
            "Need to update onClick() if the operator no longer expects volumnia axis order.  Operator wants: {}".format( operatorAxisOrder )
        self.topLevelOperatorView.assignObjectLabel(imageIndex, pos5d, label)


    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        layer = self.getLayer('Labels')
        obj = self._getObject(layer.segmentationImageSlot, position5d)
        if obj == 0:
            return

        menu = QMenu(self)
        text = "print info for object {}".format(obj)
        menu.addAction(text)
        action = menu.exec_(globalWindowCoordinate)
        if action is not None and action.text() == text:
            t = position5d[0]
            labels = self.op.LabelInputs([t]).wait()[t]
            if len(labels) > obj:
                label = int(labels[obj])
            else:
                label = "none"

            preds = self.op.Predictions([t]).wait()[t]
            if len(preds) < obj:
                pred = 'none'
            else:
                pred = int(preds[obj])

            probs = self.op.Probabilities([t]).wait()[t]
            if len(probs) < obj:
                prob = 'none'
            else:
                prob = probs[obj]

            numpy.set_printoptions(precision=4)

            print "------------------------------------------------------------"
            print "object:         {}".format(obj)
            print "label:          {}".format(label)
            print "probabilities:  {}".format(prob)
            print "prediction:     {}".format(pred)

            print 'features:'
            feats = self.op.ObjectFeatures([t]).wait()[t]
            featnames = feats.keys()
            for featname in featnames:
                print "{}:".format(featname)
                value = feats[featname]
                ft = numpy.asarray(value.squeeze())[obj]
                print ft
            print "------------------------------------------------------------"
            
    def setVisible(self, visible):
        if visible:
            self.op.triggerTransferLabels(self.op.current_view_index())
        super(ObjectClassificationGui, self).setVisible(visible)
        
