from lazyflow.operators import OpPixelFeaturesPresmoothed, OpBlockedArrayCache, OpArrayPiper, Op5ToMulti, OpBlockedSparseLabelArray, OpArrayCache, \
                               OpTrainRandomForestBlocked, OpPredictRandomForest, OpSlicedBlockedArrayCache

import os, sys, numpy, copy

from PyQt4.QtCore import pyqtSignal, QTimer, QRectF, Qt, SIGNAL, QObject
from PyQt4.QtGui import *

from PyQt4 import uic

from igms.stackloader import StackLoader

from lazyflow.graph import Graph
from lazyflow.operators import Op5ToMulti, OpArrayCache, OpBlockedArrayCache, \
                               OpArrayPiper, OpPredictRandomForest, \
                               OpSingleChannelSelector, OpSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForest, \
                               OpMultiArraySlicer2,OpH5Reader, OpBlockedSparseLabelArray, \
                               OpMultiArrayStacker, OpTrainRandomForestBlocked, \
                               OpH5ReaderBigDataset, OpSlicedBlockedArrayCache, OpPixelFeaturesPresmoothed

from volumina.api import LazyflowSource, GrayscaleLayer, RGBALayer, ColortableLayer, \
                         AlphaModulatedLayer, LayerStackModel, VolumeEditor, LazyflowSinkSource
from volumina.adaptors import Op5ifyer
from labelListView import Label
from labelListModel import LabelListModel

from ilastikshell.applet import Applet

import vigra

from utility.simpleSignal import SimpleSignal
from utility import bind

class Tool():
    Navigation = 0
    Paint = 1
    Erase = 2

def getPathToLocalDirectory():
    # Determines the path of this python file so we can refer to other files relative to it.
    p = os.path.split(__file__)[0]+'/'
    if p == "/":
        p = "."+p
    return p

class PixelClassificationGui(QMainWindow):
    def __init__(self, pipeline = None, graph = None ):
        QMainWindow.__init__(self)
        
        self.pipeline = pipeline

        self.imageIndex = 0
        self.layerstack = None

        self.pipeline.InputImages.notifyInserted( bind(self.subscribeToInputImageChanges) )
        self.pipeline.InputImages.notifyRemove( bind(self.subscribeToInputImageChanges) )
        self.subscribeToInputImageChanges()

        self.pipeline.LabelImages.notifyInserted( bind(self.subscribeToLabelImageChanges) )
        self.pipeline.LabelImages.notifyRemove( bind(self.subscribeToLabelImageChanges) )

        def handleOutputListChanged():
            """This closure is called when an image is added or removed from the output."""
            if len(self.pipeline.CachedPredictionProbabilities) > 0:
                self.pipeline.CachedPredictionProbabilities[self.imageIndex].notifyMetaChanged( bind(self.updateForNewClasses) )
            else:
                self.clearLabelListGui()

        self.pipeline.CachedPredictionProbabilities.notifyInserted( bind(handleOutputListChanged) )
        self.pipeline.CachedPredictionProbabilities.notifyRemove( bind(handleOutputListChanged) )
        
        def handleOutputListAboutToResize(slot, oldsize, newsize):
            if newsize == 0:
                self.removeAllPredictionLayers()
        self.pipeline.CachedPredictionProbabilities.notifyResize(handleOutputListAboutToResize)
        
        # Editor will be initialized when data is loaded
        self.editor = None
        self.labellayer = None
        
        #Normalize the data if true
        self._normalize_data=True
        
        if 'notnormalize' in sys.argv:
            print sys.argv
            self._normalize_data=False
            sys.argv.remove('notnormalize')

        self._colorTable16 = self._createDefault16ColorColorTable()
        
        self.g = graph if graph else Graph()
        self.fixableOperators = [self.pipeline.prediction_cache]
        
        #The old ilastik provided the following scale names:
        #['Tiny', 'Small', 'Medium', 'Large', 'Huge', 'Megahuge', 'Gigahuge']
        #The corresponding scales are:
        self.featScalesList=[0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        
        self.initCentralUic()
        self.initViewerControlUi()
        self.initAppletBarUic()

        self._programmaticallyRemovingLabels = False

        # Track 
        self.predictionLayerGuiLabels = set()

    # Subscribe to various pipeline events so we can respond appropriately in the GUI
    def subscribeToInputImageChanges(self, slot=None, position=None, finalsize=None):
        """This closure is called when a new input image is connected to the multi-input slot."""
        if len(self.pipeline.InputImages) > 0:
            # Subscribe to changes on the graph input.
            self.pipeline.InputImages[self.imageIndex].notifyConnect( bind(self.handleGraphInputChanged) )
            self.pipeline.InputImages[self.imageIndex].notifyMetaChanged( bind(self.handleGraphInputChanged) )
        else:
            if self.layerstack is not None:
                self.layerstack.clear()

    def subscribeToLabelImageChanges(self):
        if len(self.pipeline.LabelImages) > 0:
            # Subscribe to changes on the graph input.
            self.pipeline.LabelImages[self.imageIndex].notifyMetaChanged( bind(self.initLabelLayer) )
            self.pipeline.LabelImages[self.imageIndex].notifyConnect( bind(self.initLabelLayer) )

    def setImageIndex(self, imageIndex):
        self.imageIndex = imageIndex
        if self.imageIndex == -1:
            self.layerstack.clear()
        else:
            self.subscribeToInputImageChanges()
            self.handleGraphInputChanged()
            self.pipeline.LabelsAllowedFlags[self.imageIndex].notifyDirty( bind( self.changeInteractionMode, Tool.Navigation ) )
        
        # Make sure the painting controls are hidden if necessary
        self.changeInteractionMode(Tool.Navigation)

    def setIconToViewMenu(self):
        self.actionOnly_for_current_view.setIcon(QIcon(self.editor.imageViews[self.editor._lastImageViewFocus]._hud.axisLabel.pixmap()))
    
    def initViewerControlUi(self):
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self.viewerControlWidget = uic.loadUi(p+"/viewerControls.ui")

    def initCentralUic(self):
        # We don't know where the user is running this script from,
        #  so locate the .ui file relative to this .py file's path
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        uic.loadUi(p+"/centralWidget.ui", self)
        
        def toggleDebugPatches(show):
            self.editor.showDebugPatches = show
        def fitToScreen():
            shape = self.editor.posModel.shape
            for i, v in enumerate(self.editor.imageViews):
                s = list(copy.copy(shape))
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
                
        self.layerstack = LayerStackModel()
        self.predictionLayers = set()

    def initAppletBarUic(self):
        # We have two different applet bar controls
        self.initLabelUic()
        self.initPredictionControlsUic()
    
    @property
    def labelControlUi(self):
        return self._labelControlUi
    
    def initLabelUic(self):
        # We don't know where the user is running this script from,
        #  so locate the .ui file relative to this .py file's path
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        _labelControlUi = uic.loadUi(p+"/labelingDrawer.ui") # Don't pass self: applet ui is separate from the main ui

        # We own the applet bar ui
        self._labelControlUi = _labelControlUi

        # Initialize the label list model
        model = LabelListModel()
        _labelControlUi.labelListView.setModel(model)
        _labelControlUi.labelListModel=model
        _labelControlUi.labelListModel.rowsAboutToBeRemoved.connect(self.onLabelAboutToBeRemoved)
        _labelControlUi.labelListModel.labelSelected.connect(self.switchLabel)
        
        def onDataChanged(topLeft, bottomRight):
            """Handle changes to the label list selections."""
            firstRow = topLeft.row()
            lastRow  = bottomRight.row()
        
            firstCol = topLeft.column()
            lastCol  = bottomRight.column()
            
            if lastCol == firstCol == 0:
                assert(firstRow == lastRow) #only one data item changes at a time

                #in this case, the actual data (for example color) has changed
                self.switchColor(firstRow+1, _labelControlUi.labelListModel[firstRow].color)
                self.editor.scheduleSlicesRedraw()
            else:
                #this column is used for the 'delete' buttons, we don't care
                #about data changed here
                pass

        # Connect Applet GUI to our event handlers
        _labelControlUi.AddLabelButton.clicked.connect(self.handleAddLabelButtonClicked)
        _labelControlUi.checkInteractive.setEnabled(False)
        _labelControlUi.checkInteractive.toggled.connect(self.toggleInteractive)
        _labelControlUi.labelListModel.dataChanged.connect(onDataChanged)
        
        # Initialize the arrow tool button with an icon and handler
        iconPath = getPathToLocalDirectory() + "/icons/arrow.png"
        arrowIcon = QIcon(iconPath)
        _labelControlUi.arrowToolButton.setIcon(arrowIcon)
        _labelControlUi.arrowToolButton.setCheckable(True)
        _labelControlUi.arrowToolButton.clicked.connect( lambda checked: self.handleToolButtonClicked(checked, Tool.Navigation) )

        # Initialize the paint tool button with an icon and handler
        paintBrushIconPath = getPathToLocalDirectory() + "/icons/paintbrush.png"
        paintBrushIcon = QIcon(paintBrushIconPath)
        _labelControlUi.paintToolButton.setIcon(paintBrushIcon)
        _labelControlUi.paintToolButton.setCheckable(True)
        _labelControlUi.paintToolButton.clicked.connect( lambda checked: self.handleToolButtonClicked(checked, Tool.Paint) )

        # Initialize the erase tool button with an icon and handler
        eraserIconPath = getPathToLocalDirectory() + "/icons/eraser.png"
        eraserIcon = QIcon(eraserIconPath)
        _labelControlUi.eraserToolButton.setIcon(eraserIcon)
        _labelControlUi.eraserToolButton.setCheckable(True)
        _labelControlUi.eraserToolButton.clicked.connect( lambda checked: self.handleToolButtonClicked(checked, Tool.Erase) )
        
        # This maps tool types to the buttons that enable them
        self.toolButtons = { Tool.Navigation : _labelControlUi.arrowToolButton,
                             Tool.Paint      : _labelControlUi.paintToolButton,
                             Tool.Erase      : _labelControlUi.eraserToolButton }
        
        self.brushSizes = [ (1,  ""),
                            (3,  "Tiny"),
                            (5,  "Small"),
                            (7,  "Medium"),
                            (11, "Large"),
                            (23, "Huge"),
                            (31, "Megahuge"),
                            (61, "Gigahuge") ]

        for size, name in self.brushSizes:
            _labelControlUi.brushSizeComboBox.addItem( str(size) + " " + name )
        
        _labelControlUi.brushSizeComboBox.currentIndexChanged.connect(self.onBrushSizeChange)
        self.paintBrushSizeIndex = 0
        self.eraserSizeIndex = 0
        
        self._labelControlUi.checkInteractive.setEnabled(True)
        
        def enableDrawerControls(enabled):
            """
            Enable or disable all of the controls in this applet's label drawer widget.
            """
            # All the controls in our GUI
            controlList = [ _labelControlUi.AddLabelButton,
                            _labelControlUi.labelListView,
                            _labelControlUi.checkInteractive,
                            _labelControlUi.brushSizeComboBox ]
            for button in self.toolButtons.values():
                controlList.append(button)
    
            # Enable/disable all of them
            for control in controlList:
                control.setEnabled(enabled)
        
        # Expose the enable function with the name the shell expects
        _labelControlUi.enableControls = enableDrawerControls

    def handleToolButtonClicked(self, checked, toolId):
        """
        Called when the user clicks any of the "tool" buttons in the label applet bar GUI.
        """
        # Users can only *switch between* tools, not turn them off.
        # If they try to, re-select the button automatically.
        if not checked:
            self.toolButtons[toolId].setChecked(True)
        # If the user is checking a new button
        else:
            # Uncheck all the other buttons
            for tool, button in self.toolButtons.items():
                if tool != toolId:
                    button.setChecked(False)

            self.changeInteractionMode( toolId )

    @property
    def predictionControlUi(self):
        return self._predictionControlUi

    def initPredictionControlsUic(self):
        # We don't know where the user is running this script from,
        #  so locate the .ui file relative to this .py file's path
        p = os.path.split(__file__)[0]+'/'
        if p == "/": p = "."+p
        self._predictionControlUi = uic.loadUi(p+"/predictionDrawer.ui") # Don't pass self: applet ui is separate from the main ui
        self._predictionControlUi.trainAndPredictButton.clicked.connect(self.onTrainAndPredictButtonClicked)

        def enableDrawerControls(enabled):
            """
            Enable or disable all of the controls in this applet's prediction drawer widget.
            """
            # All the controls in our GUI
            controlList = [ self._predictionControlUi.trainAndPredictButton ]
    
            # Enable/disable all of them
            for control in controlList:
                control.setEnabled(enabled)
        
        # Expose the enable function with the name the shell expects
        self._predictionControlUi.enableControls = enableDrawerControls

    def toggleInteractive(self, checked):
        print "toggling interactive mode to '%r'" % checked
        
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
        else:
            self.g.stopGraph()
            self.g.resumeGraph()                

        self._labelControlUi.AddLabelButton.setEnabled(not checked)
        self._labelControlUi.labelListModel.allowRemove(not checked)
        self._predictionControlUi.trainAndPredictButton.setEnabled(not checked)
        
        for o in self.fixableOperators:
            o.inputs["fixAtCurrent"].setValue(not checked)

        # Prediction layers should be switched on/off when the interactive checkbox is toggled
        for layer in self.predictionLayers:
            layer.visible = checked

        self.editor.scheduleSlicesRedraw()

    def changeInteractionMode( self, toolId ):
        """
        Implement the GUI's response to the user selecting a new tool.
        """
        # If we have no editor, we can't do anything yet
        if self.editor is None:
            return
        
        # The volume editor expects one of two specific names
        modeNames = { Tool.Navigation   : "navigation",
                      Tool.Paint        : "brushing",
                      Tool.Erase        : "brushing" }

        # Hide everything by default
        self._labelControlUi.arrowToolButton.hide()
        self._labelControlUi.paintToolButton.hide()
        self._labelControlUi.eraserToolButton.hide()
        self._labelControlUi.brushSizeComboBox.hide()
        self._labelControlUi.brushSizeCaption.hide()

        if self.imageIndex != -1 and self.pipeline.LabelsAllowedFlags[self.imageIndex].value:
            self._labelControlUi.arrowToolButton.show()
            self._labelControlUi.paintToolButton.show()
            self._labelControlUi.eraserToolButton.show()
            # Update the applet bar caption
            if toolId == Tool.Navigation:
                # Make sure the arrow button is pressed
                self._labelControlUi.arrowToolButton.setChecked(True)
                # Hide the brush size control
                self._labelControlUi.brushSizeCaption.hide()
                self._labelControlUi.brushSizeComboBox.hide()
            elif toolId == Tool.Paint:
                # Make sure the paint button is pressed
                self._labelControlUi.paintToolButton.setChecked(True)
                # Show the brush size control and set its caption
                self._labelControlUi.brushSizeCaption.show()
                self._labelControlUi.brushSizeComboBox.show()
                self._labelControlUi.brushSizeCaption.setText("Brush Size:")
                
                # If necessary, tell the brushing model to stop erasing
                if self.editor.brushingModel.erasing:
                    self.editor.brushingModel.disableErasing()
                # Set the brushing size
                brushSize = self.brushSizes[self.paintBrushSizeIndex][0]
                self.editor.brushingModel.setBrushSize(brushSize)
    
                # Make sure the GUI reflects the correct size
                self._labelControlUi.brushSizeComboBox.setCurrentIndex(self.paintBrushSizeIndex)
                
                # Make sure we're using the correct label color
                self.switchLabel( self._labelControlUi.labelListModel.selectedRow() )
                
            elif toolId == Tool.Erase:
                # Make sure the erase button is pressed
                self._labelControlUi.eraserToolButton.setChecked(True)
                # Show the brush size control and set its caption
                self._labelControlUi.brushSizeCaption.show()
                self._labelControlUi.brushSizeComboBox.show()
                self._labelControlUi.brushSizeCaption.setText("Eraser Size:")
                
                # If necessary, tell the brushing model to start erasing
                if not self.editor.brushingModel.erasing:
                    self.editor.brushingModel.setErasing()
                # Set the brushing size
                eraserSize = self.brushSizes[self.eraserSizeIndex][0]
                self.editor.brushingModel.setBrushSize(eraserSize)
                
                # Make sure the GUI reflects the correct size
                self._labelControlUi.brushSizeComboBox.setCurrentIndex(self.eraserSizeIndex)

        self.editor.setInteractionMode( modeNames[toolId] )

    def onBrushSizeChange(self, index):
        """
        Handle the user's new brush size selection.
        Note: The editor's brushing model currently maintains only a single 
              brush size, which is used for both painting and erasing. 
              However, we maintain two different sizes for the user and swap 
              them depending on which tool is selected.
        """
        newSize = self.brushSizes[index][0]
        if self.editor.brushingModel.erasing:
            self.eraserSizeIndex = index
            self.editor.brushingModel.setBrushSize(newSize)
        else:
            self.paintBrushSizeIndex = index
            self.editor.brushingModel.setBrushSize(newSize)

    def switchLabel(self, row):
        print "switching to label=%r" % (self._labelControlUi.labelListModel[row])
        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        self.editor.brushingModel.setBrushColor(self._labelControlUi.labelListModel[row].color)
        
    def switchColor(self, row, color):
        print "label=%d changes color to %r" % (row, color)
        self.labellayer.colorTable[row]=color.rgba()
        self.editor.brushingModel.setBrushColor(color)
        self.editor.scheduleSlicesRedraw()
    
    def updateForNewClasses(self):
        self.updateLabelList()
        self.setupPredictionLayers()
    
    def updateLabelList(self):
        """
        This function is called when the number of labels has changed without our knowledge.
        We need to add/remove labels until we have the right number
        """
        # Get the number of labels in the label data
        numLabels = max(self.pipeline.MaxLabelValue.value, self._labelControlUi.labelListModel.rowCount())
        if numLabels == None:
            numLabels = 0

        # Add rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() < numLabels:
            self.addNewLabel()
        
#        # Remove rows until we have the right number
#        while self._labelControlUi.labelListModel.rowCount() > numLabels:
#            self.removeLastLabel()

        # Select a label by default so the brushing controller doesn't get confused.
        if numLabels > 0:
            selectedRow = self._labelControlUi.labelListModel.selectedRow()
            if selectedRow == -1:
                selectedRow = 0 
            self.switchLabel(selectedRow)

    def clearLabelListGui(self):
        # Remove rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() > 0:
            self.removeLastLabel()

    def handleAddLabelButtonClicked(self):
        """
        The user clicked the "Add Label" button.  Update the GUI and pipeline.
        """
        self.addNewLabel()
    
    def addNewLabel(self):
        """
        Add a new label to the label list GUI control.
        Return the new number of labels in the control.
        """
        color = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
        numLabels = len(self._labelControlUi.labelListModel)
        if numLabels < len(self._colorTable16):
            color = self._colorTable16[numLabels]
        self.labellayer.colorTable.append(color.rgba())
        
        self._labelControlUi.labelListModel.insertRow(self._labelControlUi.labelListModel.rowCount(), Label("Label %d" % (self._labelControlUi.labelListModel.rowCount() + 1), color))
        nlabels = self._labelControlUi.labelListModel.rowCount()

        #make the new label selected
        #index = self._labelControlUi.labelListModel.index(nlabels-1, 1)
        self._labelControlUi.labelListView.selectRow(nlabels-1)
        
        #FIXME: this should watch for model changes
        #drawing will be enabled when the first label is added
        #self.changeInteractionMode( Tool.Navigation )
        
        return nlabels
    
    def removeLastLabel(self):
        """
        Programmatically (i.e. not from the GUI) reduce the size of the label list by one.
        """
        self._programmaticallyRemovingLabels = True
        numRows = self._labelControlUi.labelListModel.rowCount()
        # This will trigger the signal that calls onLabelAboutToBeRemoved()
        self._labelControlUi.labelListModel.removeRow(numRows-1)
    
        self._programmaticallyRemovingLabels = False
    
    def onLabelAboutToBeRemoved(self, parent, start, end):
        #the user deleted a label, reshape prediction and remove the layer
        #the interface only allows to remove one label at a time?
        
        # Don't respond unless this actually came from the GUI
        if self._programmaticallyRemovingLabels:
            return
        
        nout = start-end+1
        ncurrent = self._labelControlUi.labelListModel.rowCount()
        print "removing", nout, "out of ", ncurrent
        
        for il in range(start, end+1):
            # Changing the deleteLabel input causes the operator (OpBlockedSparseArray)
            #  to search through the entire list of labels and delete the entries for the matching label.
            self.pipeline.opLabelArray.inputs["deleteLabel"].setValue(il+1)
            
            # We need to "reset" the deleteLabel input to -1 when we're finished.
            #  Otherwise, you can never delete the same label twice in a row.
            #  (Only *changes* to the input are acted upon.)
            self.pipeline.opLabelArray.inputs["deleteLabel"].setValue(-1)
            
    def setupPredictionLayers(self):
        """
        Add all prediction label layers to the volume editor
        """
        newGuiLabels = set()        
        # TODO: Assumes channel is last axis
        nclasses = self.pipeline.CachedPredictionProbabilities[self.imageIndex].meta.shape[-1]
        # Add prediction results for all classes as separate channels
        for icl in range(nclasses):
            layerGuiLabel = self._labelControlUi.labelListModel._labels[icl]            
            newGuiLabels.add(layerGuiLabel)
            # Only add this prediction layer if it isn't already shown in the viewer
            if layerGuiLabel not in self.predictionLayerGuiLabels:
                self.addPredictionLayer(icl, layerGuiLabel)

        # Eliminate any old layers that we don't want any more
        for oldGuiLabel in (self.predictionLayerGuiLabels - newGuiLabels): #<-- set difference
            self.removePredictionLayer(oldGuiLabel)
        self.predictionLayerGuiLabels = newGuiLabels
    
    def removeAllPredictionLayers(self):
        for label in self.predictionLayerGuiLabels:
            self.removePredictionLayer(label)
    
    def onTrainAndPredictButtonClicked(self):
        """
        The user clicked "Train and Predict".
        Handle this event by asking the pipeline for a prediction over the entire output region.
        """
        # "unfix" any operator inputs that were frozen before
        for o in self.fixableOperators:
            o.inputs["fixAtCurrent"].setValue(False)

        # Can't change labels while we're in the middle of a prediction
        self._labelControlUi.labelListModel.allowRemove(False)
        
        # Disable the parts of the GUI that can't be used while we're predicting . . .
        self._labelControlUi.AddLabelButton.setEnabled(False)
        # TODO: Need a way to disable upstream inputs while this is going on . . .
        #self._featureSelectionUi.SelectFeaturesButton.setEnabled(False)
        self._predictionControlUi.trainAndPredictButton.setEnabled(False)

        # Closure to call when the prediction is finished
        def onPredictionComplete(predictionResults):
            
            print "Prediction shape=", predictionResults.shape
            
            # Re-enable the GUI
            self._labelControlUi.AddLabelButton.setEnabled(True)
#            self._featureSelectionUi.SelectFeaturesButton.setEnabled(True)
            self._predictionControlUi.trainAndPredictButton.setEnabled(True)
            
            # Re-fix the operators now that the computation is complete.
            for o in self.fixableOperators:
                o.inputs["fixAtCurrent"].setValue(True)

            # Redraw the image in the GUI
            self.editor.scheduleSlicesRedraw()

        # Request the prediction for the entire image stack.
        # Call our callback when it's finished
        self.pipeline.CachedPredictionProbabilities[self.imageIndex][:].notify( onPredictionComplete )
    
    def addPredictionLayer(self, icl, ref_label):
        """
        Add a prediction layer to the editor.
        """
        selector=OpSingleChannelSelector(self.g)
        selector.inputs["Input"].connect(self.pipeline.CachedPredictionProbabilities[self.imageIndex])
        selector.inputs["Index"].setValue(icl)
        
##      self.pipeline.prediction_cache.inputs["fixAtCurrent"].setValue(not self._labelControlUi.checkInteractive.isChecked())
        
        predictsrc = LazyflowSource(selector.outputs["Output"])
        def srcName(newName):
            predictsrc.setObjectName("Prediction for %s" % ref_label.name)
        srcName("")
        
        predictLayer = AlphaModulatedLayer(predictsrc, tintColor=ref_label.color, normalize = None )
        predictLayer.nameChanged.connect(srcName)
        predictLayer.opacity = 0.5
        
        def setLayerColor(c):
            print "as the color of label '%s' has changed, setting layer's '%s' tint color to %r" % (ref_label.name, predictLayer.name, c)
            predictLayer.tintColor = c
        ref_label.colorChanged.connect(setLayerColor)
        def setLayerName(n):
            newName = "Prediction for %s" % ref_label.name
            print "as the name of label '%s' has changed, setting layer's '%s' name to '%s'" % (ref_label.name, predictLayer.name, newName)
            predictLayer.name = newName
        setLayerName(ref_label.name)
        ref_label.nameChanged.connect(setLayerName)
        
        # Attach a new field to identify this layer so we can find it later
        predictLayer.ref_object = ref_label

        #make sure that labels (index = 0) stay on top!
        self.layerstack.insert(1, predictLayer )
        predictLayer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )
        self.predictionLayers.add(predictLayer)
               
    def removePredictionLayer(self, ref_label):
        for il, layer in enumerate(self.layerstack):
            if layer.ref_object==ref_label:
                print "found the prediction", layer.ref_object, ref_label
                self.predictionLayers.remove(layer)
                self.layerstack.removeRows(il, 1)
                break
    
    def handleGraphInputChanged(self):
        """
        The raw input data to our top-level operator has changed.
        """
        if len(self.pipeline.InputImages) > 0 \
        and self.pipeline.InputImages[self.imageIndex].shape is not None:

            shape = self.pipeline.InputImages[self.imageIndex].shape
            srcs    = []
            minMax = []
            
            print "* Data has shape=%r" % (shape,)
            
            #create a layer for each channel of the input:
            slicer=OpMultiArraySlicer2(self.g)
            opFiver = Op5ifyer(graph=self.g)
            opFiver.input.connect(self.pipeline.InputImages[self.imageIndex])
            slicer.inputs["Input"].connect(opFiver.output)
            
            slicer.inputs["AxisFlag"].setValue('c')
           
            nchannels = shape[-1]
            for ich in xrange(nchannels):
                if self._normalize_data:
                    if slicer.outputs['Slices'][ich].meta.dtype == numpy.uint8:
                        # Don't bother normalizing uint8 data
                        mm = (0, 255)
                    else:
                        data=slicer.outputs['Slices'][ich][:].allocate().wait()
                        #find the minimum and maximum value for normalization
                        mm = (numpy.min(data), numpy.max(data))
                    print "  - channel %d: min=%r, max=%r" % (ich, mm[0], mm[1])
                    minMax.append(mm)
                else:
                    minMax.append(None)
                layersrc = LazyflowSource(slicer.outputs['Slices'][ich], priority = 100)
                layersrc.setObjectName("raw data channel=%d" % ich)
                srcs.append(layersrc)
                
            #FIXME: we shouldn't merge channels automatically, but for now it's prettier
            layer1 = None
            if nchannels == 1:
                layer1 = GrayscaleLayer(srcs[0], normalize=minMax[0])
                layer1.set_range(0,minMax[0])
                print "  - showing raw data as grayscale"
            elif nchannels==2:
                layer1 = RGBALayer(red  = srcs[0], normalizeR=minMax[0],
                                   green = srcs[1], normalizeG=minMax[1])
                layer1.set_range(0, minMax[0])
                layer1.set_range(1, minMax[1])
                print "  - showing channel 1 as red, channel 2 as green"
            elif nchannels==3:
                layer1 = RGBALayer(red   = srcs[0], normalizeR=minMax[0],
                                   green = srcs[1], normalizeG=minMax[1],
                                   blue  = srcs[2], normalizeB=minMax[2])
                layer1.set_range(0, minMax[0])
                layer1.set_range(1, minMax[1])
                layer1.set_range(2, minMax[2])
                print "  - showing channel 1 as red, channel 2 as green, channel 3 as blue"
            else:
                print "only 1,2 or 3 channels supported so far"
                return
            print
            
            layer1.name = "Input data"
            layer1.ref_object = None
            
            # Before we append the input data to the viewer,
            # Delete any previous input data layers
            self.removeLayersFromEditorStack(layer1.name)

            def handleSourceResize(slot, oldsize, newsize):
                if newsize == 0:
                    self.removeLayersFromEditorStack(layer1.name)
            self.pipeline.InputImages.notifyResize(handleSourceResize)
    
            self.initEditor()
    
            # The input data layer should always be on the bottom of the stack (last)
            #  so we can always see the labels and predictions.
            self.layerstack.insert(len(self.layerstack), layer1)
            layer1.visibleChanged.connect( self.editor.scheduleSlicesRedraw )

            self.initLabelLayer()

    def removeLayersFromEditorStack(self, layerName):
        """
        Remove the layer with the given name from the GUI image stack.
        """
        # Delete in reverse order so we can remove rows as we go
        for i in reversed(range(0, len(self.layerstack))):
            if self.layerstack[i].name == layerName:
                self.layerstack.removeRows(i, 1)

    def initLabelLayer(self, *args):
        """
        - Create the label "sourcesink" and give it to the volume editor.
        - Create the label layer and insert it into the layer stack.
        - Does not actually add any labels to the GUI.
        """
        if len(self.pipeline.LabelImages) > 0 and self.editor is not None: #and len(self.pipeline.InputImages) > 0:
            # Add the layer to draw the labels, but don't add any labels
            self.labelsrc = LazyflowSinkSource(self.pipeline,
                                               self.pipeline.LabelImages[self.imageIndex],
                                               self.pipeline.LabelInputs[self.imageIndex])
            self.labelsrc.setObjectName("labels")
        
            transparent = QColor(0,0,0,0)
            self.labellayer = ColortableLayer(self.labelsrc, colorTable = [transparent.rgba()] )
            self.labellayer.name = "Labels"
            self.labellayer.ref_object = None
            self.labellayer.visibleChanged.connect( self.editor.scheduleSlicesRedraw )
        
            # Remove any label layer we had before
            self.removeLayersFromEditorStack( self.labellayer.name )
        
            # Tell the editor where to draw label data
            self.editor.setLabelSink(self.labelsrc)

            # Labels should be first (on top)
            self.layerstack.insert(0, self.labellayer)
    
    def initEditor(self):
        """
        Initialize (or reinitialize) the Volume Editor GUI.
        """
        # Only construct the editor once
        if self.editor is None:
            self.editor = VolumeEditor(self.layerstack)
    
            self.editor.newImageView2DFocus.connect(self.setIconToViewMenu)
            #drawing will be enabled when the first label is added  
            self.editor.setInteractionMode( 'navigation' )
            self.volumeEditorWidget.init(self.editor)
            model = self.editor.layerStack
            self.viewerControlWidget.layerWidget.init(model)
            self.viewerControlWidget.UpButton.clicked.connect(model.moveSelectedUp)
            model.canMoveSelectedUp.connect(self.viewerControlWidget.UpButton.setEnabled)
            self.viewerControlWidget.DownButton.clicked.connect(model.moveSelectedDown)
            model.canMoveSelectedDown.connect(self.viewerControlWidget.DownButton.setEnabled)
            self.viewerControlWidget.DeleteButton.clicked.connect(model.deleteSelected)
            model.canDeleteSelected.connect(self.viewerControlWidget.DeleteButton.setEnabled)     
            
            self.pipeline.opLabelArray.inputs["eraser"].setValue(self.editor.brushingModel.erasingNumber)

        # Clear the label layers
        self.editor.setLabelSink(None)
        if self.labellayer is not None:
            # Remove any existing label layer before adding a new one
            self.removeLayersFromEditorStack(self.labellayer.name)

        # Give the editor the appropriate shape
        shape = self.pipeline.InputImages[self.imageIndex].shape
        self.editor.dataShape = shape

    def _createDefault16ColorColorTable(self):
        c = []
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
        return c

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



































