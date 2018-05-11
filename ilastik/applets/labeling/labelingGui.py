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
from builtins import range
from builtins import filter
import os
import re
import logging
import itertools
from functools import partial

# Third-party
import numpy
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox, QAction

# HCI
from volumina.api import LazyflowSinkSource, ColortableLayer
from volumina.utility import ShortcutManager, PreferencesManager
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.widgets.labelListView import Label
from ilastik.widgets.labelListModel import LabelListModel
from volumina import colortables

# ilastik
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThunkEventHandler, threadRouted
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

from ilastik.applets.labeling.labelingImport import import_labeling_layer


# Loggers
logger = logging.getLogger(__name__)

#===----------------------------------------------------------------------------------------------------------------===

class Tool(object):
    """Enumerate the types of toolbar buttons."""
    Navigation = 0 # Arrow
    Paint      = 1
    Erase      = 2
    Threshold  = 3

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

    def stopAndCleanUp(self):
        super(LabelingGui, self).stopAndCleanUp()

        for fn in self.__cleanup_fns:
            fn()

    ###########################################
    ###########################################

    @property
    def minLabelNumber(self):
        return self._minLabelNumber
    @minLabelNumber.setter
    def minLabelNumber(self, n):
        self._minLabelNumber = n
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
        It provides the slots that the labeling GUI uses to source labels to the display and sink labels from the
        user's mouse clicks.
        """
        def __init__(self):
            # Slot to insert elements onto
            self.labelInput = None # labelInput.setInSlot(xxx)
            # Slot to read elements from
            self.labelOutput = None # labelOutput.get(roi)
            # Slot that determines which label value corresponds to erased values
            self.labelEraserValue = None # labelEraserValue.setValue(xxx)
            # Slot that is used to request wholesale label deletion
            self.labelDelete = None # labelDelete.setValue(xxx)
            # Slot that gives a list of label names
            self.labelNames = None # labelNames.value

    def __init__(self, parentApplet, labelingSlots, topLevelOperatorView, drawerUiPath=None, rawInputSlot=None,
                 crosshair=True, is_3d_widget_visible=False):
        """
        Constructor.

        :param labelingSlots: Provides the slots needed for sourcing/sinking label data.  See LabelingGui.LabelingSlots
                              class source for details.
        :param topLevelOperatorView: is provided to the LayerViewerGui (the base class)
        :param drawerUiPath: can be given if you provide an extended drawer UI file.  Otherwise a default one is used.
        :param rawInputSlot: Data from the rawInputSlot parameter will be displayed directly underneath the elements
                             (if provided).
        """

        self._colorTable16 = list(colortables.default16_new)

        # Do have have all the slots we need?
        assert isinstance(labelingSlots, LabelingGui.LabelingSlots)
        assert labelingSlots.labelInput is not None, "Missing a required slot."
        assert labelingSlots.labelOutput is not None, "Missing a required slot."
        assert labelingSlots.labelEraserValue is not None, "Missing a required slot."
        assert labelingSlots.labelDelete is not None, "Missing a required slot."
        assert labelingSlots.labelNames is not None, "Missing a required slot."

        self.__cleanup_fns = []

        self._labelingSlots = labelingSlots
        self._minLabelNumber = 0
        self._maxLabelNumber = 99 #100 or 255 is reserved for eraser

        self._rawInputSlot = rawInputSlot

        self._labelingSlots.labelNames.notifyDirty( bind(self._updateLabelList) )
        self.__cleanup_fns.append( partial( self._labelingSlots.labelNames.unregisterDirty, bind(self._updateLabelList) ) )


<<<<<<< edad89c79ea401f8f3d79d2b69ae172f643457ec
        self._colorTable16 = colortables.default16_new
=======
>>>>>>> fixes for labeling and pixel classification gui to use the common default label colors
        self._programmaticallyRemovingLabels = False

        if drawerUiPath is None:
            # Default ui file
            drawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'
        self._initLabelUic(drawerUiPath)

        # Init base class
        super(LabelingGui, self).__init__(parentApplet,
                                          topLevelOperatorView,
                                          [labelingSlots.labelInput, labelingSlots.labelOutput],
                                          crosshair=crosshair,
                                          is_3d_widget_visible=is_3d_widget_visible)

        self.__initShortcuts()
        self._labelingSlots.labelEraserValue.setValue(self.editor.brushingModel.erasingNumber)
        self._allowDeleteLastLabelOnly = False

        # Register for thunk events (easy UI calls from non-GUI threads)
        self.thunkEventHandler = ThunkEventHandler(self)
        self._changeInteractionMode(Tool.Navigation)

    def _initLabelUic(self, drawerUiPath):
        _labelControlUi = uic.loadUi(drawerUiPath)

        # We own the applet bar ui
        self._labelControlUi = _labelControlUi

        # Initialize the label list model
        model = LabelListModel()
        _labelControlUi.labelListView.setModel(model)
        _labelControlUi.labelListModel=model
        _labelControlUi.labelListModel.rowsRemoved.connect(self._onLabelRemoved)
        _labelControlUi.labelListModel.elementSelected.connect(self._onLabelSelected)

        def handleClearRequested( row, name ):
            selection = QMessageBox.warning(self, "Clear labels?",
                          "All '{}' brush strokes will be erased.  Are you sure?"
                          .format(name),
                          QMessageBox.Ok | QMessageBox.Cancel)
            if selection != QMessageBox.Ok:
                return

            # This only works if the top-level operator has a 'clearLabel' function.
            self.topLevelOperatorView.clearLabel( row+1 )

        _labelControlUi.labelListView.clearRequested.connect( handleClearRequested )

        def handleLabelMergeRequested(from_row, from_name, into_row, into_name):
            from_label = from_row+1
            into_label = into_row+1
            selection = QMessageBox.warning(self, "Merge labels?",
                          "All '{}' brush strokes will be converted to '{}'.  Are you sure?"
                          .format(from_name, into_name),
                          QMessageBox.Ok | QMessageBox.Cancel)
            if selection != QMessageBox.Ok:
                return

            # This only works if the top-level operator has a 'mergeLabels' function.
            self.topLevelOperatorView.mergeLabels( from_label, into_label )

            names = list(self._labelingSlots.labelNames.value)
            names.pop(from_label-1)
            self._labelingSlots.labelNames.setValue( names )

        _labelControlUi.labelListView.mergeRequested.connect( handleLabelMergeRequested )

        # Connect Applet GUI to our event handlers
        if hasattr(_labelControlUi, "AddLabelButton"):
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

        # Initialize the thresholding tool
        if hasattr(_labelControlUi, "thresToolButton"):
            thresholdIconPath = os.path.split(__file__)[0] \
              + "/icons/threshold.png"
            thresholdIcon = QIcon(thresholdIconPath)
            _labelControlUi.thresToolButton.setIcon(thresholdIcon)
            _labelControlUi.thresToolButton.setCheckable(True)
            _labelControlUi.thresToolButton.clicked.connect( lambda checked: self._handleToolButtonClicked(checked, Tool.Threshold) )


        # This maps tool types to the buttons that enable them
        if hasattr(_labelControlUi, "thresToolButton"):
            self.toolButtons = { Tool.Navigation : _labelControlUi.arrowToolButton,
                                 Tool.Paint      : _labelControlUi.paintToolButton,
                                 Tool.Erase      : _labelControlUi.eraserToolButton,
                                 Tool.Threshold  : _labelControlUi.thresToolButton}
        else:
            self.toolButtons = { Tool.Navigation : _labelControlUi.arrowToolButton,
                                 Tool.Paint      : _labelControlUi.paintToolButton,
                                 Tool.Erase      : _labelControlUi.eraserToolButton}
            
        self.brushSizes = [ 1, 3, 5, 7, 11, 23, 31, 61 ]

        for size in self.brushSizes:
            _labelControlUi.brushSizeComboBox.addItem( str(size) )

        _labelControlUi.brushSizeComboBox.currentIndexChanged.connect(self._onBrushSizeChange)

        self.paintBrushSizeIndex = PreferencesManager().get( 'labeling', 'paint brush size', default=0 )
        self.eraserSizeIndex = PreferencesManager().get( 'labeling', 'eraser brush size', default=4 )

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
            color_value = color.rgba()
            color_index = firstRow + 1
            if color_index< len(self._colorTable16):
<<<<<<< edad89c79ea401f8f3d79d2b69ae172f643457ec
                self._colorTable16[color_index] = color_value
=======
                self._colorTable16[color_index] = QColor(color_value)
>>>>>>> fixes for labeling and pixel classification gui to use the common default label colors
            else:
                self._colorTable16.append(color_value)
            self.editor.brushingModel.setBrushColor(color)

            # Update the label layer colortable to match the list entry
            labellayer = self._getLabelLayer()
            if labellayer is not None:
                labellayer.colorTable = self._colorTable16

    def __initShortcuts(self):
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcutGroupName = "Labeling"

        if hasattr(self.labelingDrawerUi, "AddLabelButton"):

            mgr.register("a", ActionInfo( shortcutGroupName,
                                          "New Label",
                                          "Add New Label Class",
                                          self.labelingDrawerUi.AddLabelButton.click,
                                          self.labelingDrawerUi.AddLabelButton,
                                          self.labelingDrawerUi.AddLabelButton ) )

        mgr.register( "n", ActionInfo( shortcutGroupName,
                                       "Navigation Cursor",
                                       "Navigation Cursor",
                                       self.labelingDrawerUi.arrowToolButton.click,
                                       self.labelingDrawerUi.arrowToolButton,
                                       self.labelingDrawerUi.arrowToolButton ) )

        mgr.register( "b", ActionInfo( shortcutGroupName,
                                       "Brush Cursor",
                                       "Brush Cursor",
                                       self.labelingDrawerUi.paintToolButton.click,
                                       self.labelingDrawerUi.paintToolButton,
                                       self.labelingDrawerUi.paintToolButton ) )

        mgr.register( "e", ActionInfo( shortcutGroupName,
                                       "Eraser Cursor",
                                       "Eraser Cursor",
                                       self.labelingDrawerUi.eraserToolButton.click,
                                       self.labelingDrawerUi.eraserToolButton,
                                       self.labelingDrawerUi.eraserToolButton ) )

        mgr.register( ",", ActionInfo( shortcutGroupName,
                                       "Decrease Brush Size",
                                       "Decrease Brush Size",
                                       partial(self._tweakBrushSize, False),
                                       self.labelingDrawerUi.brushSizeComboBox,
                                       self.labelingDrawerUi.brushSizeComboBox ) )

        mgr.register( ".", ActionInfo( shortcutGroupName,
                                       "Increase Brush Size",
                                       "Increase Brush Size",
                                       partial(self._tweakBrushSize, True),
                                       self.labelingDrawerUi.brushSizeComboBox,
                                       self.labelingDrawerUi.brushSizeComboBox ) )

        if hasattr(self.labelingDrawerUi, "thresToolButton"):
            mgr.register( "t", ActionInfo( shortcutGroupName,
                                           "Window Leveling",
                                           "<p>Window Leveling can be used to adjust the data range used for visualization. Pressing the left mouse button while moving the mouse back and forth changes the window width (data range). Moving the mouse in the left-right plane changes the window mean. Pressing the right mouse button resets the view back to the original data.",
                                           self.labelingDrawerUi.thresToolButton.click,
                                           self.labelingDrawerUi.thresToolButton,
                                           self.labelingDrawerUi.thresToolButton ) )
        

        self._labelShortcuts = []

    def _tweakBrushSize(self, increase):
        """
        Increment or decrement the paint brush size or eraser size (depending on which is currently selected).
        
        increase: Bool. If True, increment.  Otherwise, decrement.
        """
        if self._toolId == Tool.Erase:
            if increase:
                self.eraserSizeIndex += 1
                self.eraserSizeIndex = min(len(self.brushSizes)-1, self.eraserSizeIndex)
            else:
                self.eraserSizeIndex -=1
                self.eraserSizeIndex = max(0, self.eraserSizeIndex)
            self._changeInteractionMode(Tool.Erase)
        else:
            if increase:
                self.paintBrushSizeIndex += 1
                self.paintBrushSizeIndex = min(len(self.brushSizes)-1, self.paintBrushSizeIndex)
            else:
                self.paintBrushSizeIndex -=1
                self.paintBrushSizeIndex = max(0, self.paintBrushSizeIndex)
            self._changeInteractionMode(Tool.Paint)

    def _updateLabelShortcuts(self):
        numShortcuts = len(self._labelShortcuts)
        numRows = len(self._labelControlUi.labelListModel)

        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        # Add any shortcuts we don't have yet.
        for i in range(numShortcuts,numRows):
            toolTipObject = LabelListModel.EntryToolTipAdapter(self._labelControlUi.labelListModel, i)
            action_info = ActionInfo( "Labeling", 
                                      "Select Label {}".format(i+1),
                                      "Select Label {}".format(i+1),
                                      partial(self._labelControlUi.labelListView.selectRow, i),
                                      self._labelControlUi.labelListView,
                                      toolTipObject )
            mgr.register( str(i+1), action_info )
            self._labelShortcuts.append( action_info )

        # Make sure that all shortcuts have an appropriate description
        for i in range(numRows):
            action_info = self._labelShortcuts[i]
            description = "Select " + self._labelControlUi.labelListModel[i].name
            new_action_info = mgr.update_description(action_info, description)
            self._labelShortcuts[i] = new_action_info

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
    def _changeInteractionMode( self, toolId ):
        """
        Implement the GUI's response to the user selecting a new tool.
        """
        # Uncheck all the other buttons
        for tool, button in list(self.toolButtons.items()):
            if tool != toolId:
                button.setChecked(False)

        # If we have no editor, we can't do anything yet
        if self.editor is None:
            return

        # The volume editor expects one of two specific names
        if hasattr(self.labelingDrawerUi, "thresToolButton"):
            modeNames = { Tool.Navigation   : "navigation",
                          Tool.Paint        : "brushing",
                          Tool.Erase        : "brushing" ,
                          Tool.Threshold    : "thresholding"}
        else:
            modeNames = { Tool.Navigation   : "navigation",
                          Tool.Paint        : "brushing",
                          Tool.Erase        : "brushing" }

        if hasattr(self._labelControlUi, "AddLabelButton"):
            if self._labelControlUi.labelListModel.rowCount() == self.maxLabelNumber:
                self._labelControlUi.AddLabelButton.setEnabled(False)
            self._labelControlUi.AddLabelButton.setText("Add Label")

        e = self._labelControlUi.labelListModel.rowCount() > 0
        self._gui_enableLabeling(e)
        
        # Update the applet bar caption
        if toolId == Tool.Navigation:
            # update GUI 
            self._gui_setNavigation()
            
        elif toolId == Tool.Paint:
            # If necessary, tell the brushing model to stop erasing
            if self.editor.brushingModel.erasing:
                self.editor.brushingModel.disableErasing()
            # Set the brushing size
            brushSize = self.brushSizes[self.paintBrushSizeIndex]
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
        elif toolId == Tool.Threshold:
            self._gui_setThresholding()

        self.editor.setInteractionMode( modeNames[toolId] )
        self._toolId = toolId
        
    def _gui_setThresholding(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.thresToolButton.setChecked(True)

    def _gui_setErasing(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(True)
        self._labelControlUi.brushSizeCaption.setEnabled(True)
        self._labelControlUi.eraserToolButton.setChecked(True)
        self._labelControlUi.brushSizeCaption.setText("Size:")
        self._labelControlUi.brushSizeComboBox.setCurrentIndex(self.eraserSizeIndex)
    def _gui_setNavigation(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(False)
        self._labelControlUi.brushSizeCaption.setEnabled(False)
        self._labelControlUi.arrowToolButton.setChecked(True)
        # self._labelControlUi.arrowToolButton.setChecked(True) # why twice?
    def _gui_setBrushing(self):
        self._labelControlUi.brushSizeComboBox.setEnabled(True)
        self._labelControlUi.brushSizeCaption.setEnabled(True)
        # Make sure the paint button is pressed
        self._labelControlUi.paintToolButton.setChecked(True)
        # Show the brush size control and set its caption
        self._labelControlUi.brushSizeCaption.setText("Size:")
        # Make sure the GUI reflects the correct size
        self._labelControlUi.brushSizeComboBox.setCurrentIndex(self.paintBrushSizeIndex)
    def _gui_enableLabeling(self, enable):
        self._labelControlUi.paintToolButton.setEnabled(enable)
        self._labelControlUi.eraserToolButton.setEnabled(enable)
        self._labelControlUi.brushSizeCaption.setEnabled(enable)
        self._labelControlUi.brushSizeComboBox.setEnabled(enable)


    def _onBrushSizeChange(self, index):
        """
        Handle the user's new brush size selection.
        Note: The editor's brushing model currently maintains only a single
              brush size, which is used for both painting and erasing.
              However, we maintain two different sizes for the user and swap
              them depending on which tool is selected.
        """
        newSize = self.brushSizes[index]
        if self.editor.brushingModel.erasing:
            self.eraserSizeIndex = index
            self.editor.brushingModel.setBrushSize(newSize)
        else:
            self.paintBrushSizeIndex = index
            self.editor.brushingModel.setBrushSize(newSize)

    def _onLabelSelected(self, row):
        logger.debug("switching to label=%r" % (self._labelControlUi.labelListModel[row]))

        # If the user is selecting a label, he probably wants to be in paint mode
        self._changeInteractionMode(Tool.Paint)

        #+1 because first is transparent
        #FIXME: shouldn't be just row+1 here
        self.editor.brushingModel.setDrawnNumber(row+1)
        brushColor = self._labelControlUi.labelListModel[row].brushColor()
        self.editor.brushingModel.setBrushColor( brushColor )

    def _resetLabelSelection(self):
        logger.debug("Resetting label selection")
        if len(self._labelControlUi.labelListModel) > 0:
            self._labelControlUi.labelListView.selectRow(0)
        else:
            self._changeInteractionMode(Tool.Navigation)
        return True

    def _updateLabelList(self):
        """
        This function is called when the number of labels has changed without our knowledge.
        We need to add/remove labels until we have the right number
        """
        # Get the number of labels in the label data
        # (Or the number of the labels the user has added.)
        names = self._labelingSlots.labelNames.value
        numLabels = len(self._labelingSlots.labelNames.value)

        # Add rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() < numLabels:
            self._addNewLabel()

        # If we have too many rows, remove the rows that aren't in the list of names.
        if self._labelControlUi.labelListModel.rowCount() > len(names):
            indices_to_remove = []
            for i in range(self._labelControlUi.labelListModel.rowCount()):
                if self._labelControlUi.labelListModel[i].name not in names:
                    indices_to_remove.append( i )
        
            for i in reversed(indices_to_remove):
                self._labelControlUi.labelListModel.removeRow(i)

        # synchronize labelNames
        for i,n in enumerate(names):
            self._labelControlUi.labelListModel[i].name = n
                
        if hasattr(self._labelControlUi, "AddLabelButton"):
            self._labelControlUi.AddLabelButton.setEnabled(numLabels < self.maxLabelNumber)

    def _addNewLabel(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        """
        Add a new label to the label list GUI control.
        Return the new number of labels in the control.
        """
        label = Label( self.getNextLabelName(), self.getNextLabelColor(),
                       pmapColor=self.getNextPmapColor(),
                   )
        label.nameChanged.connect(self._updateLabelShortcuts)
        label.nameChanged.connect(self.onLabelNameChanged)
        label.colorChanged.connect(self.onLabelColorChanged)
        label.pmapColorChanged.connect(self.onPmapColorChanged)

        newRow = self._labelControlUi.labelListModel.rowCount()
        self._labelControlUi.labelListModel.insertRow( newRow, label )

        if self._allowDeleteLastLabelOnly:
            # make previous label unremovable
            if newRow > 0:
                self._labelControlUi.labelListModel.makeRowPermanent(newRow - 1)

        newColorIndex = self._labelControlUi.labelListModel.index(newRow, 0)
        self.onLabelListDataChanged(newColorIndex, newColorIndex) # Make sure label layer colortable is in sync with the new color

        # Update operator with new name
        operator_names = self._labelingSlots.labelNames.value
        if len(operator_names) < self._labelControlUi.labelListModel.rowCount():
            operator_names.append( label.name )
            try:
                self._labelingSlots.labelNames.setValue( operator_names, check_changed=False )
            except:
                # I have no idea why this is, but sometimes PyQt "loses" exceptions here.
                # Print it out before it's too late!
                log_exception( logger, "Logged the above exception just in case PyQt loses it." )
                raise

        # Call the 'changed' callbacks immediately to initialize any listeners
        self.onLabelNameChanged()
        self.onLabelColorChanged()
        self.onPmapColorChanged()

        # Make the new label selected
        nlabels = self._labelControlUi.labelListModel.rowCount()
        selectedRow = nlabels-1
        self._labelControlUi.labelListModel.select(selectedRow)

        self._updateLabelShortcuts()
       
        e = self._labelControlUi.labelListModel.rowCount() > 0
        self._gui_enableLabeling(e)
        
        QApplication.restoreOverrideCursor()

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

    def getNextPmapColor(self):
        """
        Return a QColor to use for the next label.
        """
        return None

    def onLabelNameChanged(self):
        """
        Subclasses can override this to respond to changes in the label names.
        """
        pass

    def onLabelColorChanged(self):
        """
        Subclasses can override this to respond to changes in the label colors.
        This class gets updated before, in the _updateLabelList
        """
    
    def onPmapColorChanged(self):
        """
        Subclasses can override this to respond to changes in a label associated probability color.
        """
        pass

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

    def _clearLabelListGui(self):
        # Remove rows until we have the right number
        while self._labelControlUi.labelListModel.rowCount() > 0:
            self._removeLastLabel()

    def _onLabelRemoved(self, parent, start, end):
        # Don't respond unless this actually came from the GUI
        if self._programmaticallyRemovingLabels:
            return

        assert start == end
        row = start

        oldcount = self._labelControlUi.labelListModel.rowCount() + 1
        logger.debug("removing label {} out of {}".format( row, oldcount ))

        if self._allowDeleteLastLabelOnly:
            # make previous label removable again
            if oldcount >= 2:
                self._labelControlUi.labelListModel.makeRowRemovable(oldcount - 2)

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

        e = self._labelControlUi.labelListModel.rowCount() > 0
        self._gui_enableLabeling(e)

        # If the gui list model isn't in sync with the operator, update the operator.
        if len(self._labelingSlots.labelNames.value) > self._labelControlUi.labelListModel.rowCount():
            # Changing the deleteLabel input causes the operator (OpBlockedSparseArray)
            #  to search through the entire list of labels and delete the entries for the matching label.
            self._labelingSlots.labelDelete.setValue(row+1)
    
            # We need to "reset" the deleteLabel input to -1 when we're finished.
            #  Otherwise, you can never delete the same label twice in a row.
            #  (Only *changes* to the input are acted upon.)
            self._labelingSlots.labelDelete.setValue(-1)
            
            labelNames = self._labelingSlots.labelNames.value
            labelNames.pop(start)
            self._labelingSlots.labelNames.setValue(labelNames, check_changed=False)
       
    def getLayer(self, name):
        """find a layer by name"""
        try:
            labellayer = next(filter(lambda l: l.name == name, self.layerstack))
        except StopIteration:
            return None
        else:
            return labellayer

    def _getLabelLayer(self):
        return self.getLayer('Labels')

    def createLabelLayer(self, direct=False):
        """
        Return a colortable layer that displays the label slot data, along with its associated label source.
        direct: whether this layer is drawn synchronously by volumina
        """
        labelOutput = self._labelingSlots.labelOutput
        if not labelOutput.ready():
            return (None, None)
        else:
            # Add the layer to draw the labels, but don't add any labels
            labelsrc = LazyflowSinkSource( self._labelingSlots.labelOutput,
                                           self._labelingSlots.labelInput)

            labellayer = ColortableLayer(labelsrc, colorTable = self._colorTable16, direct=direct )
            labellayer.name = "Labels"
            labellayer.ref_object = None

            labellayer.contexts.append( QAction("Import...", None,
                                        triggered=partial(import_labeling_layer, labellayer, self._labelingSlots, self)) )

            labellayer.shortcutRegistration = ( "0", ShortcutManager.ActionInfo(
                                                        "Labeling",
                                                        "LabelVisibility",
                                                        "Show/Hide Labels",
                                                        labellayer.toggleVisible,
                                                        self.viewerControlWidget(),
                                                        labellayer ) )

            return labellayer, labelsrc

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

        # Raw Input Layer
        if self._rawInputSlot is not None and self._rawInputSlot.ready():
            layer = self.createStandardLayerFromSlot( self._rawInputSlot )
            layer.name = "Raw Input"
            layer.visible = True
            layer.opacity = 1.0

            layers.append(layer)

        return layers

    def allowDeleteLastLabelOnly(self, enabled):
        """
        In the TrackingWorkflow when labeling 0/1/2/.../N mergers we do not allow
        to remove another label but the first, as the following processing steps
        assume that all previous cell counts are given.
        """
        self._allowDeleteLastLabelOnly = enabled
