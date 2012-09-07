import numpy

from PyQt4.QtCore import QRectF, Qt
from PyQt4.QtGui import *
from PyQt4 import uic

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor

from lazyflow.graph import OperatorWrapper
from lazyflow.operators import OpSingleChannelSelector, Op1ToMulti

import os
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted

from volumina.adaptors import Op5ifyer

from volumina.clickReportingInterpreter import ClickReportingInterpreter

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)
from lazyflow.tracer import traceLogged, Tracer

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
        return [('Viewer', QWidget())]

    def menus( self ):
        return [self.menuView] # From the .ui file

    def viewerControlWidget(self):
        return self.__viewerControlWidget

    def setImageIndex(self, index):
        self._setImageIndex(index)
        
    def reset(self):
        # Remove all layers
        self.layerstack.clear()

    ###########################################
    ###########################################

    @traceLogged(traceLogger)
    def __init__(self, dataProviderSlots, layerSetupCallback=None):
        """
        Args:
            dataProviderSlot - A list of slots that we'll listen for changes on.
                               Each must be a multislot with level=1 or level=2.
                               The first index in the multislot is the image index. 
            layerSetupCallback: a function that produces all layers for the GUI.
        """
        super(LayerViewerGui, self).__init__()

        self.threadRouter = ThreadRouter(self) # For using @threadRouted

        self.dataProviderSlots = []
#            dataProviderSlots = []
#            for op in operators:
#                dataProviderSlots += op.outputs.values()

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

        self.layerstack = LayerStackModel()

        self.initAppletDrawerUi() # Default implementation loads a blank drawer.
        self.initCentralUic()
        self.__viewerControlWidget = None
        self.initViewerControlUi()
        
        self.initEditor()
        
        self.imageIndex = -1
        self.lastUpdateImageIndex = -1
        
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

    def setupLayers(self, imageIndex):
        # Users of this class have two choices:
        # 1) Provide a callback for setupLayers via the __init__ function argument
        # 2) Subclass this GUI class and override the setupLayers() function.
        raise NotImplementedError("No setup layers function defined.  See comment above.")

    @traceLogged(traceLogger)
    def _setImageIndex(self, imageIndex):
        if self.imageIndex != -1:
            for provider in self.dataProviderSlots:
                # We're switching datasets.  Unsubscribe from the old one's notifications.
                provider[self.imageIndex].unregisterInserted( bind(self.handleLayerInsertion) )
                provider[self.imageIndex].unregisterRemove( bind(self.handleLayerRemoval) )

        self.imageIndex = imageIndex
        
        # Don't repopulate the GUI if there isn't a current dataset.  Stop now. 
        if imageIndex is -1:
            self.layerstack.clear()
            return

        # Update the GUI for all layers in the current dataset
        self.updateAllLayers()

        # For layers that already exist, subscribe to ready notifications
        for provider in self.dataProviderSlots:
            for slotIndex, slot in enumerate(provider):
                slot.notifyReady( bind(self.updateAllLayers) )
                slot.notifyUnready( bind(self.updateAllLayers) )
        
        # Make sure we're notified if a layer is inserted in the future so we can subscribe to its ready notifications
        for provider in self.dataProviderSlots:
            provider[self.imageIndex].notifyInserted( bind(self.handleLayerInsertion) )
            provider[self.imageIndex].notifyRemoved( bind(self.handleLayerRemoval) )

    def handleLayerInsertion(self, slot, slotIndex):
        """
        The multislot providing our layers has a new item.
        Make room for it in the layer GUI and subscribe to updates.
        """
        with Tracer(traceLogger):
            # When the slot is ready, we'll replace the blank layer with real data
            slot[slotIndex].notifyReady( bind(self.updateAllLayers) )
            slot[slotIndex].notifyUnready( bind(self.updateAllLayers) )
    
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

    @traceLogged(traceLogger)
    def createStandardLayerFromSlot(self, slot, lastChannelIsAlpha=False):
        """
        Generate a volumina layer using the given slot.
        Choose between grayscale or RGB depending on the number of channels.
        """
        def getRange(meta):
            if 'drange' in meta:
                return meta.drange
            if numpy.issubdtype(meta.dtype, numpy.integer):
                # We assume that ints range up to their max possible value,
                return (0, numpy.iinfo( meta.dtype ).max)
            else:
                return 'auto' # Ask the image to be auto-normalized

        # Examine channel dimension to determine Grayscale vs. RGB
        shape = slot.meta.shape
        normalize = getRange(slot.meta)
        channelAxisIndex = slot.meta.axistags.index('c')
        numChannels = shape[channelAxisIndex]
        
        if lastChannelIsAlpha:
            assert numChannels <= 4, "Can't display a standard layer with more than four channels (with alpha)."
        else:
            assert numChannels <= 3, "Can't display a standard layer with more than three channels (no alpha)."

        if numChannels == 1:
            assert not lastChannelIsAlpha, "Can't have an alpha channel if there is no color channel"
            source = LazyflowSource(slot)
            return GrayscaleLayer(source, normalize=normalize)

        assert numChannels > 2 or (numChannels == 2 and not lastChannelIsAlpha)
        redProvider = OpSingleChannelSelector(graph=slot.graph)
        redProvider.Input.connect(slot)
        redProvider.Index.setValue( 0 )
        redSource = LazyflowSource( redProvider.Output )
        normalizeR = normalize
        
        greenProvider = OpSingleChannelSelector(graph=slot.graph)
        greenProvider.Input.connect(slot)
        greenProvider.Index.setValue( 1 )
        greenSource = LazyflowSource( greenProvider.Output )
        normalizeG = normalize
                        
        blueSource = None
        normalizeB = None
        if numChannels > 3 or (numChannels == 3 and not lastChannelIsAlpha):
            blueProvider = OpSingleChannelSelector(graph=slot.graph)
            blueProvider.Input.connect(slot)
            blueProvider.Index.setValue( 2 )
            blueSource = LazyflowSource( blueProvider.Output )
            normalizeB = normalize

        alphaSource = None
        normalizeA = None
        if lastChannelIsAlpha:
            alphaProvider = OpSingleChannelSelector(graph=slot.graph)
            alphaProvider.Input.connect(slot)
            alphaProvider.Index.setValue( numChannels-1 )
            alphaSource = LazyflowSource( alphaProvider.Output )
            normalizeA = normalize
        
        layer = RGBALayer( red=redSource, green=greenSource, blue=blueSource, alpha=alphaSource,
                           normalizeR=normalizeR, normalizeG=normalizeG, normalizeB=normalizeB, normalizeA=normalizeA )
        return layer

    @traceLogged(traceLogger)
    def areProvidersInSync(self):
        try:
            numImages = len(self.dataProviderSlots[0])
        except IndexError: # dataProviderSlots is empty
            pass

        inSync = True
        for slot in self.dataProviderSlots:
            inSync &= (  len(slot) == numImages
                      or ( slot._optional and slot.partner is None ) )

        return inSync

    @traceLogged(traceLogger)
    @threadRouted
    def updateAllLayers(self):
        # Check to make sure all layers are in sync
        # (During image insertions, outputs are resized one at a time.)
        if not self.areProvidersInSync():
            return

        if self.imageIndex >= 0:        
            # Ask the subclass for the updated layer list
            newGuiLayers = self.layerSetupCallback(self.imageIndex)
        else:
            newGuiLayers = []
            
        newNames = set(l.name for l in newGuiLayers)
        if len(newNames) != len(newGuiLayers):
            raise RuntimeError("All layers must have unique names.")

        # Copy the old visibilities and opacities
        if self.imageIndex != self.lastUpdateImageIndex:
            existing = {l.name : l for l in self.layerstack}
            for layer in newGuiLayers:
                if layer.name in existing.keys():
                    layer.visible = existing[layer.name].visible
                    layer.opacity = existing[layer.name].opacity

            # Clear all existing layers.
            self.layerstack.clear()
            self.lastUpdateImageIndex = self.imageIndex

            # Zoom at a 1-1 scale to avoid loading big datasets entirely...
            for view in self.editor.imageViews:
                view.doScaleTo(1)
        
        # If the datashape changed, tell the editor
        newDataShape = self.determineDatashape()
        if newDataShape is not None and self.editor.dataShape != newDataShape:
            self.editor.dataShape = newDataShape
            # Find the xyz midpoint
            midpos5d = [x/2 for x in newDataShape]
            midpos3d = midpos5d[1:4]
            
            # Start in the center of the volume
            self.editor.posModel.slicingPos = midpos3d

        # Old layers are deleted if
        # (1) They are not in the new set or
        # (2) They're data has changed
        for index, oldLayer in reversed(list(enumerate(self.layerstack))):
            if oldLayer.name not in newNames:
                needDelete = True
            else:
                newLayer = filter(lambda l: l.name == oldLayer.name, newGuiLayers)[0]
                needDelete = (newLayer.datasources != oldLayer.datasources)
                                
            if needDelete:
                self.layerstack.selectRow(index)
                self.layerstack.deleteSelected()

        # Insert all layers that aren't already in the layerstack
        # (Identified by the name attribute)
        existingNames = set(l.name for l in self.layerstack)
        for index, layer in enumerate(newGuiLayers):
            if layer.name not in existingNames:
                # Insert new
                self.layerstack.insert( index, layer )
            else:
                # Move existing layer to the correct positon
                stackIndex = self.layerstack.findMatchingIndex(lambda l: l.name == layer.name)
                self.layerstack.selectRow(stackIndex)
                while stackIndex > index:
                    self.layerstack.moveSelectedUp()
                    stackIndex -= 1
                while stackIndex < index:
                    self.layerstack.moveSelectedDown()
                    stackIndex += 1
                
    @traceLogged(traceLogger)
    def determineDatashape(self):
        if self.imageIndex < 0:
            return None

        newDataShape = None
        for provider in self.dataProviderSlots:
            for i, slot in enumerate(provider[self.imageIndex]):
                if newDataShape is None and slot.ready() and slot.meta.axistags is not None:
                    # Use an Op5ifyer adapter to transpose the shape for us.
                    op5 = Op5ifyer( graph=slot.graph )
                    op5.input.connect( slot )
                    newDataShape = op5.output.meta.shape

                    # We just needed the operator to determine the transposed shape.
                    # Disconnect it so it can be garbage collected.
                    op5.input.disconnect()
        return newDataShape

    @traceLogged(traceLogger)
    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        """
        localDir = os.path.split(__file__)[0]
        self.__viewerControlWidget = uic.loadUi(localDir + "/viewerControls.ui")

    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        """
        By default, this base class provides a blank applet drawer.
        Override this in a subclass to get a real applet drawer.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
    
    def getAppletDrawerUi(self):
        return self._drawer

    @traceLogged(traceLogger)
    def initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir+"/centralWidget.ui", self)

        # Menu is specified in a separate ui file with a dummy window
        self.menuGui = uic.loadUi(localDir+"/menu.ui") # Save as member so it doesn't get picked up by GC
        self.menuBar = self.menuGui.menuBar
        self.menuView = self.menuGui.menuView
            
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
        
        self.menuGui.actionCenterAllImages.triggered.connect(centerAllImages)
        self.menuGui.actionCenterImage.triggered.connect(centerImage)
        self.menuGui.actionToggleAllHuds.triggered.connect(hideHud)
        self.menuGui.actionToggleSelectedHud.triggered.connect(toggleSelectedHud)
        self.menuGui.actionShowDebugPatches.toggled.connect(toggleDebugPatches)
        self.menuGui.actionFitToScreen.triggered.connect(fitToScreen)
        self.menuGui.actionFitImage.triggered.connect(fitImage)
        self.menuGui.actionReset_zoom.triggered.connect(restoreImageToOriginalSize)
        self.menuGui.actionRubberBandZoom.triggered.connect(rubberBandZoom)
                
    @traceLogged(traceLogger)
    def initEditor(self):
        """
        Initialize the Volume Editor GUI.
        """
        self.editor = VolumeEditor(self.layerstack)

        # Replace the editor's navigation interpreter with one that has extra functionality
        self.clickReporter = ClickReportingInterpreter( self.editor.navInterpret, self.editor.posModel )
        self.editor.setNavigationInterpreter( self.clickReporter )
        self.clickReporter.rightClickReceived.connect( self._handleEditorRightClick )
        self.clickReporter.leftClickReceived.connect( self._handleEditorLeftClick )

        self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
        self.editor.setInteractionMode( 'navigation' )
        self.volumeEditorWidget.init(self.editor)
        
        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack

        if self.__viewerControlWidget is not None:
            model.canMoveSelectedUp.connect(self.__viewerControlWidget.UpButton.setEnabled)
            model.canMoveSelectedDown.connect(self.__viewerControlWidget.DownButton.setEnabled)
            model.canDeleteSelected.connect(self.__viewerControlWidget.DeleteButton.setEnabled)     

            # Connect our layer movement buttons to the appropriate layerstack actions
            self.__viewerControlWidget.layerWidget.init(model)
            self.__viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
            self.__viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
            self.__viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)
        
        self.editor._lastImageViewFocus = 0

    @traceLogged(traceLogger)
    def setIconToViewMenu(self):
        """
        In the "Only for Current View" menu item of the View menu, 
        show the user which axis is the current one by changing the menu item icon.
        """
        self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))

    @traceLogged(traceLogger)
    def _convertPositionToDataSpace(self, voluminaPosition):
        taggedPosition = {k:p for k,p in zip('txyzc', voluminaPosition)}
        
        # Find the first lazyflow layer in the stack
        # We assume that all lazyflow layers have the same axistags
        dataTags = None
        for layer in self.layerstack:
            for datasource in layer.datasources:
                if isinstance(datasource, LazyflowSource):
                    dataTags = datasource.dataSlot.meta.axistags
                    break

        assert dataTags is not None, "Could not find a lazyflow data source in any layer."
        position = ()
        for tag in dataTags:
            position += (taggedPosition[tag.key],)
            
        return position
    
    def _handleEditorRightClick(self, position5d):
        dataPosition = self._convertPositionToDataSpace(position5d)
        self.handleEditorRightClick(self.imageIndex, dataPosition)

    def _handleEditorLeftClick(self, position5d):
        dataPosition = self._convertPositionToDataSpace(position5d)
        self.handleEditorLeftClick(self.imageIndex, dataPosition)

    def handleEditorRightClick(self, currentImageIndex, position5d):
        # Override me
        pass

    def handleEditorLeftClick(self, currentImageIndex, position5d):
        # Override me
        pass























