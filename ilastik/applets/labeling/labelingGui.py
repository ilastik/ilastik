# Built-in
import os
import re
import logging
import itertools
from functools import partial

# Third-party
import numpy
from PyQt4 import uic
from PyQt4.QtCore import QRectF, Qt
from PyQt4.QtGui import QIcon, QColor, QShortcut, QKeySequence, QWidget

# HCI
from lazyflow.utility import traceLogged
from volumina.api import LazyflowSinkSource, ColortableLayer
from volumina.utility import ShortcutManager, PreferencesManager
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.widgets.labelListView import Label
from ilastik.widgets.labelListModel import LabelListModel

# ilastik
from ilastik.utility import bind 
from ilastik.utility.gui import ThunkEventHandler, threadRouted
from ilastik.applets.layerViewer import LayerViewerGui

# Loggers
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

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

    def appletDrawer(self):
        return self._labelControlUi

    def reset(self):
        super(LabelingGui, self).reset()

        # Clear the label list GUI
        self._clearLabelListGui()

        # Start in navigation mode (not painting)
        self._changeInteractionMode(Tool.Navigation)

    ###########################################
    ###########################################

    @property
    def minLabelNumber(self):
        return self._minLabelNumber
    @minLabelNumber.setter
    def minLabelNumber(self, n):
        self._minLabelNumer = n
        while self._labelControlUi.labelListModel.rowCount() < n:
            self._addNewLabel()
    @property
    def maxLabelNumber(self):
        return self._maxLabelNumber
    @maxLabelNumber.setter
    def maxLabelNumber(self, n):
        self._maxLabelNumber = n
        while self._labelControlUi.labelListModel.rowCount() < n:
            self._removeLastLabel()

    @property
    def labelingDrawerUi(self):
        return self._labelControlUi

    @property
    def labelListData(self):
        return self._labelControlUi.labelListModel

    def selectLabel(self, labelIndex):
        """Programmatically select the given labelIndex, which start from 0.
           Equivalent to clicking on the (labelIndex+1)'th position in the label widget."""
        self._labelControlUi.labelListModel.select(labelIndex)

    class LabelingSlots(object):
        """
        This class serves as the parameter for the LabelingGui constructor.
        It provides the slots that the labeling GUI uses to source labels to the display and sink labels from the user's mouse clicks.
        """
        def __init__(self):
            # Slot to insert labels onto
            self.labelInput = None # labelInput.setInSlot(xxx)
            # Slot to read labels from
            self.labelOutput = None # labelOutput.get(roi)
            # Slot that determines which label value corresponds to erased values
            self.labelEraserValue = None # labelEraserValue.setValue(xxx)
            # Slot that is used to request wholesale label deletion
            self.labelDelete = None # labelDelete.setValue(xxx)
            # Slot that contains the maximum label value (for all images)
            self.maxLabelValue = None # maxLabelValue.value

            # Slot to specify which images the user is allowed to label.
            self.labelsAllowed = None # labelsAllowed.value == True

    @traceLogged(traceLogger)
    def __init__(self, labelingSlots, topLevelOperatorView, drawerUiPath=None, rawInputSlot=None ):
        """
        Constructor.

        :param labelingSlots: Provides the slots needed for sourcing/sinking label data.  See LabelingGui.LabelingSlots class source for details.
        :param topLevelOperatorView: is provided to the LayerViewerGui (the base class)
        :param drawerUiPath: can be given if you provide an extended drawer UI file.  Otherwise a default one is used.
        :param rawInputSlot: Data from the rawInputSlot parameter will be displayed directly underneath the labels (if provided).
        """

        # Do have have all the slots we need?
        assert isinstance(labelingSlots, LabelingGui.LabelingSlots)
        assert all( [v is not None for v in labelingSlots.__dict__.values()] )

        self._labelingSlots = labelingSlots
        self._minLabelNumber = 0
        self._maxLabelNumber = 99 #100 or 255 is reserved for eraser

        self._rawInputSlot = rawInputSlot

        self._labelingSlots.maxLabelValue.notifyDirty( bind(self._updateLabelList) )

        self._colorTable16 = self._createDefault16ColorColorTable()
        self._programmaticallyRemovingLabels = False

        if drawerUiPath is None:
            # Default ui file
            drawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'
        self._initLabelUic(drawerUiPath)

        # Init base class
        super(LabelingGui, self).__init__( topLevelOperatorView, [labelingSlots.labelInput, labelingSlots.labelOutput] )

        self.__initShortcuts()
        self._labelingSlots.labelEraserValue.setValue(self.editor.brushingModel.erasingNumber)

        # Register for thunk events (easy UI calls from non-GUI threads)
        self.thunkEventHandler = ThunkEventHandler(self)
        self._changeInteractionMode(Tool.Navigation)

    @traceLogged(traceLogger)
    def _initLabelUic(self, drawerUiPath):
        _labelControlUi = uic.loadUi(drawerUiPath)

        # We own the applet bar ui
        self._labelControlUi = _labelControlUi

        # Initialize the label list model
        model = LabelListModel()
        _labelControlUi.labelListView.setModel(model)
        _labelControlUi.labelListModel=model
        _labelControlUi.labelListModel.rowsRemoved.connect(self._onLabelRemoved)
        _labelControlUi.labelListModel.labelSelected.connect(self._onLabelSelected)

        # Connect Applet GUI to our event handlers
        _labelControlUi.AddLabelButton.setIcon( QIcon(ilastikIcons.AddSel) )
        _labelControlUi.AddLabelButton.clicked.connect( bind(self._addNewLabel) )
        _labelControlUi.labelListModel.dataChanged.connect(self.onLabelListDataChanged)

        # Initialize the arrow tool button with an icon and handler
        iconPath = os.path.split(__file__)[0] + "/icons/arrow.png"
        arrowIcon = QIcon(iconPath)
        _labelControlUi.arrowToolButton.setIcon(arrowIcon)
        _labelControlUi.arrowToolButton.setCheckable(True)
        _labelControlUi.arrowToolButton.clicked.connect( lambda checked: self._handleToolButtonClicked(checked, Tool.Navigation) )

        # Initialize the paint tool button with an icon and handler
        paintBrushIconPath = os.path.split(__file__)[0] + "/icons/paintbrush.png"
        paintBrushIcon = QIcon(paintBrushIconPath)
        _labelControlUi.paintToolButton.setIcon(paintBrushIcon)
        _labelControlUi.paintToolButton.setCheckable(True)
        _labelControlUi.paintToolButton.clicked.connect( lambda checked: self._handleToolButtonClicked(checked, Tool.Paint) )

        # Initialize the erase tool button with an icon and handler
        eraserIconPath = os.path.split(__file__)[0] + "/icons/eraser.png"
        eraserIcon = QIcon(eraserIconPath)
        _labelControlUi.eraserToolButton.setIcon(eraserIcon)
        _labelControlUi.eraserToolButton.setCheckable(True)
        _labelControlUi.eraserToolButton.clicked.connect( lambda checked: self._handleToolButtonClicked(checked, Tool.Erase) )

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

        _labelControlUi.brushSizeComboBox.currentIndexChanged.connect(self._onBrushSizeChange)

        self.paintBrushSizeIndex = PreferencesManager().get( 'labeling', 'paint brush size', default=0 )
        self.eraserSizeIndex = PreferencesManager().get( 'labeling', 'eraser brush size', default=4 )

    @traceLogged(traceLogger)
    def onLabelListDataChanged(self, topLeft, bottomRight):
        """Handle changes to the label list selections."""
        firstRow = topLeft.row()
        lastRow  = bottomRight.row()

        firstCol = topLeft.column()
        lastCol  = bottomRight.column()

        # We only care about the color column
        if firstCol <= 0 <= lastCol:
            assert(firstRow == lastRow) # Only one data item changes at a time

            #in this case, the actual data (for example color) has changed
            color = self._labelControlUi.labelListModel[firstRow].brushColor()
            pmapColor = self._labelControlUi.labelListModel[firstRow].pmapColor()
            self._colorTable16[firstRow+1] = color.rgba()
            self.editor.brushingModel.setBrushColor(color)

            # Update the label layer colortable to match the list entry
            labellayer = self._getLabelLayer()
            if labellayer is not None:
                labellayer.colorTable = self._colorTable16

    def __initShortcuts(self):
        mgr = ShortcutManager()
        shortcutGroupName = "Labeling"

        addLabel = QShortcut( QKeySequence("a"), self, member=self.labelingDrawerUi.AddLabelButton.click )
        mgr.register( shortcutGroupName,
                      "Add New Label Class",
                      addLabel,
                      self.labelingDrawerUi.AddLabelButton )

        navMode = QShortcut( QKeySequence("n"), self, member=self.labelingDrawerUi.arrowToolButton.click )
        mgr.register( shortcutGroupName,
                      "Navigation Cursor",
                      navMode,
                      self.labelingDrawerUi.arrowToolButton )

        brushMode = QShortcut( QKeySequence("b"), self, member=self.labelingDrawerUi.paintToolButton.click )
        mgr.register( shortcutGroupName,
                      "Brush Cursor",
                      brushMode,
                      self.labelingDrawerUi.paintToolButton )

        eraserMode = QShortcut( QKeySequence("e"), self, member=self.labelingDrawerUi.eraserToolButton.click )
        mgr.register( shortcutGroupName,
                      "Eraser Cursor",
                      eraserMode,
                      self.labelingDrawerUi.eraserToolButton )

        changeBrushSize = QShortcut( QKeySequence("c"), self, member=self.labelingDrawerUi.brushSizeComboBox.showPopup )
        mgr.register( shortcutGroupName,
                      "Change Brush Size",
                      changeBrushSize,
                      self.labelingDrawerUi.brushSizeComboBox )


        self._labelShortcuts = []

    def _updateLabelShortcuts(self):
        numShortcuts = len(self._labelShortcuts)
        numRows = len(self._labelControlUi.labelListModel)

        # Add any shortcuts we don't have yet.
        for i in range(numShortcuts,numRows):
            shortcut = QShortcut( QKeySequence(str(i+1)),
                                  self,
                                  member=partial(self._labelControlUi.labelListView.selectRow, i) )
            self._labelShortcuts.append(shortcut)
            toolTipObject = LabelListModel.EntryToolTipAdapter(self._labelControlUi.labelListModel, i)
            ShortcutManager().register("Labeling", "", shortcut, toolTipObject)

        # Make sure that all shortcuts have an appropriate description
        for i in range(numRows):
            shortcut = self._labelShortcuts[i]
            description = "Select " + self._labelControlUi.labelListModel[i].name
            ShortcutManager().setDescription(shortcut, description)

    def hideEvent(self, event):
        """
        QT event handler.
        The user has selected another applet or is closing the whole app.
        Save all preferences.
        """
        with PreferencesManager() as prefsMgr:
            prefsMgr.set('labeling', 'paint brush size', self.paintBrushSizeIndex)
            prefsMgr.set('labeling', 'eraser brush size', self.eraserSizeIndex)
        super(LabelingGui, self).hideEvent(event)

    @traceLogged(traceLogger)
    def _handleToolButtonClicked(self, checked, toolId):
        """
        Called when the user clicks any of the "tool" buttons in the label applet bar GUI.
        """
        if not checked:
            # Users can only *switch between* tools, not turn them off.
            # If they try to turn a button off, re-select it automatically.
            self.toolButtons[toolId].setChecked(True)
        else:
            # If the user is checking a new button
            self._changeInteractionMode( toolId )

    @threadRouted
    @traceLogged(traceLogger)
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
                      Tool.Erase        : "brushing" }

        # Hide everything by default
        self._labelControlUi.arrowToolButton.hide()
        self._labelControlUi.paintToolButton.hide()
        self._labelControlUi.eraserToolButton.hide()
        self._labelControlUi.brushSizeComboBox.hide()
        self._labelControlUi.brushSizeCaption.hide()

        # If the user can't label this image, disable the button and say why its disabled
        labelsAllowed = False

        labelsAllowedSlot = self._labelingSlots.labelsAllowed
        if labelsAllowedSlot.ready():
            labelsAllowed = labelsAllowedSlot.value

            self._labelControlUi.AddLabelButton.setEnabled(labelsAllowed and self.maxLabelNumber > self._labelControlUi.labelListModel.rowCount())
            if labelsAllowed:
                self._labelControlUi.AddLabelButton.setText("Add Label")
            else:
                self._labelControlUi.AddLabelButton.setText("(Labeling Not Allowed)")

        if labelsAllowed:
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
                self._labelControlUi.brushSizeCaption.setText("Size:")

                # If necessary, tell the brushing model to stop erasing
                if self.editor.brushingModel.erasing:
                    self.editor.brushingModel.disableErasing()
                # Set the brushing size
                brushSize = self.brushSizes[self.paintBrushSizeIndex][0]
                self.editor.brushingModel.setBrushSize(brushSize)

                # Make sure the GUI reflects the correct size
                self._labelControlUi.brushSizeComboBox.setCurrentIndex(self.paintBrushSizeIndex)

            elif toolId == Tool.Erase:
                # Make sure the erase button is pressed
                self._labelControlUi.eraserToolButton.setChecked(True)
                # Show the brush size control and set its caption
                self._labelControlUi.brushSizeCaption.show()
                self._labelControlUi.brushSizeComboBox.show()
                self._labelControlUi.brushSizeCaption.setText("Size:")

                # If necessary, tell the brushing model to start erasing
                if not self.editor.brushingModel.erasing:
                    self.editor.brushingModel.setErasing()
                # Set the brushing size
                eraserSize = self.brushSizes[self.eraserSizeIndex][0]
                self.editor.brushingModel.setBrushSize(eraserSize)

                # Make sure the GUI reflects the correct size
                self._labelControlUi.brushSizeComboBox.setCurrentIndex(self.eraserSizeIndex)

        self.editor.setInteractionMode( modeNames[toolId] )
        self._toolId = toolId

    @traceLogged(traceLogger)
    def _onBrushSizeChange(self, index):
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
    def _onLabelSelected(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.labelListModel[row]))

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Paint)

        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        brushColor = self._labelControlUi.labelListModel[row].brushColor()
        self.editor.brushingModel.setBrushColor( brushColor )

    @traceLogged(traceLogger)
    def _resetLabelSelection(self):
        logger.debug("Resetting label selection")
        if len(self._labelControlUi.labelListModel) > 0:
            self._labelControlUi.labelListView.selectRow(0)
        else:
            self._changeInteractionMode(Tool.Navigation)
        return True

    @traceLogged(traceLogger)
    def _updateLabelList(self):
        """
        This function is called when the number of labels has changed without our knowledge.
        We need to add/remove labels until we have the right number
        """
        # Get the number of labels in the label data
        # (Or the number of the labels the user has added.)
        numLabels = max(self._labelingSlots.maxLabelValue.value, self._labelControlUi.labelListModel.rowCount())
        if numLabels == None:
            numLabels = 0

        # Add rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() < numLabels:
            self._addNewLabel()

        self._labelControlUi.AddLabelButton.setEnabled(numLabels < self.maxLabelNumber)

    @traceLogged(traceLogger)
    def _addNewLabel(self):
        """
        Add a new label to the label list GUI control.
        Return the new number of labels in the control.
        """
        label = Label( self.getNextLabelName(), self.getNextLabelColor() )
        label.nameChanged.connect(self._updateLabelShortcuts)
        label.nameChanged.connect(self.onLabelNameChanged)
        label.colorChanged.connect(self.onLabelColorChanged)
        label.pmapColorChanged.connect(self.onPmapColorChanged)

        newRow = self._labelControlUi.labelListModel.rowCount()
        self._labelControlUi.labelListModel.insertRow( newRow, label )
        newColorIndex = self._labelControlUi.labelListModel.index(newRow, 0)
        self.onLabelListDataChanged(newColorIndex, newColorIndex) # Make sure label layer colortable is in sync with the new color

        # Call the 'changed' callbacks immediately to initialize any listeners
        self.onLabelNameChanged()
        self.onLabelColorChanged()
        self.onPmapColorChanged()

        # Make the new label selected
        nlabels = self._labelControlUi.labelListModel.rowCount()
        selectedRow = nlabels-1
        self._labelControlUi.labelListModel.select(selectedRow)

        self._updateLabelShortcuts()

    def getNextLabelName(self):
        """
        Return a suitable name for the next label added by the user.
        Subclasses may override this.
        """
        maxNum = 0
        for index, label in enumerate(self._labelControlUi.labelListModel):
            nums = re.findall("\d+", label.name)
            for n in nums:
                maxNum = max(maxNum, int(n))
        return "Label {}".format(maxNum+1)

    def getNextLabelColor(self):
        """
        Return a QColor to use for the next label.
        """
        numLabels = len(self._labelControlUi.labelListModel)
        if numLabels >= len(self._colorTable16)-1:
            # If the color table isn't large enough to handle all our labels,
            #  append a random color
            randomColor = QColor(numpy.random.randint(0,255), numpy.random.randint(0,255), numpy.random.randint(0,255))
            self._colorTable16.append( randomColor.rgba() )

        color = QColor()
        color.setRgba(self._colorTable16[numLabels+1]) # First entry is transparent (for zero label)
        return color

    def onLabelNameChanged(self):
        """
        Subclasses can override this to respond to changes in the label names.
        """
        pass

    def onLabelColorChanged(self):
        """
        Subclasses can override this to respond to changes in the label colors.
        """
        pass
    
    def onPmapColorChanged(self):
        """
        Subclasses can override this to respond to changes in a label associated probability color.
        """
        pass

    @traceLogged(traceLogger)
    def _removeLastLabel(self):
        """
        Programmatically (i.e. not from the GUI) reduce the size of the label list by one.
        """
        self._programmaticallyRemovingLabels = True
        numRows = self._labelControlUi.labelListModel.rowCount()
        # This will trigger the signal that calls _onLabelRemoved()
        self._labelControlUi.labelListModel.removeRow(numRows-1)
        self._updateLabelShortcuts()

        self._programmaticallyRemovingLabels = False

    @traceLogged(traceLogger)
    def _clearLabelListGui(self):
        # Remove rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() > 0:
            self._removeLastLabel()

    @traceLogged(traceLogger)
    def _onLabelRemoved(self, parent, start, end):
        # Don't respond unless this actually came from the GUI
        if self._programmaticallyRemovingLabels:
            return

        assert start == end
        row = start

        oldcount = self._labelControlUi.labelListModel.rowCount() + 1
        logger.debug("removing label {} out of {}".format( row, oldcount ))

        # Remove the deleted label's color from the color table so that renumbered labels keep their colors.
        oldColor = self._colorTable16.pop(row+1)

        # Recycle the deleted color back into the table (for the next label to be added)
        self._colorTable16.insert(oldcount, oldColor)

        # Update the labellayer colortable with the new color mapping
        labellayer = self._getLabelLayer()
        if labellayer is not None:
            labellayer.colorTable = self._colorTable16

        currentSelection = self._labelControlUi.labelListModel.selectedRow()
        if currentSelection == -1:
            # If we're deleting the currently selected row, then switch to a different row
            self.thunkEventHandler.post( self._resetLabelSelection )

        # Changing the deleteLabel input causes the operator (OpBlockedSparseArray)
        #  to search through the entire list of labels and delete the entries for the matching label.
        self._labelingSlots.labelDelete.setValue(row+1)

        # We need to "reset" the deleteLabel input to -1 when we're finished.
        #  Otherwise, you can never delete the same label twice in a row.
        #  (Only *changes* to the input are acted upon.)
        self._labelingSlots.labelDelete.setValue(-1)

    def _getLabelLayer(self):
        # Find the labellayer in the viewer stack
        try:
            labellayer = itertools.ifilter(lambda l: l.name == "Labels", self.layerstack).next()
        except StopIteration:
            return None
        else:
            return labellayer

    @traceLogged(traceLogger)
    def createLabelLayer(self, direct=False):
        """
        Return a colortable layer that displays the label slot data, along with its associated label source.
        direct: whether this layer is drawn synchronously by volumina
        """
        labelOutput = self._labelingSlots.labelOutput
        if not labelOutput.ready():
            return (None, None)
        else:
            traceLogger.debug("Setting up labels" )
            # Add the layer to draw the labels, but don't add any labels
            labelsrc = LazyflowSinkSource( self._labelingSlots.labelOutput,
                                           self._labelingSlots.labelInput)

            labellayer = ColortableLayer(labelsrc, colorTable = self._colorTable16, direct=direct )
            labellayer.name = "Labels"
            labellayer.ref_object = None

            return labellayer, labelsrc

    @traceLogged(traceLogger)
    def setupLayers(self):
        """
        Sets up the label layer for display by our base class (LayerViewerGui).
        If our subclass overrides this function to add his own layers,
        he **must** call this function explicitly.
        """
        layers = []

        # Labels
        labellayer, labelsrc = self.createLabelLayer()
        if labellayer is not None:
            layers.append(labellayer)

            # Tell the editor where to draw label data
            self.editor.setLabelSink(labelsrc)

        # Side effect 1: We want to guarantee that the label list
        #  is up-to-date before our subclass adds his layers
        self._updateLabelList()

        # Side effect 2: Switch to navigation mode if labels aren't
        #  allowed on this image.
        labelsAllowedSlot = self._labelingSlots.labelsAllowed
        if labelsAllowedSlot.ready() and not labelsAllowedSlot.value:
            self._changeInteractionMode(Tool.Navigation)

        # Raw Input Layer
        if self._rawInputSlot is not None and self._rawInputSlot.ready():
            layer = self.createStandardLayerFromSlot( self._rawInputSlot )
            layer.name = "Raw Input"
            layer.visible = True
            layer.opacity = 1.0

            layers.append(layer)

        return layers

    @traceLogged(traceLogger)
    def _createDefault16ColorColorTable(self):
        colors = []

        # Transparent for the zero label
        colors.append(QColor(0,0,0,0))

        # ilastik v0.5 colors
        colors.append( QColor( Qt.red ) )
        colors.append( QColor( Qt.green ) )
        colors.append( QColor( Qt.yellow ) )
        colors.append( QColor( Qt.blue ) )
        colors.append( QColor( Qt.magenta ) )
        colors.append( QColor( Qt.darkYellow ) )
        colors.append( QColor( Qt.lightGray ) )

        # Additional colors
        colors.append( QColor(255, 105, 180) ) #hot pink
        colors.append( QColor(102, 205, 170) ) #dark aquamarine
        colors.append( QColor(165,  42,  42) ) #brown
        colors.append( QColor(0, 0, 128) )     #navy
        colors.append( QColor(255, 165, 0) )   #orange
        colors.append( QColor(173, 255,  47) ) #green-yellow
        colors.append( QColor(128,0, 128) )    #purple
        colors.append( QColor(240, 230, 140) ) #khaki

#        colors.append( QColor(192, 192, 192) ) #silver
#        colors.append( QColor(69, 69, 69) )    # dark grey
#        colors.append( QColor( Qt.cyan ) )

        assert len(colors) == 16

        return [c.rgba() for c in colors]
