from __future__ import absolute_import
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
# Built-in
import os
import logging
import threading
from functools import partial
import importlib

# Third-party
import numpy
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot, QObject, QRect, QSize, pyqtSignal, QEvent, QPoint
from PyQt5.QtGui import QBrush, QColor, QKeySequence, QIcon, QPen, qRed, QPalette
from PyQt5.QtWidgets import QMessageBox, QShortcut, QPushButton, QWidget, QApplication, QAction, \
                            QRubberBand, QRubberBand, QGraphicsColorizeEffect, QStylePainter

# HCI
from lazyflow.utility import traceLogged
from volumina.api import LazyflowSource, AlphaModulatedLayer, ColortableLayer, LazyflowSinkSource
from volumina.utility import ShortcutManager
from ilastik.widgets.labelListView import Label
from ilastik.widgets.boxListModel import BoxListModel,BoxLabel
from ilastik.widgets.labelListModel import LabelListModel
from lazyflow.rtype import SubRegion
from volumina.navigationController import NavigationInterpreter

# ilastik
from ilastik.utility import bind
from ilastik.utility.gui import threadRouted
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.applets.labeling.labelingGui import LabelingGui
from ilastik.applets.base.applet import ShellRequest
from lazyflow.operators.opReorderAxes import OpReorderAxes
from ilastik.applets.counting.countingGuiDotsInterface import DotCrosshairController,DotInterpreter
from ilastik.applets.base.appletSerializer import SerialListSlot


# Loggers
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

def _listReplace(old, new):
    if len(old) > len(new):
        return new + old[len(new):]
    else:
        return new





from .countingGuiBoxesInterface import BoxController,BoxInterpreter,Tool

class CallToGui(object):
    def __init__(self,opslot,setfun):
        '''
        Helper class which registers a simple callback between an operator and a gui
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
            #FXIME: workaround for recently introduced bug when setting
            #sigma box as spindoublebox
            if type(self.val)==list:
                val=self.val[0]
            else:
                val=self.val
            self.setfun(val)

class CountingGui(LabelingGui):

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    def centralWidget( self ):
        return self

    def stopAndCleanUp(self):
        # Base class
        super(CountingGui, self).stopAndCleanUp()

    def viewerControlWidget(self):
        return self._viewerControlUi

    ###########################################
    ###########################################

    @traceLogged(traceLogger)
    def __init__(self, parentApplet, topLevelOperatorView):
        self.isInitialized = False  # need this flag in countingApplet where initialization is terminated with label selection
        self.parentApplet = parentApplet

        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = topLevelOperatorView.LabelInputs
        labelSlots.labelOutput = topLevelOperatorView.LabelImages
        labelSlots.labelEraserValue = topLevelOperatorView.opLabelPipeline.opLabelArray.eraser
        labelSlots.labelDelete = topLevelOperatorView.opLabelPipeline.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = topLevelOperatorView.MaxLabelValue
        labelSlots.labelNames = topLevelOperatorView.LabelNames




        # We provide our own UI file (which adds an extra control for interactive mode)
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/countingDrawer.ui'

        # Base class init
        super(CountingGui, self).__init__(parentApplet, labelSlots, topLevelOperatorView, labelingDrawerUiPath )

        self.op = topLevelOperatorView

        self.topLevelOperatorView = topLevelOperatorView
        self.shellRequestSignal = parentApplet.shellRequestSignal
        self.predictionSerializer = parentApplet.predictionSerializer

        self.interactiveModeActive = False
        self._currentlySavingPredictions = False

#        self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)
#        self.labelingDrawerUi.savePredictionsButton.setIcon( QIcon(ilastikIcons.Save) )

        self.labelingDrawerUi.liveUpdateButton.setEnabled(False)
        self.labelingDrawerUi.liveUpdateButton.setIcon( QIcon(ilastikIcons.Play) )
        self.labelingDrawerUi.liveUpdateButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.labelingDrawerUi.liveUpdateButton.toggled.connect( self.toggleInteractive )
        self.topLevelOperatorView.MaxLabelValue.notifyDirty( bind(self.handleLabelSelectionChange) )

        self.toggleInteractive(not self.topLevelOperatorView.FreezePredictions.value)


        self.initCounting()
        #personal debugging code
        try:
            from sitecustomize import Shortcuts
        except Exception as e:
            self.labelingDrawerUi.DebugButton.setVisible(False)

        self._initShortcuts()




    def initCounting(self):






        #=======================================================================
        # Init Dotting interface
        #=======================================================================


        self.dotcrosshairController=DotCrosshairController(self.editor.brushingModel,self.editor.imageViews)
        self.editor.crosshairController=self.dotcrosshairController
        #self.dotController=DotController(self.editor.imageScenes[2],self.editor.brushingController)
        self.editor.brushingInterpreter = DotInterpreter(self.editor.navCtrl,self.editor.brushingController)
        self.dotInterpreter=self.editor.brushingInterpreter



        #=======================================================================
        # Init Label Control Ui Custom  setup
        #=======================================================================

        self._viewerControlUi.label.setVisible(False)
        self._viewerControlUi.checkShowPredictions.setVisible(False)
        self._viewerControlUi.checkShowSegmentation.setVisible(False)



        self._addNewLabel()
        self._addNewLabel()
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)



        #=======================================================================
        # Init labeling Drawer Ui Custom  setup
        #=======================================================================


        #labels for foreground and background
        self.labelingDrawerUi.labelListModel.makeRowPermanent(0)
        self.labelingDrawerUi.labelListModel.makeRowPermanent(1)
        self.labelingDrawerUi.labelListModel[0].name = "Foreground"
        self.labelingDrawerUi.labelListModel[1].name = "Background"
        self.labelingDrawerUi.labelListView.shrinkToMinimum()

        self.labelingDrawerUi.CountText.setReadOnly(True)



        #=======================================================================
        # Init Boxes Interface
        #=======================================================================

        #if not hasattr(self._labelControlUi, "boxListModel"):
        self.labelingDrawerUi.boxListModel=BoxListModel()
        self.labelingDrawerUi.boxListView.setModel(self.labelingDrawerUi.boxListModel)
        self.labelingDrawerUi.boxListModel.elementSelected.connect(self._onBoxSelected)
        #self.labelingDrawerUi.boxListModel.boxRemoved.connect(self._removeBox)


        self.labelingDrawerUi.DensityButton.clicked.connect(self.updateSum)

        mainwin=self
        self.density5d=OpReorderAxes(graph=self.op.graph, parent=self.op.parent) #

        self.density5d.Input.connect(self.op.Density)
        self.boxController=BoxController(mainwin.editor,self.density5d.Output,self.labelingDrawerUi.boxListModel)
        self.boxInterpreter=BoxInterpreter(mainwin.editor.navInterpret,mainwin.editor.posModel,self.boxController,mainwin.centralWidget())

        self.navigationInterpreterDefault=self.editor.navInterpret


        self._setUIParameters()
        self._connectUIParameters()

        self._loadViewBoxes()

        self.boxController.fixedBoxesChanged.connect(self._handleBoxConstraints)
        self.boxController.viewBoxesChanged.connect(self._changeViewBoxes)

        self.op.LabelPreviewer.sigma.setValue(self.op.opTrain.Sigma.value)
        self.op.opTrain.fixClassifier.setValue(False)

        # TODO: check if defer makes sense here!
        self.op.Density.notifyDirty(self._normalizePrediction, defer=True)
        self.op.LabelImages.notifyDirty(self._normalizeLayers, defer=True)

        self._updateSVROptions()

    def _connectUIParameters(self):

        #=======================================================================
        # Gui to operator connections
        #=======================================================================

        #Debug interface only available to advanced users
        self.labelingDrawerUi.DebugButton.pressed.connect(self._debug)
        self.labelingDrawerUi.boxListView.resetEmptyMessage("no boxes defined yet")
        self.labelingDrawerUi.SVROptions.currentIndexChanged.connect(self._updateSVROptions)
        self.labelingDrawerUi.CBox.valueChanged.connect(self._updateC)


        self.labelingDrawerUi.SigmaBox.valueChanged.connect(self._updateSigma)
        self.labelingDrawerUi.EpsilonBox.valueChanged.connect(self._updateEpsilon)
        self.labelingDrawerUi.MaxDepthBox.valueChanged.connect(self._updateMaxDepth)
        self.labelingDrawerUi.NtreesBox.valueChanged.connect(self._updateNtrees)

        #=======================================================================
        # Operators to Gui connections
        #=======================================================================

        self._registerOperatorsToGuiCallbacks()

        #=======================================================================
        # Initialize Values
        #=======================================================================

        self._updateSigma()
        self._updateNtrees()
        self._updateMaxDepth()

    def _registerOperatorsToGuiCallbacks(self):

        op=self.op.opTrain
        gui=self.labelingDrawerUi

        CallToGui(op.Ntrees,gui.NtreesBox.setValue)
        CallToGui(op.MaxDepth,gui.MaxDepthBox.setValue)
        CallToGui(op.C,gui.CBox.setValue)
        CallToGui(op.Sigma,gui.SigmaBox.setValue)
        CallToGui(op.Epsilon,gui.EpsilonBox.setValue)

        def _setoption(option):
            index=gui.SVROptions.findText(option)
            gui.SVROptions.setCurrentIndex(index)

        CallToGui(op.SelectedOption,_setoption)
        idx = self.op.current_view_index()

        


    def _setUIParameters(self):

        self.labelingDrawerUi.SigmaBox.setKeyboardTracking(False)
        self.labelingDrawerUi.CBox.setRange(0,1000)
        self.labelingDrawerUi.CBox.setKeyboardTracking(False)
        self.labelingDrawerUi.EpsilonBox.setKeyboardTracking(False)
        self.labelingDrawerUi.EpsilonBox.setDecimals(6)
        self.labelingDrawerUi.NtreesBox.setKeyboardTracking(False)
        self.labelingDrawerUi.MaxDepthBox.setKeyboardTracking(False)

        for option in self.op.options:
            if "req" in list(option.keys()):
                try:
                    for req in option["req"]:
                        importlib.import_module(req)
                except Exception as e:
                    continue
            #values=[v for k,v in option.items() if k not in ["gui", "req"]]
            self.labelingDrawerUi.SVROptions.addItem(option["method"], (option,))


        cache = self.op.classifier_cache
        if hasattr(cache._value, "__iter__") and len(self.op.classifier_cache._value) > 0:
        #if self.op.classifier_cache._value!=None and len(self.op.classifier_cache._value) > 0:
            #use parameters from cached classifier
            params = cache._value[0].get_params()
            Sigma = params["Sigma"]
            Epsilon = params["epsilon"]
            C = params["C"]
            Ntrees = params["ntrees"]
            MaxDepth = params["maxdepth"]
            _ind = self.labelingDrawerUi.SVROptions.findText(params["method"])

            #set opTrain from parameters
            self.op.opTrain.initInputs(params)



        else:
            #read parameters from opTrain Operator
            Sigma = self.op.opTrain.Sigma.value
            Epsilon = self.op.opTrain.Epsilon.value
            C = self.op.opTrain.C.value
            Ntrees = self.op.opTrain.Ntrees.value
            MaxDepth = self.op.opTrain.MaxDepth.value
            _ind = self.labelingDrawerUi.SVROptions.findText(self.op.opTrain.SelectedOption.value)

        #FIXME: quick fix recently introduced bug
        if type(Sigma)==list:
            Sigma=Sigma[0]
        self.labelingDrawerUi.SigmaBox.setValue(Sigma)
        self.labelingDrawerUi.EpsilonBox.setValue(Epsilon)
        self.labelingDrawerUi.CBox.setValue(C)
        self.labelingDrawerUi.NtreesBox.setValue(Ntrees)
        self.labelingDrawerUi.MaxDepthBox.setValue(MaxDepth)
        if _ind == -1:
            self.labelingDrawerUi.SVROptions.setCurrentIndex(0)
            self._updateSVROptions()
        else:
            self.labelingDrawerUi.SVROptions.setCurrentIndex(_ind)

        self._hideParameters()

    def _updateMaxDepth(self):
        self.op.opTrain.MaxDepth.setValue(self.labelingDrawerUi.MaxDepthBox.value())
    def _updateNtrees(self):
        self.op.opTrain.Ntrees.setValue(self.labelingDrawerUi.NtreesBox.value())

    def _hideParameters(self):
        _ind = self.labelingDrawerUi.SVROptions.currentIndex()
        option = self.labelingDrawerUi.SVROptions.itemData(_ind)[0]
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

    def _updateSigma(self):
        #if self._changedSigma:

        sigma = self._labelControlUi.SigmaBox.value()

        self.editor.crosshairController.setSigma(sigma)
        #2 * the maximal value of a gaussian filter, to allow some leeway for overlapping
        self.op.opTrain.Sigma.setValue(sigma)
        self.op.opUpperBound.Sigma.setValue(sigma)
        self.op.LabelPreviewer.sigma.setValue(sigma)

        #    self._changedSigma = False
        self._normalizeLayers()

    def _normalizeLayers(self, *args):
        upperBound = self.op.UpperBound.value
        self.upperBound = upperBound

        if hasattr(self, "labelPreviewLayer"):
            self.labelPreviewLayer.set_normalize(0, (0, upperBound))
        return


    def _normalizePrediction(self, *args):
        if hasattr(self, "predictionLayer") and hasattr(self, "upperBound"):
            self.predictionLayer.set_normalize(0,(0,self.upperBound))
        if hasattr(self, "uncertaintyLayer") and hasattr(self, "upperBound"):
            self.uncertaintyLayer.set_normalize(0,(0,self.upperBound))

    def _updateEpsilon(self):
        self.op.opTrain.Epsilon.setValue(self.labelingDrawerUi.EpsilonBox.value())

    def _updateSVROptions(self):
        index = self.labelingDrawerUi.SVROptions.currentIndex()
        option = self.labelingDrawerUi.SVROptions.itemData(index)[0]
        self.op.opTrain.SelectedOption.setValue(option["method"])

        self._hideFixable(option)

        self._hideParameters()

    def _hideFixable(self,option):
        if 'boxes' in option and option['boxes'] == False:
            self.labelingDrawerUi.boxListView.allowFixIcon=False
            self.labelingDrawerUi.boxListView.allowFixValues=False
        elif 'boxes' in option and option['boxes'] == True:
            self.labelingDrawerUi.boxListView.allowFixIcon=True



    def _handleBoxConstraints(self, constr):
        opTrain = self.op.opTrain
        id = self.op.current_view_index()
        vals = constr["values"]
        rois = constr["rois"]
        fixedClassifier = opTrain.fixClassifier.value
        assert len(vals) == len(rois)
        if opTrain.BoxConstraintRois.ready() and opTrain.BoxConstraintValues.ready():
            if opTrain.BoxConstraintValues[id].value != vals or opTrain.BoxConstraintRois[id].value != rois:
                opTrain.fixClassifier.setValue(True)
                opTrain.BoxConstraintRois[id].setValue(rois)
                #at this position so the change of a value can trigger a recomputation
                opTrain.fixClassifier.setValue(fixedClassifier)
                opTrain.BoxConstraintValues[id].setValue(vals)

        #boxes = self.boxController._currentBoxesList
    def _changeViewBoxes(self, boxes):
        id = self.op.current_view_index()
        self.op.boxViewer.rois[id].setValue(boxes["rois"])


    def _loadViewBoxes(self):
        op = self.op.opTrain
        fix = op.fixClassifier.value
        op.fixClassifier.setValue(True)

        idx = self.op.current_view_index()
        boxCounter = 0
        if self.op.boxViewer.rois.ready() and len(self.op.boxViewer.rois[idx].value) > 0:
            #if fixed boxes are existent, make column visible
            #self.labelingDrawerUi.boxListView._table.setColumnHidden(self.boxController.boxListModel.ColumnID.Fix, False)
            for roi in self.op.boxViewer.rois[idx].value:
                if type(roi) is not list or len(roi) is not 2:
                    continue
                self.boxController.addNewBox(roi[0], roi[1])
                #boxIndex = self.boxController.boxListModel.index(boxCounter, self.boxController.boxListModel.ColumnID.Fix)
                #iconIndex = self.boxController.boxListModel.index(boxCounter, self.boxController.boxListModel.ColumnID.FixIcon)
                #self.boxController.boxListModel.setData(boxIndex,val)
                boxCounter = boxCounter + 1


        if op.BoxConstraintRois.ready() and len(op.BoxConstraintRois[idx].value) > 0:
            #if fixed boxes are existent, make column visible
            self.labelingDrawerUi.boxListView._table.setColumnHidden(self.boxController.boxListModel.ColumnID.Fix, False)
            for constr in zip(op.BoxConstraintRois[idx].value, op.BoxConstraintValues[idx].value):
                roi, val = constr
                if type(roi) is not list or len(roi) is not 2:
                    continue
                self.boxController.addNewBox(roi[0], roi[1])
                boxIndex = self.boxController.boxListModel.index(boxCounter, self.boxController.boxListModel.ColumnID.Fix)
                iconIndex = self.boxController.boxListModel.index(boxCounter, self.boxController.boxListModel.ColumnID.FixIcon)
                self.boxController.boxListModel.setData(boxIndex,val)
                boxCounter = boxCounter + 1
        
        op.fixClassifier.setValue(fix)



    def _debug(self):
        go.db


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

        def _monkey_contextMenuEvent(s,event):
            from volumina.widgets.layercontextmenu import layercontextmenu
            idx = s.indexAt(event.pos())
            layer = s.model()[idx.row()]
            if layer.name=="Boxes":
                pass
                #FIXME: for the moment we do nothing here
            else:
                layercontextmenu(layer, s.mapToGlobal(event.pos()), s )



        import types
        self._viewerControlUi.viewerControls.layerWidget.contextMenuEvent = \
        types.MethodType(_monkey_contextMenuEvent,self._viewerControlUi.viewerControls.layerWidget)







    def _initShortcuts(self):
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcutGroupName = "Predictions"
        
        mgr.register( "p", ActionInfo( shortcutGroupName,
                                       "Toggle Prediction",
                                       "Toggle Prediction Layer Visibility",
                                       self._viewerControlUi.checkShowPredictions.click,
                                       self._viewerControlUi.checkShowPredictions,
                                       self._viewerControlUi.checkShowPredictions ) )

        mgr.register( "s", ActionInfo( shortcutGroupName,
                                       "Toggle Segmentation",
                                       "Toggle Segmentaton Layer Visibility",
                                       self._viewerControlUi.checkShowSegmentation.click,
                                       self._viewerControlUi.checkShowSegmentation,
                                       self._viewerControlUi.checkShowSegmentation ) )

        mgr.register( "l", ActionInfo( shortcutGroupName,
                                       "Toggle Live Prediction Mode",
                                       "Toggle Live",
                                       self.labelingDrawerUi.liveUpdateButton.toggle,
                                       self.labelingDrawerUi.liveUpdateButton,
                                       self.labelingDrawerUi.liveUpdateButton ) )

        shortcutGroupName = "Counting"

        mgr.register( "Del", ActionInfo( shortcutGroupName,
                                         "Delete a Box",
                                         "Delete a Box",
                                         self.boxController.deleteSelectedItems,
                                         self,
                                         None ) )

        try:
            from sitecustomize import Shortcuts
            mgr.register( "F5", ActionInfo( shortcutGroupName,
                                            "Activate Debug Mode",
                                            "Activate Debug Mode",
                                            self._debug,
                                            self,
                                            None ) )
        except ImportError as e:
            pass


    @traceLogged(traceLogger)
    def setupLayers(self):
        """
        Called by our base class when one of our data slots has changed.
        This function creates a layer for each slot we want displayed in the volume editor.
        """
        # Base class provides the label layer.
        layers = super(CountingGui, self).setupLayers()

        slots = {'Prediction': (self.op.Density, 0.5),
                 'LabelPreview': (self.op.LabelPreview, 1.0),
                 'Uncertainty': (self.op.UncertaintyEstimate, 1.0)}

        for name, (slot, opacity) in list(slots.items()):
            if slot.ready():
                layer = ColortableLayer(
                    LazyflowSource(slot),
                    colorTable=countingColorTable,
                    normalize=(0, self.upperBound))
                layer.name = name
                layer.opacity = opacity
                layer.visible = self.labelingDrawerUi.liveUpdateButton.isChecked()
                layers.append(layer)

        #Set LabelPreview-layer to True

        boxlabelsrc = LazyflowSinkSource(self.op.BoxLabelImages,self.op.BoxLabelInputs )
        boxlabellayer = ColortableLayer(boxlabelsrc, colorTable = self._colorTable16, direct = False)
        boxlabellayer.name = "Boxes"
        boxlabellayer.opacity = 1.0
        boxlabellayer.boxListModel = self.labelingDrawerUi.boxListModel
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

            inputLayer.shortcutRegistration = ( "i", ShortcutManager.ActionInfo(
                                                        "Prediction Layers",
                                                        "Bring Input To Top/Bottom",
                                                        "Bring Input To Top/Bottom",
                                                        toggleTopToBottom,
                                                        self.viewerControlWidget(),
                                                        inputLayer ) )
            layers.append(inputLayer)

        self.handleLabelSelectionChange()
        return layers

    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        """
        If enable
        """
        logger.debug("toggling interactive mode to '%r'" % checked)

        if checked:
            if not self.topLevelOperatorView.FeatureImages.ready() \
            or self.topLevelOperatorView.FeatureImages.meta.shape is None:
                self.labelingDrawerUi.liveUpdateButton.setChecked(False)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        if self.interactiveModeActive != checked:
            if checked:
                self.labelingDrawerUi.labelListView.allowDelete = False
        #        self.labelingDrawerUi.AddLabelButton.setEnabled( False )
            else:
                self.labelingDrawerUi.labelListView.allowDelete = True
        #        self.labelingDrawerUi.AddLabelButton.setEnabled( True )
        self.interactiveModeActive = checked
#        self.labelingDrawerUi.savePredictionsButton.setEnabled(not checked)
        self.topLevelOperatorView.FreezePredictions.setValue( not checked )
        self.labelingDrawerUi.liveUpdateButton.setChecked(checked)

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self._viewerControlUi.checkShowPredictions.setChecked( True )
            self.handleShowPredictionsClicked()

        # If we're changing modes, enable/disable our controls and other applets accordingly
        self.parentApplet.appletStateUpdateRequested()


    @traceLogged(traceLogger)
    def updateAllLayers(self, slot=None):
        super(CountingGui, self).updateAllLayers()
        for layer in self.layerstack:
            if layer.name == "LabelPreview":
                layer.visible = True
                self.labelPreviewLayer = layer
            if layer.name == "Prediction":
                self.predictionLayer = layer
            if layer.name == "Uncertainty":
                self.uncertaintyLayer = layer



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

        #self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self.labelingDrawerUi.liveUpdateButton.setEnabled(enabled)
        self._viewerControlUi.checkShowPredictions.setEnabled(enabled)
        self._viewerControlUi.checkShowSegmentation.setEnabled(enabled)

#    @pyqtSlot()
#    @traceLogged(traceLogger)
#    def onSavePredictionsButtonClicked(self):
#        """
#        The user clicked "Train and Predict".
#        Handle this event by asking the topLevelOperatorView for a prediction over the entire output region.
#        """
#        import warnings
#        warnings.warn("FIXME: Remove this function and just use the data export applet.")
#        # The button does double-duty as a cancel button while predictions are being stored
#        if self._currentlySavingPredictions:
#            self.predictionSerializer.cancel()
#        else:
#            # Compute new predictions as needed
#            predictionsFrozen = self.topLevelOperatorView.FreezePredictions.value
#            self.topLevelOperatorView.FreezePredictions.setValue(False)
#            self._currentlySavingPredictions = True
#
#            originalButtonText = "Full Volume Predict and Save"
#            #self.labelingDrawerUi.savePredictionsButton.setText("Cancel Full Predict")
#
#            @traceLogged(traceLogger)
#            def saveThreadFunc():
#                logger.info("Starting full volume save...")
#                # Disable all other applets
#                def disableAllInWidgetButName(widget, exceptName):
#                    for child in widget.children():
#                        if child.findChild( QPushButton, exceptName) is None:
#                            child.setEnabled(False)
#                        else:
#                            disableAllInWidgetButName(child, exceptName)
#
#                # Disable everything in our drawer *except* the cancel button
#                disableAllInWidgetButName(self.labelingDrawerUi, "savePredictionsButton")
#
#                # But allow the user to cancel the save
#                self.labelingDrawerUi.savePredictionsButton.setEnabled(True)
#
#                # First, do a regular save.
#                # During a regular save, predictions are not saved to the project file.
#                # (It takes too much time if the user only needs the classifier.)
#                self.shellRequestSignal(ShellRequest.RequestSave)
#
#                # Enable prediction storage and ask the shell to save the project again.
#                # (This way the second save will occupy the whole progress bar.)
#                self.predictionSerializer.predictionStorageEnabled = True
#                self.shellRequestSignal(ShellRequest.RequestSave)
#                self.predictionSerializer.predictionStorageEnabled = False
#
#                # Restore original states (must use events for UI calls)
#                self.thunkEventHandler.post(self.labelingDrawerUi.savePredictionsButton.setText, originalButtonText)
#                self.topLevelOperatorView.FreezePredictions.setValue(predictionsFrozen)
#                self._currentlySavingPredictions = False
#
#                # Re-enable our controls
#                def enableAll(widget):
#                    for child in widget.children():
#                        if isinstance( child, QWidget ):
#                            child.setEnabled(True)
#                            enableAll(child)
#                enableAll(self.labelingDrawerUi)
#
#                # Re-enable all other applets
#                logger.info("Finished full volume save.")
#
#            saveThread = threading.Thread(target=saveThreadFunc)
#            saveThread.start()

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
        new = list(map(mapf, self.labelListData))
        old = slot.value
        slot.setValue(_listReplace(old, new))

    def _onLabelRemoved(self, parent, start, end):
        super(CountingGui, self)._onLabelRemoved(parent, start, end)
        op = self.topLevelOperatorView
        for slot in (op.LabelNames, op.LabelColors, op.PmapColors):
            value = slot.value
            value.pop(start)
            slot.setValue(value)

    def _clearLabelListGui(self):
        """Remove rows until we have the right number"""
        while self._labelControlUi.labelListModel.rowCount() > 2:
            self._removeLastLabel()

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


    def _gui_setNavigation(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(True)

    def _gui_setBrushing(self):
#         self._labelControlUi.brushSizeComboBox.setEnabled(False)
#         self._labelControlUi.brushSizeCaption.setEnabled(False)
        # Make sure the paint button is pressed
        self._labelControlUi.paintToolButton.setChecked(True)
        # Show the brush size control and set its caption
        self._labelControlUi.brushSizeCaption.setText("Size:")
        # Make sure the GUI reflects the correct size
        #self._labelControlUi.brushSizeComboBox.setCurrentIndex(0)

    def _gui_setBox(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(False)

        #self._labelControlUi.boxToolButton.setChecked(True)


    def _onBoxChanged(self,parentFun, mapf):

        parentFun()
        new = list(map(mapf, self.labelListData))


    def _changeInteractionMode( self, toolId ):
        """
        Implement the GUI's response to the user selecting a new tool.
        """
        QApplication.restoreOverrideCursor()
        for v in self.editor.crosshairController._imageViews:
                    v._crossHairCursor.enabled=True


        # Uncheck all the other buttons
        for tool, button in list(self.toolButtons.items()):
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

        if hasattr(self._labelControlUi, "AddLabelButton"):
            self._labelControlUi.AddLabelButton.setEnabled(self.maxLabelNumber > self._labelControlUi.labelListModel.rowCount())
            self._labelControlUi.AddLabelButton.setText("Add Label")

        e = self._labelControlUi.labelListModel.rowCount() > 0
        self._gui_enableLabeling(e)

        # Update the applet bar caption
        if toolId == Tool.Navigation:
            # update GUI
            #self.editor.brushingModel.setBrushSize(0)
            self.editor.setNavigationInterpreter(NavigationInterpreter(self.editor.navCtrl))
            self._gui_setNavigation()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Paint:
            # If necessary, tell the brushing model to stop erasing
            if self.editor.brushingModel.erasing:
                self.editor.brushingModel.disableErasing()
            # Set the brushing size
            #this is done at the wrong time, drawnNumber has to be changed first before changing
            #interaction mode
            if self.editor.brushingModel.drawnNumber==1:
                brushSize = 1
                self.editor.brushingModel.setBrushSize(brushSize)

            # update GUI
            self._gui_setBrushing()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Erase:

            # If necessary, tell the brushing model to start erasing
            if not self.editor.brushingModel.erasing:
                self.editor.brushingModel.setErasing()
            # Set the brushing size
            eraserSize = self.brushSizes[self.eraserSizeIndex]
            self.editor.brushingModel.setBrushSize(eraserSize)
            # update GUI
            self._gui_setErasing()
            self.setCursor(Qt.ArrowCursor)

        elif toolId == Tool.Box:

            self.setCursor(Qt.CrossCursor)
            self._labelControlUi.labelListModel.clearSelectionModel()
            for v in self.editor.crosshairController._imageViews:
                v._crossHairCursor.enabled=False

            #self.setOverrideCursor(Qt.CrossCursor)
            #QApplication.setOverrideCursor(Qt.CrossCursor)
            self.editor.brushingModel.setBrushSize(0)
            self.editor.setNavigationInterpreter(self.boxInterpreter)
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
        self.labelingDrawerUi.boxListView.resetEmptyMessage("Draw the box on the image")


    def _onBoxSelected(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.boxListModel[row]))

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Box)


        self.boxController.selectBoxItem(row)


    def _onLabelSelected(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.labelListModel[row]))






        self.toolButtons[Tool.Paint].setEnabled(True)
        #elf.toolButtons[Tool.Box].setEnabled(False)
        self.toolButtons[Tool.Paint].click()

        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        brushColor = self._labelControlUi.labelListModel[row].brushColor()
        self.editor.brushingModel.setBrushColor( brushColor )

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Paint)


        if row==0: #foreground

            self._cachedBrushSizeIndex= self._labelControlUi.brushSizeComboBox.currentIndex()
            self._labelControlUi.SigmaBox.setEnabled(True)
            self._labelControlUi.brushSizeComboBox.setEnabled(False)
            self._labelControlUi.brushSizeComboBox.setCurrentIndex(0)
        else:
            if not hasattr(self, "_cachedBrushSizeIndex"):
                self._cachedBrushSizeIndex=0

            self._labelControlUi.SigmaBox.setEnabled(False)
            self._labelControlUi.brushSizeComboBox.setCurrentIndex(self._cachedBrushSizeIndex)



    def updateSum(self, *args, **kw):
        state = self.labelingDrawerUi.liveUpdateButton.isChecked()
        self.labelingDrawerUi.liveUpdateButton.setChecked(True)
        density = self.op.OutputSum[...].wait()
        strdensity = "{0:.2f}".format(density[0])
        self._labelControlUi.CountText.setText(strdensity)
        self.labelingDrawerUi.liveUpdateButton.setChecked(state)


#==============================================================================
#                   Colortable
#==============================================================================

countingColorTable = [
    QColor(0.0,0.0,127.0,0.0).rgba(),
    QColor(0.0,0.0,134.0,1.0).rgba(),
    QColor(0.0,0.0,141.0,3.0).rgba(),
    QColor(0.0,0.0,148.0,4.0).rgba(),
    QColor(0.0,0.0,154.0,6.0).rgba(),
    QColor(0.0,0.0,161.0,7.0).rgba(),
    QColor(0.0,0.0,168.0,9.0).rgba(),
    QColor(0.0,0.0,175.0,10.0).rgba(),
    QColor(0.0,0.0,182.0,12.0).rgba(),
    QColor(0.0,0.0,189.0,13.0).rgba(),
    QColor(0.0,0.0,196.0,15.0).rgba(),
    QColor(0.0,0.0,202.0,16.0).rgba(),
    QColor(0.0,0.0,209.0,18.0).rgba(),
    QColor(0.0,0.0,216.0,19.0).rgba(),
    QColor(0.0,0.0,223.0,21.0).rgba(),
    QColor(0.0,0.0,230.0,22.0).rgba(),
    QColor(0.0,0.0,237.0,24.0).rgba(),
    QColor(0.0,0.0,244.0,25.0).rgba(),
    QColor(0.0,0.0,250.0,27.0).rgba(),
    QColor(0.0,0.0,255.0,28.0).rgba(),
    QColor(0.0,0.0,255.0,30.0).rgba(),
    QColor(0.0,0.0,255.0,31.0).rgba(),
    QColor(0.0,5.0,255.0,33.0).rgba(),
    QColor(0.0,11.0,255.0,34.0).rgba(),
    QColor(0.0,17.0,255.0,36.0).rgba(),
    QColor(0.0,23.0,255.0,37.0).rgba(),
    QColor(0.0,29.0,255.0,39.0).rgba(),
    QColor(0.0,35.0,255.0,40.0).rgba(),
    QColor(0.0,41.0,255.0,42.0).rgba(),
    QColor(0.0,47.0,255.0,43.0).rgba(),
    QColor(0.0,53.0,255.0,45.0).rgba(),
    QColor(0.0,59.0,255.0,46.0).rgba(),
    QColor(0.0,65.0,255.0,48.0).rgba(),
    QColor(0.0,71.0,255.0,49.0).rgba(),
    QColor(0.0,77.0,255.0,51.0).rgba(),
    QColor(0.0,83.0,255.0,52.0).rgba(),
    QColor(0.0,89.0,255.0,54.0).rgba(),
    QColor(0.0,95.0,255.0,55.0).rgba(),
    QColor(0.0,101.0,255.0,57.0).rgba(),
    QColor(0.0,107.0,255.0,58.0).rgba(),
    QColor(0.0,113.0,255.0,60.0).rgba(),
    QColor(0.0,119.0,255.0,61.0).rgba(),
    QColor(0.0,125.0,255.0,63.0).rgba(),
    QColor(0.0,132.0,255.0,64.0).rgba(),
    QColor(0.0,138.0,255.0,66.0).rgba(),
    QColor(0.0,144.0,255.0,67.0).rgba(),
    QColor(0.0,150.0,255.0,69.0).rgba(),
    QColor(0.0,156.0,255.0,70.0).rgba(),
    QColor(0.0,162.0,255.0,72.0).rgba(),
    QColor(0.0,168.0,255.0,73.0).rgba(),
    QColor(0.0,174.0,255.0,75.0).rgba(),
    QColor(0.0,180.0,255.0,76.0).rgba(),
    QColor(0.0,186.0,255.0,78.0).rgba(),
    QColor(0.0,192.0,255.0,79.0).rgba(),
    QColor(0.0,198.0,255.0,81.0).rgba(),
    QColor(0.0,204.0,255.0,82.0).rgba(),
    QColor(0.0,210.0,255.0,84.0).rgba(),
    QColor(0.0,216.0,255.0,85.0).rgba(),
    QColor(0.0,222.0,252.0,87.0).rgba(),
    QColor(0.0,228.0,247.0,88.0).rgba(),
    QColor(4.0,234.0,242.0,90.0).rgba(),
    QColor(9.0,240.0,237.0,91.0).rgba(),
    QColor(13.0,246.0,232.0,93.0).rgba(),
    QColor(18.0,252.0,228.0,94.0).rgba(),
    QColor(23.0,255.0,223.0,96.0).rgba(),
    QColor(28.0,255.0,218.0,97.0).rgba(),
    QColor(33.0,255.0,213.0,99.0).rgba(),
    QColor(38.0,255.0,208.0,100.0).rgba(),
    QColor(43.0,255.0,203.0,102.0).rgba(),
    QColor(47.0,255.0,198.0,103.0).rgba(),
    QColor(52.0,255.0,193.0,105.0).rgba(),
    QColor(57.0,255.0,189.0,106.0).rgba(),
    QColor(62.0,255.0,184.0,108.0).rgba(),
    QColor(67.0,255.0,179.0,109.0).rgba(),
    QColor(72.0,255.0,174.0,111.0).rgba(),
    QColor(77.0,255.0,169.0,112.0).rgba(),
    QColor(82.0,255.0,164.0,114.0).rgba(),
    QColor(86.0,255.0,159.0,115.0).rgba(),
    QColor(91.0,255.0,155.0,117.0).rgba(),
    QColor(96.0,255.0,150.0,118.0).rgba(),
    QColor(101.0,255.0,145.0,120.0).rgba(),
    QColor(106.0,255.0,140.0,121.0).rgba(),
    QColor(111.0,255.0,135.0,123.0).rgba(),
    QColor(116.0,255.0,130.0,124.0).rgba(),
    QColor(120.0,255.0,125.0,126.0).rgba(),
    QColor(125.0,255.0,120.0,127.0).rgba(),
    QColor(130.0,255.0,116.0,129.0).rgba(),
    QColor(135.0,255.0,111.0,130.0).rgba(),
    QColor(140.0,255.0,106.0,132.0).rgba(),
    QColor(145.0,255.0,101.0,133.0).rgba(),
    QColor(150.0,255.0,96.0,135.0).rgba(),
    QColor(155.0,255.0,91.0,136.0).rgba(),
    QColor(159.0,255.0,86.0,138.0).rgba(),
    QColor(164.0,255.0,82.0,139.0).rgba(),
    QColor(169.0,255.0,77.0,141.0).rgba(),
    QColor(174.0,255.0,72.0,142.0).rgba(),
    QColor(179.0,255.0,67.0,144.0).rgba(),
    QColor(184.0,255.0,62.0,145.0).rgba(),
    QColor(189.0,255.0,57.0,147.0).rgba(),
    QColor(193.0,255.0,52.0,148.0).rgba(),
    QColor(198.0,255.0,47.0,150.0).rgba(),
    QColor(203.0,255.0,43.0,151.0).rgba(),
    QColor(208.0,255.0,38.0,153.0).rgba(),
    QColor(213.0,255.0,33.0,154.0).rgba(),
    QColor(218.0,255.0,28.0,156.0).rgba(),
    QColor(223.0,255.0,23.0,157.0).rgba(),
    QColor(228.0,255.0,18.0,159.0).rgba(),
    QColor(232.0,255.0,13.0,160.0).rgba(),
    QColor(237.0,255.0,9.0,162.0).rgba(),
    QColor(242.0,250.0,4.0,163.0).rgba(),
    QColor(247.0,244.0,0.0,165.0).rgba(),
    QColor(252.0,239.0,0.0,166.0).rgba(),
    QColor(255.0,233.0,0.0,168.0).rgba(),
    QColor(255.0,227.0,0.0,169.0).rgba(),
    QColor(255.0,222.0,0.0,171.0).rgba(),
    QColor(255.0,216.0,0.0,172.0).rgba(),
    QColor(255.0,211.0,0.0,174.0).rgba(),
    QColor(255.0,205.0,0.0,175.0).rgba(),
    QColor(255.0,200.0,0.0,177.0).rgba(),
    QColor(255.0,194.0,0.0,178.0).rgba(),
    QColor(255.0,188.0,0.0,180.0).rgba(),
    QColor(255.0,183.0,0.0,181.0).rgba(),
    QColor(255.0,177.0,0.0,183.0).rgba(),
    QColor(255.0,172.0,0.0,184.0).rgba(),
    QColor(255.0,166.0,0.0,186.0).rgba(),
    QColor(255.0,160.0,0.0,187.0).rgba(),
    QColor(255.0,155.0,0.0,189.0).rgba(),
    QColor(255.0,149.0,0.0,190.0).rgba(),
    QColor(255.0,144.0,0.0,192.0).rgba(),
    QColor(255.0,138.0,0.0,193.0).rgba(),
    QColor(255.0,132.0,0.0,195.0).rgba(),
    QColor(255.0,127.0,0.0,196.0).rgba(),
    QColor(255.0,121.0,0.0,198.0).rgba(),
    QColor(255.0,116.0,0.0,199.0).rgba(),
    QColor(255.0,110.0,0.0,201.0).rgba(),
    QColor(255.0,105.0,0.0,202.0).rgba(),
    QColor(255.0,99.0,0.0,204.0).rgba(),
    QColor(255.0,93.0,0.0,205.0).rgba(),
    QColor(255.0,88.0,0.0,207.0).rgba(),
    QColor(255.0,82.0,0.0,208.0).rgba(),
    QColor(255.0,77.0,0.0,210.0).rgba(),
    QColor(255.0,71.0,0.0,211.0).rgba(),
    QColor(255.0,65.0,0.0,213.0).rgba(),
    QColor(255.0,60.0,0.0,214.0).rgba(),
    QColor(255.0,54.0,0.0,216.0).rgba(),
    QColor(255.0,49.0,0.0,217.0).rgba(),
    QColor(255.0,43.0,0.0,219.0).rgba(),
    QColor(255.0,37.0,0.0,220.0).rgba(),
    QColor(255.0,32.0,0.0,222.0).rgba(),
    QColor(255.0,26.0,0.0,223.0).rgba(),
    QColor(255.0,21.0,0.0,225.0).rgba(),
    QColor(250.0,15.0,0.0,226.0).rgba(),
    QColor(244.0,10.0,0.0,228.0).rgba(),
    QColor(237.0,4.0,0.0,229.0).rgba(),
    QColor(230.0,0.0,0.0,231.0).rgba(),
    QColor(223.0,0.0,0.0,232.0).rgba(),
    QColor(216.0,0.0,0.0,234.0).rgba(),
    QColor(209.0,0.0,0.0,235.0).rgba(),
    QColor(202.0,0.0,0.0,237.0).rgba(),
    QColor(196.0,0.0,0.0,238.0).rgba(),
    QColor(189.0,0.0,0.0,240.0).rgba(),
    QColor(182.0,0.0,0.0,241.0).rgba(),
    QColor(175.0,0.0,0.0,243.0).rgba(),
    QColor(168.0,0.0,0.0,244.0).rgba(),
    QColor(161.0,0.0,0.0,246.0).rgba(),
    QColor(154.0,0.0,0.0,247.0).rgba(),
    QColor(148.0,0.0,0.0,249.0).rgba(),
    QColor(141.0,0.0,0.0,250.0).rgba(),
    QColor(134.0,0.0,0.0,252.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba(),
    QColor(127.0,0.0,0.0,255.0).rgba()]
