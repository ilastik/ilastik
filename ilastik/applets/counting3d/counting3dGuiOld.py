from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot, QObject

from ilastik.widgets.featureTableWidget import FeatureEntry
from ilastik.widgets.featureDlg import FeatureDlg

import os
import numpy
from ilastik.utility import bind
from lazyflow.operators import OpSubRegion

#import logging
#logger = logging.getLogger(__name__)
#traceLogger = logging.getLogger('TRACE.' + __name__)

from ilastik.applets.layerViewer import LayerViewerGui
from ilastik.applets.labeling import LabelingGui

import volumina.colortables as colortables
from volumina.api import \
    LazyflowSource, GrayscaleLayer, ColortableLayer, AlphaModulatedLayer, \
    ClickableColortableLayer, LazyflowSinkSource
from sitecustomize import debug_trace

from volumina.interpreter import ClickInterpreter, ClickReportingInterpreter

from PyQt4.QtCore import QObject, pyqtSignal, QEvent, Qt, QPoint
from PyQt4.QtCore import QPoint, QRect, QSize



class ClickReportingInterpreter(QObject):
    rightClickReceived = pyqtSignal(object, QPoint) # list of indexes, global window coordinate of click
    leftClickReceived = pyqtSignal(object, QPoint)  # ditto
    leftClickReleased = pyqtSignal(object, object)
    
    def __init__(self, navigationInterpreter, positionModel, editor):
        QObject.__init__(self)
        self.baseInterpret = navigationInterpreter
        self.posModel      = positionModel
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, editor)
        self.origin = QPoint()
        self.originpos = object()

    def start( self ):
        self.baseInterpret.start()

    def stop( self ):
        self.baseInterpret.stop()

    def eventFilter( self, watched, event ):
        if event.type() == QEvent.MouseButtonPress:
            pos = [int(i) for i in self.posModel.cursorPos]
            pos = [self.posModel.time] + pos + [self.posModel.channel]

            if event.button() == Qt.LeftButton:
                self.origin = QPoint(event.pos())
                self.originpos = pos
                self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                self.rubberBand.show()
                gPos = watched.mapToGlobal( event.pos() )
                self.leftClickReceived.emit( pos, gPos )
            if event.button() == Qt.RightButton:
                gPos = watched.mapToGlobal( event.pos() )
                self.rightClickReceived.emit( pos, gPos )                
        if event.type() == QEvent.MouseMove:
            if not self.origin.isNull():
                self.rubberBand.setGeometry(QRect(self.origin,
                                                  event.pos()).normalized())
        if event.type() == QEvent.MouseButtonRelease:
            pos = [int(i) for i in self.posModel.cursorPos]
            pos = [self.posModel.time] + pos + [self.posModel.channel]
            if event.button() == Qt.LeftButton:
                self.rubberBand.hide()
                self.leftClickReleased.emit( self.originpos,pos )                

    

        # Event is always forwarded to the navigation interpreter.
        return self.baseInterpret.eventFilter(watched, event)

class Counting3dGui(LabelingGui):

    def centralWidget(self):
        return self

    def appletDrawers(self):
        # Get the labeling drawer from the base class
        labelingDrawer = super(Counting3dGui, self).appletDrawers()[0][1]
        return [("Training", labelingDrawer)]

    def reset(self):
        # Base class first
        super(Counting3dGui, self).reset()

        # Ensure that we are NOT in interactive mode
        #self.labelingDrawerUi.checkInteractive.setChecked(False)
        #self.labelingDrawerUi.checkShowPredictions.setChecked(False)

    def __init__(self, topLevelOperatorView, shellRequestSignal, guiControlSignal, predictionSerializer ):
        self.op = topLevelOperatorView
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = topLevelOperatorView.LabelInputs
        labelSlots.labelOutput = topLevelOperatorView.LabelImages
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelPipeline.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = topLevelOperatorView.MaxLabelValue
        labelSlots.labelsAllowed = topLevelOperatorView.LabelsAllowedFlags

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'

        # Base class init
        super(Counting3dGui, self).__init__( labelSlots, topLevelOperatorView, labelingDrawerUiPath, rawInputSlot =
                                            self.op.InputImages )
        # Tell our base class which slots to monitor

        # We provide our own UI file (which adds an extra control for interactive mode)
        # This UI file is copied from pixelClassification pipeline
        #

        # Base class init


        self.topLevelOperatorView = topLevelOperatorView
        self.shellRequestSignal = shellRequestSignal
        self.guiControlSignal = guiControlSignal
        self.predictionSerializer = predictionSerializer

        labelSlots.maxLabelValue.setValue(0)
        #self.op.InputChannelIndexes.notifyDirty( self.updateInputChannelGui )
        self._labelControlUi.SigmaLine.setText("1")
        self._labelControlUi.UnderLine.setText("1000")
        self._labelControlUi.OverLine.setText("1000")
        for option in self.op.options:
            print "option", option
            self._labelControlUi.SVROptions.addItem('+'.join(option.values()), (option,))

        self._addNewLabel()
        self._addNewLabel()

        self._train()
        #self.updateDensitySum()
        #self.op.InputChannelIndexes.setValue([])
        #self.op.InputChannelIndexes.setValue([0])

        #self.editor = VolumeEditor(self.layerstack)

        # Replace the editor's navigation interpreter with one that has extra functionality

        #self.editor.newImageView2DFocus.connect(self._setIconToViewMenu)
        #self.editor.setInteractionMode( 'navigation' )
        #self.volumeEditorWidget.init(self.editor)

        #self.editor._lastImageViewFocus = 0

        # Zoom at a 1-1 scale to avoid loading big datasets entirely...
        #for view in self.editor.imageViews:
        #    view.doScaleTo(1)

   # Replace the editor's navigation interpreter with one that has extra functionality
        self.clickReporter = ClickReportingInterpreter(
            self.editor.navInterpret, self.editor.posModel, self.centralWidget() )
        self.editor.setNavigationInterpreter( self.clickReporter )
        #self.clickReporter.rightClickReceived.connect( self._handleEditorRightClick )
        self.clickReporter.leftClickReleased.connect( self.test )

        #self.editor.newImageView2DFocus.connect(self._setIconToViewMenu)
        self.editor.setInteractionMode( 'navigation' )
        #self.op.Density.notifyDirty(self.updateDensitySum)



#    def initAppletDrawerUi(self):
#        """
#        Load the ui file for the applet drawer, which we own.
#        """
#        localDir = os.path.split(__file__)[0]
#        # (We don't pass self here because we keep the drawer ui in a separate object.)
#        self._labelControlUi = uic.loadUi(localDir+"/labelingDrawer.ui")
#        #self._labelControlUi.ChangeChannelsButton.pressed.connect(self._changeChannels)
#        self._labelControlUi.DebugButton.pressed.connect(self._debug)
#        self._labelControlUi.TrainButton.pressed.connect(self._train)
#        self._labelControlUi.PredictionButton.pressed.connect(self.updateDensitySum)
#        self._labelControlUi.SVROptions.currentIndexChanged.connect(self._updateSVROptions)

    def _updateSVROptions(self, index):
        option = self._labelControlUi.SVROptions.itemData(index).toPyObject()[0]
        self.op.SelectedOption.setValue(option)

#    def getAppletDrawerUi(self):
#        return self._labelControlUi

    def setupLayers(self):
        layers = super(Counting3dGui, self).setupLayers()

        from PyQt4.QtGui import QColor
        # Base class provides the label layer.
        #layers = super(Counting3dGui, self).setupLayers()
        #This is just for colors
        #labels = self.labelListData

        #Personal Note: the standardlayer rescales its value range when
        #displaying gray value images, which, in turn, makes some data invisible
        #when being viewed after some others.


        #labelOutput = self._labelingSlots.labelOutput
        slots = {#'featureData' : self.op.FeatureData, 
                 #'filteredFeatureData' : self.op.FilteredFeatureData,
                 #'modFeatureData' : self.op.ModifiedFeatureData, 
                 'density' : self.op.Density
                 #'FilteredRawData' : self.op.FilteredRaw
                }
        colortableSlots = {
            'UserLabels' : self.op.LabelImages
        
        }
        for name, slot in colortableSlots.items():
            if slot.ready():
                self.imagesrc = LazyflowSource(slot)
                ct = colortables.default16
                ct[0] = QColor(0,0,0,0)
                layer = ColortableLayer(self.imagesrc, colorTable =
                                        colortables.default16)
                layer.zeroIsTransparent= True
                layer.name = name
                layers.append(layer)
        for name, slot in slots.items():
            if slot.ready():
                self.imagesrc = LazyflowSource(slot)
                layer = self.createStandardLayerFromSlot(slot)
                layer.name = name
                layers.append(layer)



        #if binarySlot.ready():
        #    ct_binary = [QColor(0,0,0,0).rgba(), QColor(0,0,255,255).rgba()]
        #    self.binaryimagesrc = LazyflowSource(binarySlot)
        #    #layer = GrayscaleLayer(self.binaryimagesrc, range=(0,1), normalize=(0,1))
        #    layer = ColortableLayer(self.binaryimagesrc, ct_binary)
        #    layer.name = "Binary Image"
        #    layers.append(layer)
        #predictionSlot = self.op.PredictionImages
        #if predictionSlot.ready():
        #    self.predictsrc = LazyflowSource(predictionSlot)
        #    self.predictlayer = ColortableLayer(self.predictsrc, colorTable=self._colorTable16)
        #    self.predictlayer.name = "Prediction"
        #    self.predictlayer.ref_object = None
        #    self.predictlayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()

        #    # put first, so that it is visible after hitting "live
        #    # predict".
        #    layers.insert(0, self.predictlayer)

        return layers

    @pyqtSlot()
    def handleLabelSelectionChange(self):
        enabled = False
        if self.op.NumLabels.ready():
            enabled = True
            enabled &= self.op.NumLabels.value >= 2

        self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self.labelingDrawerUi.checkInteractive.setEnabled(enabled)
        self.labelingDrawerUi.checkShowPredictions.setEnabled(enabled)

    def toggleInteractive(self, checked):
        logger.debug("toggling interactive mode to '%r'" % checked)
        # if checked and len(self.op.ObjectFeatures) == 0:
        #     self.labelingDrawerUi.checkInteractive.setChecked(False)
        #     mexBox=QMessageBox()
        #     mexBox.setText("There are no features selected ")
        #     mexBox.exec_()
        #     return

        self.labelingDrawerUi.savePredictionsButton.setEnabled(not checked)
        self.op.FreezePredictions.setValue(not checked)

        # Auto-set the "show predictions" state according to what the
        # user just clicked.
        if checked:
            self.labelingDrawerUi.checkShowPredictions.setChecked(True)
            self.handleShowPredictionsClicked()

        # If we're changing modes, enable/disable our controls and
        # other applets accordingly
        #if self.interactiveModeActive != checked:
        #    if checked:
        #        self.labelingDrawerUi.labelListView.allowDelete = False
        #        self.labelingDrawerUi.AddLabelButton.setEnabled(False)
        #    else:
        #        self.labelingDrawerUi.labelListView.allowDelete = True
        #        self.labelingDrawerUi.AddLabelButton.setEnabled(True)
        #self.interactiveModeActive = checked

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

    def onClick(self, layer, pos5D, pos):
        """Extracts the object index that was clicked on and updates
        that object's label.

        """
        label = self.editor.brushingModel.drawnNumber
        if label == self.editor.brushingModel.erasingNumber:
            label = 0
        assert 0 <= label <= self._labelingSlots.maxLabelValue.value
        slicing = tuple(slice(i, i+1) for i in pos5D)

        arr = layer.segmentationImageSlot[slicing].wait()
        obj = arr.flat[0]
        if obj == 0: # background; FIXME: do not hardcode
            return
        t = pos5D[0]

        labelslot = layer._datasources[0]._inputSlot
        labelsdict = labelslot.value
        labels = labelsdict[t]

        nobjects = len(labels)
        if obj >= nobjects:
            newLabels = numpy.zeros((obj + 1),)
            newLabels[:nobjects] = labels[:]
            labels = newLabels
        labels[obj] = label
        labelsdict[t] = labels
        labelslot.setValue(labelsdict)
        labelslot.setDirty([(t, obj)])
    
    
    def _changeChannels( self ):
        sigma = [float(n) for n in
                       self._labelControlUi.ChannelList.text().split(" ")]
        #print channelList
        self.op._changeChannels(sigma)
    
    def _train( self ):
        sigma = [float(n) for n in
                       self._labelControlUi.SigmaLine.text().split(" ")]
        #print channelList
        underMult = float(self._labelControlUi.UnderLine.text())
        overMult = float(self._labelControlUi.OverLine.text())
        self.op._updateParams(sigma,underMult,overMult)

    def _debug(self):
        import sitecustomize
        sitecustomize.debug_trace()

    def updateDensitySum(self,*args, **kwargs):
        print "updateDensitySum"
        density = self.op.OutputSum.value

        self._labelControlUi.CountText.setText(str(density))
    
    def test(self, position5d_start, position5d_stop):
        from lazyflow.rtype import SubRegion
        import numpy
        from sitecustomize import debug_trace

        roi = SubRegion(self.op.Density, position5d_start,
                                       position5d_stop)
        key = roi.toSlice()
        key = tuple(k for k in key if k != slice(0,0, None))
        newKey = []
        for k in key:
            if k != slice(0,0,None):
                if k.stop < k.start:
                    k = slice(k.stop, k.start)
            newKey.append(k)
        newKey = tuple(newKey)
        try:
            density = numpy.sum(self.op.Density[newKey].wait())
            self._labelControlUi.CountText.setText(str(density))
        except:
            debug_trace()

