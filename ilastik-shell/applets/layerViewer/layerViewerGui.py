from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import ArraySource, LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource

import labelListModel
from labelListModel import LabelListModel

from lazyflow.graph import MultiInputSlot, MultiOutputSlot, OperatorWrapper
from lazyflow.operators import OpSingleChannelSelector, OpMultiArraySlicer2, Op1ToMulti, OpMultiInputConcatenater, OpTransposeSlots

from functools import partial
import os
import utility # This is the ilastik shell utility module
import numpy
from utility import bind

from volumina.adaptors import Op5ifyer

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import Tracer

class LayerViewerGui(QMainWindow):
    """
    Implements an applet GUI whose central widget is a VolumeEditor 
      and whose layer controls simply contains a layer list widget.
    Intended to be used as a subclass for applet GUI objects.
    
    Provides: - Central widget (viewer)
              - View Menu
              - Layer controls
              
    Does NOT provide an applet drawer widget.
    """


    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawers(self):
        return ['Viewer', QWidget()]

    def menuWidget( self ):
        return self.menuBar

    def viewerControlWidget(self):
        return self._viewerControlWidget

    def setImageIndex(self, index):
        self._setImageIndex(index)

    ###########################################
    ###########################################

    def __init__(self, operators, layerSetupCallback=None):
        """
        Args:
            dataProviderSlot - A list of slots that we'll listen for changes on.
                               Each must be a multislot with level=1 or level=2.
                               The first index in the multislot is the image index. 
            layerSetupCallback: a function that produces all layers for the GUI.
        """
        with Tracer(traceLogger):
            super(LayerViewerGui, self).__init__()
    
            self.dataProviderSlots = []
            dataProviderSlots = []
            for op in operators:
                dataProviderSlots += op.outputs.values()
    
            for slot in dataProviderSlots:
                if slot.level == 1:
                    # The user gave us a slot that is indexed as slot[image]
                    # Wrap the operator so it has the right level.  Indexed as: slot[image][0]
                    opPromoteInput = OperatorWrapper( Op1ToMulti(graph=slot.operator.graph) )
                    opPromoteInput.Input.connect(slot)
                    slot = opPromoteInput.Outputs
    
                # Each slot should now be indexed as slot[image][sub_index]
                assert slot.level == 2
                self.dataProviderSlots.append( slot )
    
            # If the user didn't provide a layer setup function for us,
            #  we assume he's using a subclass of this GUI.
            self.layerSetupCallback = layerSetupCallback
            if self.layerSetupCallback is None:
                self.layerSetupCallback = self.setupLayers
    
            self.menuBar = QMenuBar()
            
            self.initAppletDrawerUi() # Default implementation loads a blank drawer.
            self.initCentralUic()
            self.initViewerControlUi()
            
            self.layerstack = LayerStackModel()
            self.initEditor()
            
            self.imageIndex = -1
            
            def handleDatasetInsertion(slot, imageIndex):
                if self.imageIndex == -1 and self.areProvidersInSync():
                    self.setImageIndex( imageIndex )
            
            for provider in self.dataProviderSlots:
                provider.notifyInserted( bind( handleDatasetInsertion ) )
            
            def handleDatasetRemoval(slot, index, finalsize):
                if finalsize == 0:
                    # Clear everything
                    self.setImageIndex(-1)
                elif index == self.imageIndex:
                    # Our currently displayed image is being removed.
                    # Switch to the first image (unless that's the one being removed!)
                    newIndex = 0
                    if index == newIndex:
                        newIndex = 1
                    self.setImageIndex(newIndex)
                
            for provider in self.dataProviderSlots:
                provider.notifyRemove( bind( handleDatasetRemoval ) )

    def setupLayers(self):
        # Users of this class have two choices:
        # 1) Provide a callback for setupLayers via the __init__ function argument
        # 2) Subclass this GUI class and override the setupLayers() function.
        raise NotImplementedError("No setup layers function defined.  See comment above.")

    def _setImageIndex(self, imageIndex):
        with Tracer(traceLogger):
            if self.imageIndex != -1:
                for provider in self.dataProviderSlots:
                    # We're switching datasets.  Unsubscribe from the old one's notifications.
                    provider[self.imageIndex].unregisterInserted( bind(self.handleLayerInsertion) )
                    provider[self.imageIndex].unregisterRemove( bind(self.handleLayerRemoval) )
    
            # Clear the GUI
            self.layerstack.clear()
    
            self.imageIndex = imageIndex
            
            # Don't repopulate the GUI if there isn't a current dataset.  Stop now. 
            if imageIndex is -1:
                return
    
            # Update the GUI for all layers in the current dataset
            self.updateAllLayers()
    
            # For layers that already exist, subscribe to ready notifications
            for provider in self.dataProviderSlots:
                for slotIndex, slot in enumerate(provider):
                    slot.notifyReady( bind(self.updateAllLayers) )
            
            # Make sure we're notified if a layer is inserted in the future so we can subscribe to its ready notifications
            for provider in self.dataProviderSlots:
                provider[self.imageIndex].notifyInserted( bind(self.handleLayerInsertion) )
                provider[self.imageIndex].notifyRemove( bind(self.handleLayerRemoval) )

    def handleLayerInsertion(self, slot, slotIndex):
        """
        The multislot providing our layers has a new item.
        Make room for it in the layer GUI and subscribe to updates.
        """
        # When the slot is ready, we'll replace the blank layer with real data
        slot[slotIndex].notifyReady( bind(self.updateAllLayers) )
    
    def handleLayerRemoval(self, slot, slotIndex):
        """
        An item is about to be removed from the multislot that is providing our layers.
        Remove the layer from the GUI.
        """
        with Tracer(traceLogger):
            self.updateAllLayers()

    def generateAlphaModulatedLayersFromChannels(self, slot):
        # TODO
        assert False

    def createStandardLayerFromSlot(self, slot):
        """
        Generate a volumina layer using the given slot.
        Choose between grayscale or RGB depending on the number of channels.
        """
        with Tracer(traceLogger):
            # Examine channel dimension to determine Grayscale vs. RGB
            shape = slot.meta.shape
            channelAxisIndex = slot.meta.axistags.index('c')
            numChannels = shape[channelAxisIndex]
            
            assert numChannels <= 3, "Can't display a standard layer with more than three channels."
            
            if numChannels == 1:
                source = LazyflowSource(slot)
                layer = GrayscaleLayer(source)
    
            if numChannels >= 2:
                redProvider = OpSingleChannelSelector(graph=slot.graph)
                redProvider.Input.connect(slot)
                redProvider.Index.setValue( 0 )
                redSource = LazyflowSource( redProvider.Output )
    
                greenProvider = OpSingleChannelSelector(graph=slot.graph)
                greenProvider.Input.connect(slot)
                greenProvider.Index.setValue( 1 )
                greenSource = LazyflowSource( greenProvider.Output )
                            
                if numChannels == 3:
                    blueProvider = OpSingleChannelSelector(graph=slot.graph)
                    blueProvider.Input.connect(slot)
                    blueProvider.Index.setValue( 2 )
                    blueSource = LazyflowSource( blueProvider.Output )
                else:
                    blueSource = None
    
                layer = RGBALayer(red = redSource, green = greenSource, blue = blueSource)
    
            return layer

    def areProvidersInSync(self):
        with Tracer(traceLogger):
            numImages = len(self.dataProviderSlots[0])
            for slot in self.dataProviderSlots:
                if len(slot) != numImages:
                    return False        
            return True

    def updateAllLayers(self):
        with Tracer(traceLogger):
            # Check to make sure all layers are in sync
            # (During image insertions, outputs are resized one at a time.)
            if not self.areProvidersInSync():
                return
            
            # Ask the subclass for the updated layer list
            newGuiLayers = self.layerSetupCallback(self.imageIndex)
            
            # Testing: Simply remove everything and add it all back
            # TODO: Selectively remove/add rows based on what actually changed.
            self.layerstack.clear()
    
            # Reinitialize the editor datashape with the first ready slot we've got
            newDataShape = None
            for provider in self.dataProviderSlots:
                for i, slot in enumerate(provider[self.imageIndex]):
                    if newDataShape is None and slot.ready():
                        # Use an Op5ifyer adapter to transpose the shape for us.
                        op5 = Op5ifyer( graph=slot.graph )
                        op5.input.connect( slot )
                        newDataShape = op5.output.meta.shape

                        # We just needed the operator to determine the transposed shape.
                        # Disconnect it so it can be garbage collected.
                        op5.input.disconnect()
            if newDataShape is not None and self.editor.dataShape != newDataShape:
                self.editor.dataShape = newDataShape
    
            for index, layer in enumerate(newGuiLayers):
                layer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )
                self.layerstack.insert( index, layer )
        
    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        """
        with Tracer(traceLogger):
            p = os.path.split(__file__)[0]+'/'
            if p == "/": p = "."+p
            self._viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def initAppletDrawerUi(self):
        """
        By default, this base class provides a blank applet drawer.
        Override this in a subclass to get a real applet drawer.
        """
        with Tracer(traceLogger):
            # Load the ui file (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            self._drawer = uic.loadUi(localDir+"/drawer.ui")
            
            def enableDrawerControls(enabled):
                pass
            # Expose the enable function with the name the shell expects
            self._drawer.enableControls = enableDrawerControls
    
    def getAppletDrawerUi(self):
        return self._drawer

    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        with Tracer(traceLogger):
            # Load the ui file into this class (find it in our own directory)
            localDir = os.path.split(__file__)[0]
            uic.loadUi(localDir+"/centralWidget.ui", self)
                
            def toggleDebugPatches(show):
                self.editor.showDebugPatches = show
            def fitToScreen():
                shape = self.editor.posModel.shape
                for i, v in enumerate(self.editor.imageViews):
                    s = list(shape)
                    del s[i]
                    v.changeViewPort(v.scene().data2scene.mapRect(QRectF(0,0,*s)))  
                    
            def fitImage():
                if hasattr(self.editor, '_lastImageViewFocus'):
                    self.editor.imageViews[self.editor._lastImageViewFocus].fitImage()
                    
            def restoreImageToOriginalSize():
                if hasattr(self.editor, '_lastImageViewFocus'):
                    self.editor.imageViews[self.editor._lastImageViewFocus].doScaleTo()
                        
            def rubberBandZoom():
                if hasattr(self.editor, '_lastImageViewFocus'):
                    if not self.editor.imageViews[self.editor._lastImageViewFocus]._isRubberBandZoom:
                        self.editor.imageViews[self.editor._lastImageViewFocus]._isRubberBandZoom = True
                        self.editor.imageViews[self.editor._lastImageViewFocus]._cursorBackup = self.editor.imageViews[self.editor._lastImageViewFocus].cursor()
                        self.editor.imageViews[self.editor._lastImageViewFocus].setCursor(Qt.CrossCursor)
                    else:
                        self.editor.imageViews[self.editor._lastImageViewFocus]._isRubberBandZoom = False
                        self.editor.imageViews[self.editor._lastImageViewFocus].setCursor(self.editor.imageViews[self.editor._lastImageViewFocus]._cursorBackup)
                    
            def hideHud():
                hide = not self.editor.imageViews[0]._hud.isVisible()
                for i, v in enumerate(self.editor.imageViews):
                    v.setHudVisible(hide)
                    
            def toggleSelectedHud():
                if hasattr(self.editor, '_lastImageViewFocus'):
                    self.editor.imageViews[self.editor._lastImageViewFocus].toggleHud()
                    
            def centerAllImages():
                for i, v in enumerate(self.editor.imageViews):
                    v.centerImage()
                    
            def centerImage():
                if hasattr(self.editor, '_lastImageViewFocus'):
                    self.editor.imageViews[self.editor._lastImageViewFocus].centerImage()
                    self.actionOnly_for_current_view.setEnabled(True)
            
            self.actionCenterAllImages.triggered.connect(centerAllImages)
            self.actionCenterImage.triggered.connect(centerImage)
            self.actionToggleAllHuds.triggered.connect(hideHud)
            self.actionToggleSelectedHud.triggered.connect(toggleSelectedHud)
            self.actionShowDebugPatches.toggled.connect(toggleDebugPatches)
            self.actionFitToScreen.triggered.connect(fitToScreen)
            self.actionFitImage.triggered.connect(fitImage)
            self.actionReset_zoom.triggered.connect(restoreImageToOriginalSize)
            self.actionRubberBandZoom.triggered.connect(rubberBandZoom)
                
    def initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """
        with Tracer(traceLogger):
            self.editor = VolumeEditor(self.layerstack)
    
            self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
            self.editor.setInteractionMode( 'navigation' )
            self.volumeEditorWidget.init(self.editor)
            
            # The editor's layerstack is in charge of which layer movement buttons are enabled
            model = self.editor.layerStack
            model.canMoveSelectedUp.connect(self._viewerControlWidget.UpButton.setEnabled)
            model.canMoveSelectedDown.connect(self._viewerControlWidget.DownButton.setEnabled)
            model.canDeleteSelected.connect(self._viewerControlWidget.DeleteButton.setEnabled)     
    
            # Connect our layer movement buttons to the appropriate layerstack actions
            self._viewerControlWidget.layerWidget.init(model)
            self._viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
            self._viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
            self._viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)
            
            self.editor._lastImageViewFocus = 0

    def setIconToViewMenu(self):
        """
        In the "Only for Current View" menu item of the View menu, 
        show the user which axis is the current one by changing the menu item icon.
        """
        with Tracer(traceLogger):
            self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))

    def enableControls(self, enabled):
        """
        Enable or disable all of the controls in this applet's central widget.
        """
        # All the controls in our GUI
        controlList = [ self.menuBar,
                        self.volumeEditorWidget,
                        self._viewerControlWidget.UpButton,
                        self._viewerControlWidget.DownButton,
                        self._viewerControlWidget.DeleteButton ]

        # Enable/disable all of them
        for control in controlList:
            control.setEnabled(enabled)






























