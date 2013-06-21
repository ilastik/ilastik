# Built-in
import os
import logging
import threading
from functools import partial

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4.QtGui import QMessageBox, QColor, QShortcut, QKeySequence, QPushButton, QWidget, QIcon

# HCI
from lazyflow.utility import traceLogged
from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer, LazyflowSinkSource
from volumina.utility import ShortcutManager
from ilastik.widgets.labelListView import Label
from ilastik.widgets.boxListModel import BoxListModel,BoxLabel
from ilastik.widgets.labelListModel import LabelListModel
from lazyflow.rtype import SubRegion
from volumina.navigationControler import NavigationInterpreter

# ilastik
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.labeling import LabelingGui
from ilastik.applets.base.applet import ShellRequest, ControlCommand
from lazyflow.operators.adaptors import Op5ifyer



try:
    from volumina.view.volumeRendering import RenderingManager
except:
    pass

# Loggers
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new):]
    else:
        return new




from PyQt4.QtCore import QObject, QRect, QSize, pyqtSignal, QEvent, QPoint,QString,QVariant
from PyQt4.QtGui import QRubberBand,QRubberBand,qRed,QPalette,QBrush,QColor,QGraphicsColorizeEffect,\
        QStylePainter, QPen

from countingGuiElements import BoxController,BoxInterpreter,Tool

        

class CountingGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self

    def reset(self):
        # Base class first
        super(CountingGui, self).reset()

        # Ensure that we are NOT in interactive mode
        self.labelingDrawerUi.liveUpdateButton.setChecked(False)
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
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelPipeline.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = topLevelOperatorView.MaxLabelValue
        labelSlots.labelsAllowed = topLevelOperatorView.LabelsAllowedFlags

        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'

        # Base class init
        super(CountingGui, self).__init__( labelSlots, topLevelOperatorView, labelingDrawerUiPath )
        
        self.op = topLevelOperatorView
        #self.clickReporter.rightClickReceived.connect( self._handleEditorRightClick )

        self.topLevelOperatorView = topLevelOperatorView
        self.shellRequestSignal = shellRequestSignal
        self.guiControlSignal = guiControlSignal
        self.predictionSerializer = predictionSerializer

        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

        self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)
        self.labelingDrawerUi.savePredictionsButton.setIcon( QIcon(ilastikIcons.Save) )
        
        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon( QIcon(ilastikIcons.Play) )
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect( self.toggleInteractive )

        self.topLevelOperatorView.MaxLabelValue.notifyDirty( bind(self.handleLabelSelectionChange) )
        
        self._initShortcuts()

        try:
            self.render = True
            self._renderedLayers = {} # (layer name, label number)
            self._renderMgr = RenderingManager(
                renderer=self.editor.view.qvtk.renderer,
                qvtk=self.editor.view.qvtk)
        except:
            self.render = False


        self.initCounting()

    
    def initCounting(self):
        #=======================================================================
        # Init Label Uic Custom  setup
        #=======================================================================
        
        self._viewerControlUi.label.setVisible(False)
        self._viewerControlUi.checkShowPredictions.setVisible(False)
        self._viewerControlUi.checkShowSegmentation.setVisible(False)
        
        
        
        self._addNewLabel()
        self._addNewLabel()
        self._labelControlUi.brushSizeComboBox.setEnabled(False) 
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self.selectLabel(0)

        self.labelingDrawerUi.labelListModel.makeRowPermanent(0)
        self.labelingDrawerUi.labelListModel.makeRowPermanent(1)
        
        self.labelingDrawerUi.labelListModel[0].name = "Foreground"
        self.labelingDrawerUi.labelListModel[1].name = "Background"
        
        self.labelingDrawerUi.labelListView.shrinkToMinimum()

        self.labelingDrawerUi.SigmaLine.setText(str(self.op.opTrain.Sigma.value))
        self.labelingDrawerUi.CBox.setRange(0,1000)
        self.labelingDrawerUi.CBox.setKeyboardTracking(False)
        self.labelingDrawerUi.EpsilonBox.setKeyboardTracking(False)
        self.labelingDrawerUi.EpsilonBox.setDecimals(6)
        self.labelingDrawerUi.NtreesBox.setKeyboardTracking(False)
        self.labelingDrawerUi.MaxDepthBox.setKeyboardTracking(False)

        for option in self.op.options:
            if "req" in option.keys():
                try:
                    import imp
                    for req in option["req"]:
                        imp.find_module(req)
                except:
                    continue
            #values=[v for k,v in option.items() if k not in ["gui", "req"]]
            self.labelingDrawerUi.SVROptions.addItem(option["method"], (option,))
        
        self._setUIParameters()
        
        self.labelingDrawerUi.DebugButton.pressed.connect(self._debug)
        #elf._updateSVROptions()
        self.labelingDrawerUi.boxListView.resetEmptyMessage("no boxes defined yet")
        #self.labelingDrawerUi.boxListView._colorDialog=BoxDialog()
        #self.labelingDrawerUi.TrainButton.pressed.connect(self._train)
        #self.labelingDrawerUi.PredictionButton.pressed.connect(self.updateDensitySum)
        self.labelingDrawerUi.SVROptions.currentIndexChanged.connect(self._updateSVROptions)
        #self.labelingDrawerUi.OverBox.valueChanged.connect(self._updateOverMult)
        #self.labelingDrawerUi.UnderBox.valueChanged.connect(self._updateUnderMult)
        self.labelingDrawerUi.CBox.valueChanged.connect(self._updateC)
        self.labelingDrawerUi.SigmaLine.editingFinished.connect(self._updateSigma)
        self.labelingDrawerUi.SigmaLine.textChanged.connect(self._changedSigma)
        self.labelingDrawerUi.EpsilonBox.valueChanged.connect(self._updateEpsilon)
        self.labelingDrawerUi.MaxDepthBox.valueChanged.connect(self._updateMaxDepth)
        self.labelingDrawerUi.NtreesBox.valueChanged.connect(self._updateNtrees)
        

        self._registerOperatorsToGuiCallbacks() 

        
        
        self._updateNtrees()
        self._updateMaxDepth()
        
        
        self.changedSigma = False
        
        self.labelingDrawerUi.CountText.setReadOnly(True)
        
        
        
        
        #=======================================================================
        # Density boxes elements
        #=======================================================================
            
        def updateSum(*args, **kw):
            print "updatingSum"
            density = self.op.OutputSum.value 
            strdensity = "{0:.2f}".format(density)
            self._labelControlUi.CountText.setText(strdensity)

        self.op.Density.notifyDirty(updateSum)
    
        self.density5d=Op5ifyer(graph=object()) #FIXME: Hack , get the proper reference to the graph
        self.density5d.input.connect(self.op.Density)
    
        
        if not hasattr(self._labelControlUi, "boxListModel"):
            self.labelingDrawerUi.boxListModel=BoxListModel()
            self.labelingDrawerUi.boxListView.setModel(self.labelingDrawerUi.boxListModel)
            self.labelingDrawerUi.boxListModel.elementSelected.connect(self._onBoxSelected)
            self.labelingDrawerUi.boxListModel.boxRemoved.connect(self._removeBox)
        
        
        
        
        mainwin=self
        self.boxController=BoxController(mainwin.editor.imageScenes[2],self.density5d.output,self.labelingDrawerUi.boxListModel)
        self.boxIntepreter=BoxInterpreter(mainwin.editor.navInterpret,mainwin.editor.posModel,self.boxController,mainwin.centralWidget())
        
        
#         ###FIXME: Only for debug
        self.rubberbandClickReporter = self.boxIntepreter
        self.rubberbandClickReporter.leftClickReleased.connect( self.handleBoxQuery )
        self.rubberbandClickReporter.leftClickReleased.connect(self._addNewBox)
        self.navigationIntepreterDefault=self.editor.navInterpret
        #self.editor.setNavigationInterpreter(self.rubberbandClickReporter)

        self.boxController.fixedBoxesChanged.connect(self._handleBoxConstraints)
    
        
    
    def _registerOperatorsToGuiCallbacks(self):
        
        class CallToGui:
            def __init__(self,opslot,setfun):
                '''
                Helper class which defines a simple callback between an operator and a gui 
                element so that gui elements can be kept in sync across different images
                :param opslot:
                :param setfun:
                :param defaultval:
                '''
                
                self.val=None
                self.opslot=opslot
                self.setfun=setfun
                self._exec()
                self.opslot.notifyDirty(bind(self._exec))
            
            def _exec(self):
                if self.opslot.ready():
                    self.val=self.opslot.value
                    
                if self.val!=None:
                    self.setfun(self.val)
        
        op=self.op.opTrain
        gui=self.labelingDrawerUi
        
        CallToGui(op.Ntrees,gui.NtreesBox.setValue)
        CallToGui(op.MaxDepth,gui.MaxDepthBox.setValue)

        CallToGui(op.C,gui.CBox.setValue)
        
        def _setsigma(floatList):
            ss=""
            for el in floatList:
                ss+="%.1f "%el
            ss=ss[:-1]
            gui.SigmaLine.setText(QString(ss))
        
        CallToGui(op.Sigma,_setsigma)
        CallToGui(op.Epsilon,gui.EpsilonBox.setValue)
        
        def _setoption(option):
            ss = option["method"]
            index=gui.SVROptions.findText(ss)
            gui.SVROptions.setCurrentIndex(index)
            
        CallToGui(op.SelectedOption,_setoption)
        
        
        
        
        
    
    def _setUIParameters(self):
        if self.op.classifier_cache._value and len(self.op.classifier_cache._value) > 0:
            #use parameters from cached classifier
            params = self.op.classifier_cache.Output.value.get_params() 
            Sigma = params["Sigma"]
            Epsilon = params["epsilon"]
            C = params["C"]
            Ntrees = params["ntrees"]
            MaxDepth = params["maxdepth"]
            _ind = self.labelingDrawerUi.SVROptions.findText(params["method"])
        
        else:
            #read parameters from opTrain Operator

            Sigma = self.op.opTrain.Sigma.value
            Epsilon = self.op.opTrain.Epsilon.value
            C = self.op.opTrain.C.value
            Ntrees = self.op.opTrain.Ntrees.value
            MaxDepth = self.op.opTrain.MaxDepth.value
            _ind = self.labelingDrawerUi.SVROptions.findText(self.op.opTrain.SelectedOption.value["method"])


        self.labelingDrawerUi.SigmaLine.setText(" ".join(str(s) for s in Sigma))
        self.labelingDrawerUi.EpsilonBox.setValue(Epsilon)
        self.labelingDrawerUi.CBox.setValue(C)
        self.labelingDrawerUi.NtreesBox.setValue(Ntrees)
        self.labelingDrawerUi.MaxDepthBox.setValue(MaxDepth)
        self.labelingDrawerUi.SVROptions.setCurrentIndex(_ind)
        self._hideParameters()

        
    def _updateMaxDepth(self):
        self.op.opTrain.MaxDepth.setValue(self.labelingDrawerUi.MaxDepthBox.value())
    def _updateNtrees(self):
        self.op.opTrain.Ntrees.setValue(self.labelingDrawerUi.NtreesBox.value())
    
    def _hideParameters(self):
        _ind = self.labelingDrawerUi.SVROptions.currentIndex()
        option = self.labelingDrawerUi.SVROptions.itemData(_ind).toPyObject()[0]
        if "svr" not in option["gui"]:
            self.labelingDrawerUi.gridLayout_2.setVisible(False)
        else:
            self.labelingDrawerUi.gridLayout_2.setVisible(True)
            
 
        if "rf" not in option["gui"]:
            self.labelingDrawerUi.rf_panel.setVisible(False)
        else:
            self.labelingDrawerUi.rf_panel.setVisible(True)
    #def _updateOverMult(self):
    #    self.op.opTrain.OverMult.setValue(self.labelingDrawerUi.OverBox.value())
    #def _updateUnderMult(self):
    #    self.op.opTrain.UnderMult.setValue(self.labelingDrawerUi.UnderBox.value())
    def _updateC(self):
        self.op.opTrain.C.setValue(self.labelingDrawerUi.CBox.value())
        print "blub"
    def _updateSigma(self):
        if self.changedSigma:
            sigma = [float(n) for n in
                           self._labelControlUi.SigmaLine.text().split(" ")]
            self.op.opTrain.Sigma.setValue(sigma)
            self.changedSigma = False

    def _changedSigma(self, text):
        self.changedSigma = True

    def _updateEpsilon(self):
        self.op.opTrain.Epsilon.setValue(self.labelingDrawerUi.EpsilonBox.value())

    def _updateSVROptions(self):
        index = self.labelingDrawerUi.SVROptions.currentIndex()
        option = self.labelingDrawerUi.SVROptions.itemData(index).toPyObject()[0]
        self.op.opTrain.SelectedOption.setValue(option)

        self._hideParameters()        

    def _handleBoxConstraints(self, constr):
        self.op.opTrain.BoxConstraints.setValue(constr)

        #boxes = self.boxController._currentBoxesList


    def _debug(self):
        import sitecustomize
        sitecustomize.debug_trace()


    @traceLogged(traceLogger)
    def initViewerControlUi(self):
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi( os.path.join( localDir, "viewerControls.ui" ) )
        
        # Connect checkboxes
        def nextCheckState(checkbox):
            checkbox.setChecked( not checkbox.isChecked() )

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

    @traceLogged(traceLogger)
    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(CountingGui, self).setupLayers()

        # Add each of the predictions
        labels = self.labelListData
     


        slots = {'Prediction' : self.op.Density}

        for name, slot in slots.items():
            if slot.ready():
                from volumina import colortables
                layer = ColortableLayer(LazyflowSource(slot), colorTable = colortables.jet(), normalize = 'auto')
                layer.name = name
                layer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                #layer.visibleChanged.connect(self.updateShowPredictionCheckbox)
                layers.append(layer)


        boxlabelsrc = LazyflowSinkSource(self.op.BoxLabelImages,self.op.BoxLabelInputs )
        boxlabellayer = ColortableLayer(boxlabelsrc, colorTable = self._colorTable16, direct = False)
        boxlabellayer.name = "boxLabels"
        boxlabellayer.opacity = 1.0
        boxlabellayer.visibleChanged.connect(self.boxController.changeBoxesVisibility)
        boxlabellayer.opacityChanged.connect(self.boxController.changeBoxesOpacity)
        
        
        
        layers.append(boxlabellayer)
        self.boxlabelsrc = boxlabelsrc


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

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        """
        If enable
        """
        logger.debug("toggling interactive mode to '%r'" % checked)

        if checked==True:
            if not self.topLevelOperatorView.FeatureImages.ready() \
            or self.topLevelOperatorView.FeatureImages.meta.shape==None:
                self.labelingDrawerUi.liveUpdateButton.setChecked(False)
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
                #self.labelingDrawerUi.AddLabelButton.setEnabled( False )
            else:
                self.labelingDrawerUi.labelListView.allowDelete = True
                #self.labelingDrawerUi.AddLabelButton.setEnabled( True )
        self.interactiveModeActive = checked

    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleShowPredictionsClicked(self):
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

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
    @threadRouted
    @traceLogged(traceLogger)
    def handleLabelSelectionChange(self):
        enabled = False
        if self.topLevelOperatorView.MaxLabelValue.ready():
            enabled = True
            enabled &= self.topLevelOperatorView.MaxLabelValue.value >= 2
            enabled &= numpy.all(numpy.asarray(self.topLevelOperatorView.CachedFeatureImages.meta.shape) > 0)
            # FIXME: also check that each label has scribbles?
        
        self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self.labelingDrawerUi.liveUpdateButton.setEnabled(enabled)
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
                logger.info("Starting full volume save...")
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
                logger.info("Finished full volume save.")

            saveThread = threading.Thread(target=saveThreadFunc)
            saveThread.start()

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
        super(CountingGui, self)._onLabelRemoved(parent, start, end)
        op = self.topLevelOperatorView
        for slot in (op.LabelNames, op.LabelColors, op.PmapColors):
            value = slot.value
            value.pop(start)
            slot.setValue(value)

    def getNextLabelName(self):
        return self._getNext(self.topLevelOperatorView.LabelNames,
                             super(CountingGui, self).getNextLabelName)

    def getNextLabelColor(self):
        return self._getNext(
            self.topLevelOperatorView.LabelColors,
            super(CountingGui, self).getNextLabelColor,
            lambda x: QColor(*x)
        )

    def getNextPmapColor(self):
        return self._getNext(
            self.topLevelOperatorView.PmapColors,
            super(CountingGui, self).getNextPmapColor,
            lambda x: QColor(*x)
        )

    def onLabelNameChanged(self):
        self._onLabelChanged(super(CountingGui, self).onLabelNameChanged,
                             lambda l: l.name,
                             self.topLevelOperatorView.LabelNames)

    def onLabelColorChanged(self):
        self._onLabelChanged(super(CountingGui, self).onLabelColorChanged,
                             lambda l: (l.brushColor().red(),
                                        l.brushColor().green(),
                                        l.brushColor().blue()),
                             self.topLevelOperatorView.LabelColors)


    def onPmapColorChanged(self):
        self._onLabelChanged(super(CountingGui, self).onPmapColorChanged,
                             lambda l: (l.pmapColor().red(),
                                        l.pmapColor().green(),
                                        l.pmapColor().blue()),
                             self.topLevelOperatorView.PmapColors)

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
            color = (color.red(), color.green() , color.blue() )
            self._renderMgr.setColor(label, color)



    def _gui_setNavigation(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(True)
#         if not hasattr(self, "rubberbandClickReporter"):
#             
#             self.rubberbandClickReporter = self.boxIntepreter
#             self.rubberbandClickReporter.leftClickReleased.connect( self.handleBoxQuery )
#         self.editor.setNavigationInterpreter(self.rubberbandClickReporter)
    
    def _gui_setBrushing(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        # Make sure the paint button is pressed
        self._labelControlUi.paintToolButton.setChecked(True)
        # Show the brush size control and set its caption
        self._labelControlUi.brushSizeCaption.setText("Size:")
        # Make sure the GUI reflects the correct size
        self._labelControlUi.brushSizeComboBox.setCurrentIndex(0)

    def _gui_setBox(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(False)
        
        #self._labelControlUi.boxToolButton.setChecked(True)
        
    
    def _onBoxChanged(self,parentFun, mapf):
        
        parentFun()
        new = map(mapf, self.labelListData)
    
    
    def _changeInteractionMode( self, toolId ):
        """
        Implement the GUI's response to the user selecting a new tool.
        """
        # Uncheck all the other buttons
        for tool, button in self.toolButtons.items():
            if tool != toolId:
                button.setChecked(False)

        # If we have no editor, we can't do anything yet
        if self.editor is None:
            return

        # The volume editor expects one of two specific names
        modeNames = { Tool.Navigation   : "navigation",
                      Tool.Paint        : "brushing",
                      Tool.Erase        : "brushing",
                      Tool.Box          : "navigation"
                    }

        # If the user can't label this image, disable the button and say why its disabled
        labelsAllowed = False

        labelsAllowedSlot = self._labelingSlots.labelsAllowed
        if labelsAllowedSlot.ready():
            labelsAllowed = labelsAllowedSlot.value

            if hasattr(self._labelControlUi, "AddLabelButton"):
                self._labelControlUi.AddLabelButton.setEnabled(labelsAllowed and self.maxLabelNumber > self._labelControlUi.labelListModel.rowCount())
                if labelsAllowed:
                    self._labelControlUi.AddLabelButton.setText("Add Label")
                else:
                    self._labelControlUi.AddLabelButton.setText("(Labeling Not Allowed)")

        e = labelsAllowed & (self._labelControlUi.labelListModel.rowCount() > 0)
        self._gui_enableLabeling(e)
        
        if labelsAllowed:
            # Update the applet bar caption
            if toolId == Tool.Navigation:
                # update GUI 
                self.editor.brushingModel.setBrushSize(0)
                self.editor.setNavigationInterpreter(NavigationInterpreter(self.editor.navCtrl))
                self._gui_setNavigation()
                
            elif toolId == Tool.Paint:
                # If necessary, tell the brushing model to stop erasing
                if self.editor.brushingModel.erasing:
                    self.editor.brushingModel.disableErasing()
                # Set the brushing size
                brushSize = 1
                self.editor.brushingModel.setBrushSize(brushSize)
                # update GUI 
                self._gui_setBrushing()


            elif toolId == Tool.Erase:
                # If necessary, tell the brushing model to start erasing
                if not self.editor.brushingModel.erasing:
                    self.editor.brushingModel.setErasing()
                # Set the brushing size
                eraserSize = self.brushSizes[self.eraserSizeIndex]
                self.editor.brushingModel.setBrushSize(eraserSize)
                # update GUI 
                self._gui_setErasing()
            
            elif toolId == Tool.Box:
                print "Interaction mode box"
                self.editor.brushingModel.setBrushSize(0)
                self.editor.setNavigationInterpreter(self.boxIntepreter)
                self._gui_setBox()

        self.editor.setInteractionMode( modeNames[toolId] )
        self._toolId = toolId



    def _initLabelUic(self, drawerUiPath):
        super(CountingGui, self)._initLabelUic(drawerUiPath)
        #self._labelControlUi.boxToolButton.setCheckable(True)
        #self._labelControlUi.boxToolButton.clicked.connect( lambda checked: self._handleToolButtonClicked(checked,
        #                                                                                                  Tool.Box) )
        #self.toolButtons[Tool.Box] = self._labelControlUi.boxToolButton
        if hasattr(self._labelControlUi, "AddBoxButton"):

            self._labelControlUi.AddBoxButton.setIcon( QIcon(ilastikIcons.AddSel) )
            self._labelControlUi.AddBoxButton.clicked.connect( bind(self.onAddNewBoxButtonClicked) )
        
        
    
    def onAddNewBoxButtonClicked(self):

        self._changeInteractionMode(Tool.Box)
#         qcolor=self._getNextBoxColor()
#         self.boxController.currentColor=qcolor
        self.labelingDrawerUi.boxListView.resetEmptyMessage("Draw the box on the image")
        
    
    def _addNewBox(self):
#         pass
        
        #Fixme: The functionality should maybe removed from here
        
        newRow = self.labelingDrawerUi.boxListModel.rowCount()-1
        newColorIndex = self._labelControlUi.boxListModel.index(newRow, 0)
#         qcolor=self._getNextBoxColor()
#         self.boxController.currentColor=qcolor


        # Call the 'changed' callbacks immediately to initialize any listeners
        #self.onLabelNameChanged()
        #self.onLabelColorChanged()
        #self.onPmapColorChanged()

    
    def _removeBox(self,index):
        #handled by the boxController
        pass 
        
        #self.boxController.deleteItem(index)
        
         
    def _onBoxSelected(self, row):
        print "switching to box=%r" % (self._labelControlUi.boxListModel[row])
        print "row = ",row
        logger.debug("switching to label=%r" % (self._labelControlUi.boxListModel[row]))

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Box)

        print len(self.boxController._currentBoxesList)
        self.boxController.selectBoxItem(row)
    
    @traceLogged(traceLogger)
    def onBoxListDataChanged(self, topLeft, bottomRight):
        pass
#         """Handle changes to the label list selections."""
#         firstRow = topLeft.row()
#         lastRow  = bottomRight.row()
#  
#         firstCol = topLeft.column()
#         lastCol  = bottomRight.column()
#  
#         # We only care about the color column
#         if firstCol <= 0 <= lastCol:
#             assert(firstRow == lastRow) # Only one data item changes at a time
#  
#             #in this case, the actual data (for example color) has changed
#             color = self._labelControlUi.boxListModel[firstRow].brushColor()
#             self._colorTable16[firstRow+1] = color.rgba()
#             self.editor.brushingModel.setBrushColor(color)
#  
#             # Update the label layer colortable to match the list entry
#             labellayer = self._getLabelLayer()
#             if labellayer is not None:
#                 labellayer.colorTable = self._colorTable16
    
    def _onLabelSelected(self, row):
        print "switching to label=%r" % (self._labelControlUi.labelListModel[row])
        logger.debug("switching to label=%r" % (self._labelControlUi.labelListModel[row]))

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Paint)

        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        if row >= 2:
            self.toolButtons[Tool.Paint].setEnabled(False)
            self.toolButtons[Tool.Box].setEnabled(True)
            self.toolButtons[Tool.Box].click()
            self.activeBox = row - 2
        else:
            self.toolButtons[Tool.Paint].setEnabled(True)
            #elf.toolButtons[Tool.Box].setEnabled(False)
            self.toolButtons[Tool.Paint].click()

        self.editor.brushingModel.setDrawnNumber(row+1)
        brushColor = self._labelControlUi.labelListModel[row].brushColor()
        self.editor.brushingModel.setBrushColor( brushColor )


    def handleBoxQuery(self, position5d_start, position5d_stop):
        print "HANDLING BOX QUERY"
        
        if self._labelControlUi.arrowToolButton.isChecked():
            self.test(position5d_start, position5d_stop)
        #elif self._labelControlUi.boxToolButton.isChecked():
        #    self.test2(position5d_start, position5d_stop)


    def test2(self, position5d_start, position5d_stop):
        print "test2"

        roi = SubRegion(self.op.LabelInputs, position5d_start,
                                       position5d_stop)
        key = roi.toSlice()
        #key = tuple(k for k in key if k != slice(0,0, None))
        newKey = []
        for k in key:
            if k.stop < k.start:
                k = slice(k.stop, k.start)
            newKey.append(k)
        newKey = tuple(newKey)
        self.boxes[self.activeBox] = newKey
        #self.op.BoxLabelImages[newKey] = self.activeBox + 2
        #self.op.BoxLabelImages
        labelShape = tuple([position5d_stop[i] + 1 - position5d_start[i] for i in range(5)])
        labels = numpy.ones((labelShape), dtype = numpy.uint8) * (self.activeBox + 3)
        self.boxlabelsrc.put(newKey, labels)


    def test(self, position5d_start, position5d_stop):
        print "test"
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
            strdensity = "{0:.2f}".format(density)
            self._labelControlUi.CountText.setText(strdensity)
        except:
            pass
        
