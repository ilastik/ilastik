# Built-in
import os
import logging
import itertools

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import QRect
from PyQt4.QtGui import *

# HCI
from lazyflow.tracer import traceLogged
from volumina.api import LazyflowSinkSource, ColortableLayer
from igms.labelListView import Label
from igms.labelListModel import LabelListModel

# ilastik
from ilastik.utility import bind
from ilastik.utility.gui import ThunkEventHandler
from ilastik.applets.layerViewer import LayerViewerGui

# Loggers    
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

# FIXME: This should be eliminated or moved to utility.
def getPathToLocalDirectory():
    # Determines the path of this python file so we can refer to other files relative to it.
    p = os.path.split(__file__)[0]+'/'
    if p == "/":
        p = "."+p
    return p

class Tool():
    """Enumerate the types of toolbar buttons."""
    Navigation = 0 # Arrow
    Paint = 1
    Erase = 2

class LabelingGui(LayerViewerGui):
    """
    Provides all the functionality of a simple layerviewer 
    applet with the added functionality of labeling.
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################
    
    def centralWidget( self ):
        return self

    def appletDrawers(self):
        return [ ("Label Marking", self._drawerUi) ]

    def reset(self):
        # Clear the label list GUI
        self.clearLabelListGui()
        
        # Start in navigation mode (not painting)
        self.changeInteractionMode(Tool.Navigation)

    ###########################################
    ###########################################

    class LabelingGuiSlots(object):
        def __init__(self):
            # Label slots are multi (level=1) and accessed as shown.
            # Slot to insert labels onto
            self.labelInput = None # labelInput[image_index].setInSlot(xxx)
            # Slot to read labels from 
            self.labelOutput = None # labelOutput[image_index].get(roi)            
            # Slot that determines which label value corresponds to erased values
            self.labelEraserValue = None # labelEraserValue.setValue(xxx) 
            # Slot that is used to request wholesale label deletion
            self.labelDelete = None # labelDelete.setValue(xxx)
            # Slot that contains the maximum label value (for all images)
            self.maxLabelValue = None # maxLabelValue.value
            
            # Slot to specify which images the user is allowed to label.
            self.labelsAllowed = None # labelsAllowed[image_index].value == True

            # Each display slot can be either:
            # Multi with level=1, accessed as: slot[image_index].get(roi)
            # Multi with level=2, accessed as: slot[image_index][layer_index].get(roi)
            self.displaySlots = []
    
    @traceLogged(traceLogger)
    def __init__(self, labelingGuiSlots ):
        """
        See LabelingGuiSlots class (above) for expected type of labelingGuiSlots parameter.
        """
        # Do have have all the slots we need?
        assert isinstance(labelingGuiSlots, LabelingGui.LabelingGuiSlots)
        assert all( [v is not None for v in labelingGuiSlots.__dict__.values()] )
        
        # Init base class
        allSlots = labelingGuiSlots.displaySlots + [ labelingGuiSlots.labelOutput ]
        super(LabelingGui, self).__init__( allSlots )

        self._labelingGuiSlots = labelingGuiSlots
        self._labelingGuiSlots.labelEraserValue.setValue(self.editor.brushingModel.erasingNumber)
        self._labelingGuiSlots.maxLabelValue.notifyDirty( bind(self.updateLabelList) )

        # Register for thunk events (easy UI calls from non-GUI threads)
        self.thunkEventHandler = ThunkEventHandler(self)

        self._colorTable16 = self._createDefault16ColorColorTable()        
        self._programmaticallyRemovingLabels = False
        self.initLabelControls()
        self.initBrushControls()
        self.initAppletDrawer()

    @traceLogged(traceLogger)
    def initAppletDrawer(self):
        self._drawerUi = QWidget(parent=self)
        geo = QRect(self._drawerUi.geometry())
        geo.setHeight(self._labelControlUi.height() + self._brushControlUi.height())
        self._drawerUi.setGeometry(geo) 

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self._labelControlUi)
        layout.addWidget(self._brushControlUi)
        self._drawerUi.setLayout(layout)

    @traceLogged(traceLogger)
    def initLabelControls(self):
        # Don't pass self: applet ui is separate from the main ui
        _labelControlUi = uic.loadUi(getPathToLocalDirectory() + "/labelControls.ui")

        # We own the applet bar ui
        self._labelControlUi = _labelControlUi

        # Initialize the label list model
        model = LabelListModel()
        _labelControlUi.labelListView.setModel(model)
        _labelControlUi.labelListModel=model
        _labelControlUi.labelListModel.rowsAboutToBeRemoved.connect(self.onLabelAboutToBeRemoved)
        _labelControlUi.labelListModel.labelSelected.connect(self.switchLabel)
        
        @traceLogged(traceLogger)
        def onDataChanged(topLeft, bottomRight):
            """Handle changes to the label list selections."""
            firstRow = topLeft.row()
            lastRow  = bottomRight.row()
        
            firstCol = topLeft.column()
            lastCol  = bottomRight.column()
            
            if lastCol == firstCol == 0:
                assert(firstRow == lastRow) #only one data item changes at a time

                #in this case, the actual data (for example color) has changed
                color = _labelControlUi.labelListModel[firstRow].color
                self._colorTable16[firstRow+1] = color.rgba()
                self.editor.brushingModel.setBrushColor(color)
                
                # Update the label layer colortable to match the list entry
                labellayer = self.getLabelLayer()
                labellayer.colorTable = self._colorTable16                
            else:
                #this column is used for the 'delete' buttons, we don't care
                #about data changed here
                pass

        # Connect Applet GUI to our event handlers
        _labelControlUi.AddLabelButton.clicked.connect( bind(self.handleAddLabelButtonClicked) )
#        _labelControlUi.checkInteractive.setEnabled(False)
#        _labelControlUi.checkInteractive.toggled.connect(self.toggleInteractive)
        _labelControlUi.labelListModel.dataChanged.connect(onDataChanged)
        
    @traceLogged(traceLogger)
    def initBrushControls(self):
        _brushControlUi = uic.loadUi(getPathToLocalDirectory() + "/brushingControls.ui")
        self._brushControlUi = _brushControlUi

        # Initialize the arrow tool button with an icon and handler
        iconPath = getPathToLocalDirectory() + "/icons/arrow.jpg"
        arrowIcon = QIcon(iconPath)
        _brushControlUi.arrowToolButton.setIcon(arrowIcon)
        _brushControlUi.arrowToolButton.setCheckable(True)
        _brushControlUi.arrowToolButton.clicked.connect( lambda checked: self.handleToolButtonClicked(checked, Tool.Navigation) )

        # Initialize the paint tool button with an icon and handler
        paintBrushIconPath = getPathToLocalDirectory() + "/icons/paintbrush.png"
        paintBrushIcon = QIcon(paintBrushIconPath)
        _brushControlUi.paintToolButton.setIcon(paintBrushIcon)
        _brushControlUi.paintToolButton.setCheckable(True)
        _brushControlUi.paintToolButton.clicked.connect( lambda checked: self.handleToolButtonClicked(checked, Tool.Paint) )

        # Initialize the erase tool button with an icon and handler
        eraserIconPath = getPathToLocalDirectory() + "/icons/eraser.png"
        eraserIcon = QIcon(eraserIconPath)
        _brushControlUi.eraserToolButton.setIcon(eraserIcon)
        _brushControlUi.eraserToolButton.setCheckable(True)
        _brushControlUi.eraserToolButton.clicked.connect( lambda checked: self.handleToolButtonClicked(checked, Tool.Erase) )
        
        # This maps tool types to the buttons that enable them
        self.toolButtons = { Tool.Navigation : _brushControlUi.arrowToolButton,
                             Tool.Paint      : _brushControlUi.paintToolButton,
                             Tool.Erase      : _brushControlUi.eraserToolButton }
        
        self.brushSizes = [ (1,  ""),
                            (3,  "Tiny"),
                            (5,  "Small"),
                            (7,  "Medium"),
                            (11, "Large"),
                            (23, "Huge"),
                            (31, "Megahuge"),
                            (61, "Gigahuge") ]

        for size, name in self.brushSizes:
            _brushControlUi.brushSizeComboBox.addItem( str(size) + " " + name )
        
        _brushControlUi.brushSizeComboBox.currentIndexChanged.connect(self.onBrushSizeChange)
        self.paintBrushSizeIndex = 0
        self.eraserSizeIndex = 4
        
#        self._labelControlUi.checkInteractive.setEnabled(True)
        
    @traceLogged(traceLogger)
    def handleToolButtonClicked(self, checked, toolId):
        """
        Called when the user clicks any of the "tool" buttons in the label applet bar GUI.
        """
        if not checked:
            # Users can only *switch between* tools, not turn them off.
            # If they try to turn a button off, re-select it automatically.
            self.toolButtons[toolId].setChecked(True)
        else:
            # If the user is checking a new button
            self.changeInteractionMode( toolId )

    @traceLogged(traceLogger)
    def changeInteractionMode( self, toolId ):
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
                      Tool.Erase        : "brushing" }

        # Hide everything by default
        self._brushControlUi.arrowToolButton.hide()
        self._brushControlUi.paintToolButton.hide()
        self._brushControlUi.eraserToolButton.hide()
        self._brushControlUi.brushSizeComboBox.hide()
        self._brushControlUi.brushSizeCaption.hide()

        # If the user can't label this image, disable the button and say why its disabled
        labelsAllowed = self.imageIndex >= 0 and self._labelingGuiSlots.labelsAllowed[self.imageIndex].value

        self._labelControlUi.AddLabelButton.setEnabled(labelsAllowed)
        if labelsAllowed:
            self._labelControlUi.AddLabelButton.setText("Add Label")
        else:
            self._labelControlUi.AddLabelButton.setText("(Labeling Not Allowed)")

        if self.imageIndex != -1 and labelsAllowed:
            self._brushControlUi.arrowToolButton.show()
            self._brushControlUi.paintToolButton.show()
            self._brushControlUi.eraserToolButton.show()
            # Update the applet bar caption
            if toolId == Tool.Navigation:
                # Make sure the arrow button is pressed
                self._brushControlUi.arrowToolButton.setChecked(True)
                # Hide the brush size control
                self._brushControlUi.brushSizeCaption.hide()
                self._brushControlUi.brushSizeComboBox.hide()
            elif toolId == Tool.Paint:
                # Make sure the paint button is pressed
                self._brushControlUi.paintToolButton.setChecked(True)
                # Show the brush size control and set its caption
                self._brushControlUi.brushSizeCaption.show()
                self._brushControlUi.brushSizeComboBox.show()
                self._brushControlUi.brushSizeCaption.setText("Brush Size:")
                
                # If necessary, tell the brushing model to stop erasing
                if self.editor.brushingModel.erasing:
                    self.editor.brushingModel.disableErasing()
                # Set the brushing size
                brushSize = self.brushSizes[self.paintBrushSizeIndex][0]
                self.editor.brushingModel.setBrushSize(brushSize)
    
                # Make sure the GUI reflects the correct size
                self._brushControlUi.brushSizeComboBox.setCurrentIndex(self.paintBrushSizeIndex)
                
            elif toolId == Tool.Erase:
                # Make sure the erase button is pressed
                self._brushControlUi.eraserToolButton.setChecked(True)
                # Show the brush size control and set its caption
                self._brushControlUi.brushSizeCaption.show()
                self._brushControlUi.brushSizeComboBox.show()
                self._brushControlUi.brushSizeCaption.setText("Eraser Size:")
                
                # If necessary, tell the brushing model to start erasing
                if not self.editor.brushingModel.erasing:
                    self.editor.brushingModel.setErasing()
                # Set the brushing size
                eraserSize = self.brushSizes[self.eraserSizeIndex][0]
                self.editor.brushingModel.setBrushSize(eraserSize)
                
                # Make sure the GUI reflects the correct size
                self._brushControlUi.brushSizeComboBox.setCurrentIndex(self.eraserSizeIndex)

        self.editor.setInteractionMode( modeNames[toolId] )

    @traceLogged(traceLogger)
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

    @traceLogged(traceLogger)
    def switchLabel(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.labelListModel[row]))
        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        self.editor.brushingModel.setBrushColor(self._labelControlUi.labelListModel[row].color)

    @traceLogged(traceLogger)
    def resetLabelSelection(self):
        logger.debug("Resetting label selection")
        if len(self._labelControlUi.labelListModel) > 0:
            self._labelControlUi.labelListView.selectRow(0)
        else:
            self.changeInteractionMode(Tool.Navigation)
        return True
    
    @traceLogged(traceLogger)
    def handleAddLabelButtonClicked(self):
        """
        The user clicked the "Add Label" button.  Update the GUI and pipeline.
        """
        self.addNewLabel()
    
    @traceLogged(traceLogger)
    def updateLabelList(self):
        """
        This function is called when the number of labels has changed without our knowledge.
        We need to add/remove labels until we have the right number
        """
        # Get the number of labels in the label data
        # (Or the number of the labels the user has added.)
        numLabels = max(self._labelingGuiSlots.maxLabelValue.value, self._labelControlUi.labelListModel.rowCount())
        if numLabels == None:
            numLabels = 0

        # Add rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() < numLabels:
            self.addNewLabel()
        
        # Select a label by default so the brushing controller doesn't get confused.
        if numLabels > 0:
            selectedRow = self._labelControlUi.labelListModel.selectedRow()
            if selectedRow == -1:
                selectedRow = 0
            self.switchLabel(selectedRow)

    @traceLogged(traceLogger)
    def addNewLabel(self):
        """
        Add a new label to the label list GUI control.
        Return the new number of labels in the control.
        """
        numLabels = len(self._labelControlUi.labelListModel)
        if numLabels >= len(self._colorTable16)-1:
            # If the color table isn't large enough to handle all our labels,
            #  append a random color
            randomColor = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
            self._colorTable16.append( randomColor.rgba() )

        color = QColor()
        color.setRgba(self._colorTable16[numLabels+1]) # First entry is transparent (for zero label)
        self._labelControlUi.labelListModel.insertRow(self._labelControlUi.labelListModel.rowCount(), Label("Label %d" % (self._labelControlUi.labelListModel.rowCount() + 1), color))
        nlabels = self._labelControlUi.labelListModel.rowCount()

        #make the new label selected
        self._labelControlUi.labelListView.selectRow(nlabels-1)
        
        return nlabels
    
    @traceLogged(traceLogger)
    def removeLastLabel(self):
        """
        Programmatically (i.e. not from the GUI) reduce the size of the label list by one.
        """
        self._programmaticallyRemovingLabels = True
        numRows = self._labelControlUi.labelListModel.rowCount()
        # This will trigger the signal that calls onLabelAboutToBeRemoved()
        self._labelControlUi.labelListModel.removeRow(numRows-1)
    
        self._programmaticallyRemovingLabels = False
    
    @traceLogged(traceLogger)
    def clearLabelListGui(self):
        # Remove rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() > 0:
            self.removeLastLabel()

    @traceLogged(traceLogger)
    def onLabelAboutToBeRemoved(self, parent, start, end):
        # Don't respond unless this actually came from the GUI
        if self._programmaticallyRemovingLabels:
            return
        
        for il in reversed(range(start, end+1)):
            ncount = self._labelControlUi.labelListModel.rowCount()
            logger.debug("removing label {} out of {}".format( il, ncount ))

            # Changing the deleteLabel input causes the operator (OpBlockedSparseArray)
            #  to search through the entire list of labels and delete the entries for the matching label.
            self._labelingGuiSlots.labelDelete.setValue(il+1)
            
            # We need to "reset" the deleteLabel input to -1 when we're finished.
            #  Otherwise, you can never delete the same label twice in a row.
            #  (Only *changes* to the input are acted upon.)
            self._labelingGuiSlots.labelDelete.setValue(-1)

            # Remove the deleted label's color from the color table so that renumbered labels keep their colors.                
            oldColor = self._colorTable16.pop(il+1)
            
            # Recycle the deleted color back into the table (for the next label to be added)
            self._colorTable16.insert(ncount-end+start, oldColor)

            # Update the labellayer colortable with the new color mapping
            labellayer = self.getLabelLayer()
            labellayer.colorTable = self._colorTable16
        
        currentSelection = self._labelControlUi.labelListModel.selectedRow()
        if currentSelection == -1:
            # If we're deleting the currently selected row, then switch to a different row
            self.thunkEventHandler.post( self.resetLabelSelection )

    def getLabelLayer(self):
        # Find the labellayer in the viewer stack
        try:
            labellayer = itertools.ifilter(lambda l: l.name == "Labels", self.layerstack).next()
        except StopIteration:
            raise RuntimeError("Couldn't locate the label layer in the layer stack.  Does it have the expected name?")
        return labellayer

    @traceLogged(traceLogger)
    def createLabelLayer(self, currentImageIndex):
        """
        Return a colortable layer that displays the label slot data, along with its associated label source.
        """
        labelOutput = self._labelingGuiSlots.labelOutput[currentImageIndex]
        if not labelOutput.ready():
            return (None, None)
        else:
            traceLogger.debug("Setting up labels for image index={}".format(self.imageIndex) )
            # Add the layer to draw the labels, but don't add any labels
            labelsrc = LazyflowSinkSource(self.pipeline,
                                           self.pipeline.LabelImages[self.imageIndex],
                                           self.pipeline.LabelInputs[self.imageIndex])
            #labelsrc.setObjectName("labels")
        
            labellayer = ColortableLayer(labelsrc, colorTable = self._colorTable16 )
            labellayer.name = "Labels"
            labellayer.ref_object = None
            
            return labellayer, labelsrc

    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        """
        Sets up the label layer for display by our base class (layerviewer).
        If our subclass overrides this function to add his own layers,
        he must call this function explicitly.
        """
        layers = []

        # Labels
        labellayer, labelsrc = self.createLabelLayer(currentImageIndex)
        if labellayer is not None:
            layers.append(labellayer)
        
            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)
        
        # Side effect: Switch to navigation mode if labels aren't allowed on this image.
        labelsAllowedSlot = self._labelingGuiSlots.labelsAllowed[self.imageIndex]
        if labelsAllowedSlot.ready() and not labelsAllowedSlot.value:
            self.changeInteractionMode(Tool.Navigation)

        return layers
        
    @traceLogged(traceLogger)
    def _createDefault16ColorColorTable(self):
        colors = []
        colors.append(QColor(0,0,0,0)) # Transparent for the zero label
        colors.append(QColor(0, 0, 255))
        colors.append(QColor(255, 255, 0))
        colors.append(QColor(255, 0, 0))
        colors.append(QColor(0, 255, 0))
        colors.append(QColor(0, 255, 255))
        colors.append(QColor(255, 0, 255))
        colors.append(QColor(255, 105, 180)) #hot pink
        colors.append(QColor(102, 205, 170)) #dark aquamarine
        colors.append(QColor(165,  42,  42)) #brown        
        colors.append(QColor(0, 0, 128))     #navy
        colors.append(QColor(255, 165, 0))   #orange
        colors.append(QColor(173, 255,  47)) #green-yellow
        colors.append(QColor(128,0, 128))    #purple
        colors.append(QColor(192, 192, 192)) #silver
        colors.append(QColor(240, 230, 140)) #khaki
        colors.append(QColor(69, 69, 69))    # dark grey
        
        return [c.rgba() for c in colors]































