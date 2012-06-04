from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import ArraySource, LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource

import labelListModel
from labelListModel import LabelListModel

from lazyflow.graph import MultiInputSlot, MultiOutputSlot
from lazyflow.operators import OpSingleChannelSelector, OpMultiArraySlicer2

from functools import partial
import os
import utility # This is the ilastik shell utility module
import numpy
from utility import bind

class LayerType():
    # Enum for layer types we support (provided via input metadata)
    Standard = 0 # Default
    AlphaModulated = 1
    ColorTable = 2

class GenericViewerGui(QMainWindow):
    """
    Implements an applet GUI whose central widget is a VolumeEditor 
      and whose layer controls simply contains a layer list widget.
    Intended to be used as a subclass for applet GUI objects.
    
    Provides: - Central widget (viewer)
              - View Menu
              - Layer controls
              
    Does NOT provide an applet drawer widget.
    """
    
    def __init__(self, dataProviderMultiMultiSlot, layerNameSlot=None):
        """
        
        """
        super(GenericViewerGui, self).__init__()

        # Constants
        self.ColorTableSize = 256
        self.DefaultColorTable = self.createDefaultColorTable(self.ColorTableSize)

        assert isinstance(dataProviderMultiMultiSlot, (MultiInputSlot, MultiOutputSlot))
        assert dataProviderMultiMultiSlot.level == 2
        self.datasetMultiSlot = dataProviderMultiMultiSlot

        self.menuBar = QMenuBar()
        
        self.initAppletDrawerUi() # Default implementation loads a blank drawer.
        self.initCentralUic()
        self.initViewerControlUi()
        
        self.layerstack = LayerStackModel()
        self.initEditor()
        
        self.currentDatasetSlot = None # The multislot we're currently getting layers from.
        
        # This list maps from layer slot indexes to layer GUI indexes
        # Uninitialized slots map to 'None'
        self.slotIndexToGuiIndex = []
        
        def handleDatasetInsertion(slot, imageIndex):
            if self.currentDatasetSlot is None:
                self.setImageIndex( imageIndex )
        
        self.datasetMultiSlot.notifyInserted( bind( handleDatasetInsertion ) )
        
        def handleDatasetRemoval(slot, index, finalsize):
            if finalsize == 0:
                # Clear everything
                self.setImageIndex(-1)
            elif index == self.currentDatasetIndex:
                # Our currently displayed image is being removed.
                # Switch to the first image (unless that's the one being removed!)
                newIndex = 0
                if index == newIndex:
                    newIndex = 1
                self.setImageIndex(newIndex)
            
        self.datasetMultiSlot.notifyRemove( bind( handleDatasetRemoval ) )

    def setImageIndex(self, imageIndex):
        if self.currentDatasetSlot is not None:
            # We're switching datasets.  Unsubscribe from the old one's notifications.
            self.currentDatasetSlot.unregisterInserted( bind(self.handleLayerInsertion) )
            self.currentDatasetSlot.unregisterRemove( bind(self.handleLayerRemoval) )

        # Clear the GUI
        self.layerstack.clear()
        self.slotIndexToGuiIndex = []

        self.currentDatasetIndex = imageIndex
        
        # Don't repopulate the GUI if there isn't a current dataset.  Stop now. 
        if imageIndex is -1:
            self.currentDatasetSlot = None
            return

        # Each subslot in the currentDatasetSlot provides a layer
        self.currentDatasetSlot = self.datasetMultiSlot[imageIndex]
        assert isinstance(self.currentDatasetSlot, (MultiInputSlot, MultiOutputSlot))

        # Update the GUI for all layers in the current dataset
        for index, slot in enumerate(self.currentDatasetSlot):
            if slot.configured():
                self.slotIndexToGuiIndex.append(index)
                self.updateLayer(slot)
            else:
                self.slotIndexToGuiIndex.append(-1)
        
        # Subscribe to any future layer insertions/removals in the current dataset
        self.currentDatasetSlot.notifyInserted( bind(self.handleLayerInsertion) )
        self.currentDatasetSlot.notifyRemove( bind(self.handleLayerRemoval) )

    def handleLayerInsertion(self, slot, slotIndex):
        """
        The multislot providing our layers has a new item.
        Make room for it in the layer GUI and subscribe to updates.
        """
        assert slot == self.currentDatasetSlot
        
        # The newly inserted slot isn't initialized yet
        self.slotIndexToGuiIndex.insert( slotIndex, None )
        
        # When the slot is ready, we'll replace the blank layer with real data
        slot[slotIndex].notifyMetaChanged( self.updateLayer )
    
    def handleLayerRemoval(self, slot, slotIndex):
        """
        An item is about to be removed from the multislot that is providing our layers.
        Remove the layer from the GUI.
        """
        guiIndex = self.slotIndexToGuiIndex[slotIndex]
        if guiIndex is not None:
            self.layerstack.removeRow(guiIndex)
        self.slotIndexToGuiIndex.pop(slotIndex)

    def updateLayer(self, slot):
        # Can't update if the slot doesn't have data
        if not slot.configured():
            return
        
        slotIndex = list(self.currentDatasetSlot).index(slot)
        guiIndex = self.slotIndexToGuiIndex[slotIndex]

        # If our gui already has a layer for this slot, just remove the layer.
        # We're about to replace it, so the gui index will not change
        if guiIndex is not None:
            self.layerstack.removeRow(guiIndex)
        else:
            # Figure out which gui index this layer will take.
            guiIndex = 0
            for si, gi in enumerate( self.slotIndexToGuiIndex[:slotIndex] ):
                if gi is not None:
                    guiIndex = gi + 1

            # Assign the gui index for this slot
            self.slotIndexToGuiIndex[slotIndex] = guiIndex

            # Increment the gui index of all subsequent layers that come after our new layer
            for si, gi in enumerate( self.slotIndexToGuiIndex[slotIndex+1:] ):
                if gi != None:
                    gi += 1

        # If this is the first layer in the GUI, initialize the editor shape
        if self.layerstack.rowCount() == 0:
            self.editor.dataShape = slot.meta.shape

        # Now create a layer with the slot data
        # TODO: Replace the color selection mechanism with something better
        # TODO: Use an Op5ifyer to make sure the layer will be displayed correctly in volumina
        
        # Determine the type of layer to make        
        try:
            layertype = slot.meta.layertype
        except KeyError:
            layertype = LayerType.Standard

        # Create the layer
        if layertype == LayerType.Standard:
            # Examine channel dimension to determine Grayscale vs. RGB
            shape = slot.meta.shape
            channelAxisIndex = slot.meta.axistags.index('c')
            numChannels = shape[channelAxisIndex]
            
            assert numChannels <= 3, "Can't display a layer with more than three channels."
            
            if numChannels == 1:
                source = LazyflowSource(slot)
                layer = GrayscaleLayer(source)

            if numChannels >= 2:
                redSource = OpSingleChannelSelector(graph=self.datasetMultiSlot.operator.graph)
                redSource.Input.connect(slot)
                redSource.Index.setValue( 0 )

                greenSource = OpSingleChannelSelector(graph=self.datasetMultiSlot.operator.graph)
                greenSource.Input.connect(slot)
                greenSource.Index.setValue( 1 )
                            
                if numChannels == 3:
                    blueSource = OpSingleChannelSelector(graph=self.datasetMultiSlot.operator.graph)
                    blueSource.Input.connect(slot)
                    blueSource.Index.setValue( 2 )
                else:
                    blueSource = None

                layer = RGBALayer(red = redSource, green = greenSource, blue = blueSource)
            
        elif layertype == LayerType.AlphaModulated:
            # Must be a single-channel image 
            shape = slot.meta.shape
            channelAxisIndex = slot.meta.axistags.index('c')
            assert shape[channelAxisIndex] == 1

            # Choose the next color from our default color table
            assert slotIndex < len(self.DefaultColorTable)
            color = self.DefaultColorTable[slotIndex]

            source = LazyflowSource(slot)
            layer = AlphaModulatedLayer(source, tintColor=color, normalize = None )
            layer.opacity = 1.0 # (Since this is alpha-modulated, other layers will be visible anyway)

        elif layertype == LayerType.ColorTable:
            # Must be a single-channel image 
            shape = slot.meta.shape
            channelAxisIndex = slot.meta.axistags.index('c')
            assert shape[channelAxisIndex] == 1

            # Use the default color table
            # TODO: Allow the user to specify a color table in the metadata....
            source = LazyflowSource(slot)
            layer = ColortableLayer(source, self.DefaultColorTable )
        else:
            assert False, "Unknown layertype: " + str(layertype)

        try:
            layerName = slot.meta.name
        except KeyError:
            layerName = "Layer {}".format(slotIndex)

        layer.name = layerName
        layer.visible = True
        layer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )

        # Add the new layer to the GUI stack
        self.layerstack.insert( guiIndex, layer )
        
    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        """
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self.viewerControlWidget = uic.loadUi(p+"viewerControls.ui")

    def initAppletDrawerUi(self):
        """
        By default, this base class provides a blank applet drawer.
        Override this in a subclass to get a real applet drawer.
        """
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
        self.editor = VolumeEditor(self.layerstack)

        self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        self.editor.setInteractionMode( 'navigation' )
        self.volumeEditorWidget.init(self.editor)
        
        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack
        model.canMoveSelectedUp.connect(self.viewerControlWidget.UpButton.setEnabled)
        model.canMoveSelectedDown.connect(self.viewerControlWidget.DownButton.setEnabled)
        model.canDeleteSelected.connect(self.viewerControlWidget.DeleteButton.setEnabled)     

        # Connect our layer movement buttons to the appropriate layerstack actions
        self.viewerControlWidget.layerWidget.init(model)
        self.viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
        self.viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
        self.viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)
        
        self.editor._lastImageViewFocus = 0

    def setIconToViewMenu(self):
        """
        In the "Only for Current View" menu item of the View menu, 
        show the user which axis is the current one by changing the menu item icon.
        """
        self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))

    def enableControls(self, enabled):
        """
        Enable or disable all of the controls in this applet's central widget.
        """
        # All the controls in our GUI
        controlList = [ self.menuBar,
                        self.volumeEditorWidget,
                        self.viewerControlWidget.UpButton,
                        self.viewerControlWidget.DownButton,
                        self.viewerControlWidget.DeleteButton ]

        # Enable/disable all of them
        for control in controlList:
            control.setEnabled(enabled)

    def createDefaultColorTable(self, colorTableSize):
        c = []
        # Create some standard colors for the first 16 entries
        c.append(QColor(0, 0, 255))
        c.append(QColor(255, 255, 0))
        c.append(QColor(255, 0, 0))
        c.append(QColor(0, 255, 0))
        c.append(QColor(0, 255, 255))
        c.append(QColor(255, 0, 255))
        c.append(QColor(255, 105, 180)) #hot pink
        c.append(QColor(102, 205, 170)) #dark aquamarine
        c.append(QColor(165,  42,  42)) #brown        
        c.append(QColor(0, 0, 128))     #navy
        c.append(QColor(255, 165, 0))   #orange
        c.append(QColor(173, 255,  47)) #green-yellow
        c.append(QColor(128,0, 128))    #purple
        c.append(QColor(192, 192, 192)) #silver
        c.append(QColor(240, 230, 140)) #khaki
        c.append(QColor(69, 69, 69))    # dark grey
        
        # Choose random colors for remaining entries
        while len(c) < colorTableSize:
            c.append( QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255)) )
        
        return c






























