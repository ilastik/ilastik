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
import os
import re
import logging
import itertools
from functools import partial

# Third-party
import numpy
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QShortcut, QApplication
from PyQt5.QtGui import QIcon, QColor, QKeySequence

# HCI
from volumina.api import LazyflowSinkSource, ColortableLayer
from volumina.utility import ShortcutManager, PreferencesManager
from volumina import colortables
from ilastik.shell.gui.iconMgr import ilastikIcons
from ilastik.widgets.cropListView import Crop
from ilastik.widgets.cropListModel import CropListModel
from ilastik.applets.cropping.cropSelectionWidget import CropSelectionWidget

# ilastik
from ilastik.utility import bind, log_exception
from ilastik.utility.gui import ThunkEventHandler, threadRouted
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

# Loggers
logger = logging.getLogger(__name__)

class Tool(object):
    """Enumerate the types of toolbar buttons."""
    Navigation = 0 # Arrow
    Paint      = 1
    Erase      = 2
    Threshold  = 3

class CroppingGui(LayerViewerGui):
    """
    Provides all the functionality of a simple layerviewer
    applet with the added functionality of cropping.
    """
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget( self ):
        return self

    def appletDrawer(self):
        return self._cropControlUi

    def stopAndCleanUp(self):
        super(CroppingGui, self).stopAndCleanUp()

        for fn in self.__cleanup_fns:
            fn()

    ###########################################
    ###########################################

    @property
    def minCropNumber(self):
        return self._minCropNumber
    @minCropNumber.setter
    def minCropNumber(self, n):
        self._minCropNumer = n
        while self._cropControlUi.cropListModel.rowCount() < n:
            self._addNewCrop()
    @property
    def maxCropNumber(self):
        return self._maxCropNumber
    @maxCropNumber.setter
    def maxCropNumber(self, n):
        self._maxCropNumber = n
        while self._cropControlUi.cropListModel.rowCount() < n:
            self._removeLastCrop()

    @property
    def croppingDrawerUi(self):
        return self._cropControlUi

    @property
    def cropListData(self):
        return self._cropControlUi.cropListModel

    def selectCrop(self, cropIndex):
        """Programmatically select the given cropIndex, which start from 0.
           Equivalent to clicking on the (cropIndex+1)'th position in the crop widget."""
        self._cropControlUi.cropListModel.select(cropIndex)

    class CroppingSlots(object):
        """
        This class serves as the parameter for the CroppingGui constructor.
        It provides the slots that the cropping GUI uses to source crops to the display and sink crops from the
        user's mouse clicks.
        """
        def __init__(self):
            # Slot to insert elements onto
            self.cropInput = None # cropInput.setInSlot(xxx)

            # Slot to read elements from
            self.cropOutput = None # cropOutput.get(roi)

            # Slot that determines which crop value corresponds to erased values
            self.cropEraserValue = None # cropEraserValue.setValue(xxx)

            # Slot that is used to request wholesale crop deletion
            self.cropDelete = None # cropDelete.setValue(xxx)

            # Slot that gives a list of crop names
            self.cropNames = None # cropNames.value

            # Slot to specify which images the user is allowed to crop.
            self.cropsAllowed = None # cropsAllowed.value == True

    def __init__(self, parentApplet, croppingSlots, topLevelOperatorView, drawerUiPath=None, rawInputSlot=None, crosshair=True):
        """
        Constructor.

        :param croppingSlots: Provides the slots needed for sourcing/sinking crop data.  See CroppingGui.CroppingSlots
                              class source for details.
        :param topLevelOperatorView: is provided to the LayerViewerGui (the base class)
        :param drawerUiPath: can be given if you provide an extended drawer UI file.  Otherwise a default one is used.
        :param rawInputSlot: Data from the rawInputSlot parameter will be displayed directly underneath the elements
                             (if provided).
        """

        # Do we have all the slots we need?
        assert isinstance(croppingSlots, CroppingGui.CroppingSlots)
        assert croppingSlots.cropInput is not None, "Missing a required slot."
        assert croppingSlots.cropOutput is not None, "Missing a required slot."
        assert croppingSlots.cropEraserValue is not None, "Missing a required slot."
        assert croppingSlots.cropDelete is not None, "Missing a required slot."
        assert croppingSlots.cropNames is not None, "Missing a required slot."
        assert croppingSlots.cropsAllowed is not None, "Missing a required slot."

        self.__cleanup_fns = []
        self._croppingSlots = croppingSlots
        self._minCropNumber = 0
        self._maxCropNumber = 99 #100 or 255 is reserved for eraser

        self._rawInputSlot = rawInputSlot

        self.topLevelOperatorView.Crops.notifyDirty( bind(self._updateCropList) )
        self.topLevelOperatorView.Crops.notifyDirty( bind(self._updateCropList) )
        self.__cleanup_fns.append( partial( self.topLevelOperatorView.Crops.unregisterDirty, bind(self._updateCropList) ) )
        
        self._colorTable16 = colortables.default16_new
        self._programmaticallyRemovingCrops = False

        self._initCropUic(drawerUiPath)

        self._maxCropNumUsed = 0

        self._allowDeleteLastCropOnly = False
        self.__initShortcuts()
        # Init base class
        super(CroppingGui, self).__init__(parentApplet,
                                          topLevelOperatorView,
                                          [croppingSlots.cropInput, croppingSlots.cropOutput],
                                          crosshair=crosshair)
        self._croppingSlots.cropEraserValue.setValue(self.editor.brushingModel.erasingNumber)

        # Register for thunk events (easy UI calls from non-GUI threads)
        self.thunkEventHandler = ThunkEventHandler(self)

    def _initCropUic(self, drawerUiPath):

        self.cropSelectionWidget = CropSelectionWidget()

        self._cropControlUi = self.cropSelectionWidget

        # Initialize the crop list model
        model = CropListModel()
        self._cropControlUi.cropListView.setModel(model)
        self._cropControlUi.cropListModel=model
        self._cropControlUi.cropListModel.rowsRemoved.connect(self._onCropRemoved)
        self._cropControlUi.cropListModel.elementSelected.connect(self._onCropSelected)
        self._cropControlUi.cropListModel.dataChanged.connect(self.onCropListDataChanged)
        self.toolButtons = None

    def _initCropListView(self):
        if self.topLevelOperatorView.Crops.value != {}:
            self._cropControlUi.cropListModel=CropListModel()
            crops = self.topLevelOperatorView.Crops.value
            for key in sorted(crops):
                newRow = self._cropControlUi.cropListModel.rowCount()
                crop = Crop(
                        key,
                        [(crops[key]["time"][0],crops[key]["starts"][0],crops[key]["starts"][1],crops[key]["starts"][2]),(crops[key]["time"][1],crops[key]["stops"][0],crops[key]["stops"][1],crops[key]["stops"][2])],
                        QColor(crops[key]["cropColor"][0],crops[key]["cropColor"][1],crops[key]["cropColor"][2]),
                        pmapColor=QColor(crops[key]["pmapColor"][0],crops[key]["pmapColor"][1],crops[key]["pmapColor"][2])
                )
                self._cropControlUi.cropListModel.insertRow( newRow, crop )

            self._cropControlUi.cropListModel.elementSelected.connect(self._onCropSelected)
            self._cropControlUi.cropListView.setModel(self._cropControlUi.cropListModel)
            self._cropControlUi.cropListView.updateGeometry()
            self._cropControlUi.cropListView.update()
            self._cropControlUi.cropListView.selectRow(0)
            self._maxCropNumUsed = len(crops)
        else:
            self.editor.cropModel.set_volume_shape_3d(self.editor.dataShape[1:4])
            self.newCrop()
            self.setCrop()

    def onCropListDataChanged(self, topLeft, bottomRight):
        """Handle changes to the crop list selections."""
        firstRow = topLeft.row()
        lastRow  = bottomRight.row()

        firstCol = topLeft.column()
        lastCol  = bottomRight.column()

        # We only care about the color column
        if firstCol <= 0 <= lastCol:
            assert(firstRow == lastRow) # Only one data item changes at a time

            #in this case, the actual data (for example color) has changed
            color = self._cropControlUi.cropListModel[firstRow].brushColor()
            self._colorTable16[firstRow+1] = color.rgba()
            self.editor.brushingModel.setBrushColor(color)

            # Update the crop layer colortable to match the list entry
            croplayer = self._getCropLayer()
            if croplayer is not None:
                croplayer.colorTable = self._colorTable16

    def __initShortcuts(self):
        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        shortcutGroupName = "Cropping"

        if hasattr(self.croppingDrawerUi, "AddCropButton"):
            mgr.register("n", ActionInfo( shortcutGroupName,
                                          "New Crop",
                                          "Add a new crop.",
                                          self.croppingDrawerUi.AddCropButton.click,
                                          self.croppingDrawerUi.AddCropButton,
                                          self.croppingDrawerUi.AddCropButton ) )

        if hasattr(self.croppingDrawerUi, "SetCropButton"):
            mgr.register("s", ActionInfo( shortcutGroupName,
                                          "Save Crop",
                                          "Save the current crop.",
                                          self.croppingDrawerUi.SetCropButton.click,
                                          self.croppingDrawerUi.SetCropButton,
                                          self.croppingDrawerUi.SetCropButton ) )

        self._cropShortcuts = []

    def _updateCropShortcuts(self):
        numShortcuts = len(self._cropShortcuts)
        numRows = len(self._cropControlUi.cropListModel)

        mgr = ShortcutManager()
        ActionInfo = ShortcutManager.ActionInfo
        # Add any shortcuts we don't have yet.
        for i in range(numShortcuts,numRows):
            toolTipObject = CropListModel.EntryToolTipAdapter(self._cropControlUi.cropListModel, i)
            action_info = ActionInfo( "Cropping", 
                                      "Select Crop {}".format(i+1),
                                      "Select Crop {}".format(i+1),
                                      partial(self._cropControlUi.cropListView.selectRow, i),
                                      self._cropControlUi.cropListView,
                                      toolTipObject )
            mgr.register( str(i+1), action_info )
            self._cropShortcuts.append( action_info )

        # Make sure that all shortcuts have an appropriate description
        for i in range(numRows):
            action_info = self._cropShortcuts[i]
            description = "Select " + self._cropControlUi.cropListModel[i].name
            new_action_info = mgr.update_description(action_info, description)
            self._cropShortcuts[i] = new_action_info

    def hideEvent(self, event):
        """
        QT event handler.
        The user has selected another applet or is closing the whole app.
        Save all preferences.
        """
        super(CroppingGui, self).hideEvent(event)

    @threadRouted
    def _changeInteractionMode( self, toolId ):
         """
         Implement the GUI's response to the user selecting a new tool.
         """
         # Uncheck all the other buttons
         if self.toolButtons != None:
             for tool, button in list(self.toolButtons.items()):
                 if tool != toolId:
                     button.setChecked(False)

         # If we have no editor, we can't do anything yet
         if self.editor is None:
             return

         # If the user can't crop this image, disable the button and say why its disabled
         cropsAllowed = False

         cropsAllowedSlot = self._croppingSlots.cropsAllowed
         if cropsAllowedSlot.ready():
             cropsAllowed = cropsAllowedSlot.value

             if hasattr(self._cropControlUi, "AddCropButton"):
                 if not cropsAllowed or self._cropControlUi.cropListModel.rowCount() == self.maxCropNumber:
                     self._cropControlUi.AddCropButton.setEnabled(False)
                 if cropsAllowed:
                     self._cropControlUi.AddCropButton.setText("Add Crop")
                 else:
                     self._cropControlUi.AddCropButton.setText("(Cropping Not Allowed)")

         e = cropsAllowed & (self._cropControlUi.cropListModel.rowCount() > 0)
         self._gui_enableCropping(e)

    def _resetCropSelection(self):
        logger.debug("Resetting crop selection")
        if len(self._cropControlUi.cropListModel) > 0:
            self._cropControlUi.cropListView.selectRow(0)
        else:
            self._changeInteractionMode(Tool.Navigation)
        return True

    def _updateCropList(self):
        """
        This function is called when the number of crops has changed without our knowledge.
        We need to add/remove crops until we have the right number
        """
        # Get the number of crops in the crop data
        # (Or the number of crops the user has added.)
        names = sorted(self.topLevelOperatorView.Crops.value.keys())
        numCrops = len(names)

        # Add rows until we have the right number
        while self._cropControlUi.cropListModel.rowCount() < numCrops:
            self._addNewCrop()

        # synchronize cropNames
        for i,n in enumerate(names):
            self._cropControlUi.cropListModel[i].name = n
                
        if hasattr(self._cropControlUi, "AddCropButton"):
            self._cropControlUi.AddCropButton.setEnabled(numCrops < self.maxCropNumber)

    def _addNewCrop(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        """
        Add a new crop to the crop list GUI control.
        Return the new number of crops in the control.
        """
        color = self.getNextCropColor()
        crop = Crop( self.getNextCropName(), self.get_roi_4d(), color,
                       pmapColor=self.getNextPmapColor(),
                   )
        crop.nameChanged.connect(self._updateCropShortcuts)
        crop.nameChanged.connect(self.onCropNameChanged)
        crop.colorChanged.connect(self.onCropColorChanged)
        crop.pmapColorChanged.connect(self.onPmapColorChanged)

        newRow = self._cropControlUi.cropListModel.rowCount()
        self._cropControlUi.cropListModel.insertRow( newRow, crop )

        if self._allowDeleteLastCropOnly:
            # make previous crop unremovable
            if newRow > 0:
                self._cropControlUi.cropListModel.makeRowPermanent(newRow - 1)

        newColorIndex = self._cropControlUi.cropListModel.index(newRow, 0)
        self.onCropListDataChanged(newColorIndex, newColorIndex) # Make sure crop layer colortable is in sync with the new color

        # Update operator with new name
        operator_names = self._croppingSlots.cropNames.value

        if len(operator_names) < self._cropControlUi.cropListModel.rowCount():
            operator_names.append( crop.name )

            try:
                self._croppingSlots.cropNames.setValue( operator_names, check_changed=False )
            except:
                # I have no idea why this is, but sometimes PyQt "loses" exceptions here.
                # Print it out before it's too late!
                log_exception( logger, "Logged the above exception just in case PyQt loses it." )
                raise


        # Call the 'changed' callbacks immediately to initialize any listeners
        self.onCropNameChanged()
        self.onCropColorChanged()
        self.onPmapColorChanged()


        self._maxCropNumUsed += 1
        self._updateCropShortcuts()

        e = self._cropControlUi.cropListModel.rowCount() > 0
        QApplication.restoreOverrideCursor()

    def getNextCropName(self):
        """
        Return a suitable name for the next crop added by the user.
        Subclasses may override this.
        """
        maxNum = 0
        for index, crop in enumerate(self._cropControlUi.cropListModel):
            nums = re.findall("\d+", crop.name)
            for n in nums:
                maxNum = max(maxNum, int(n))
        return "Crop {}".format(maxNum+1)

    def getNextPmapColor(self):
        """
        Return a QColor to use for the next crop.
        """
        return None

    def onCropNameChanged(self):
        """
        Subclasses can override this to respond to changes in the crop names.
        """
        pass

    def onCropColorChanged(self):
        """
        Subclasses can override this to respond to changes in the crop colors.
        """
        pass
    
    def onPmapColorChanged(self):
        """
        Subclasses can override this to respond to changes in a crop associated probability color.
        """
        pass

    def _removeLastCrop(self):
        """
        Programmatically (i.e. not from the GUI) reduce the size of the crop list by one.
        """
        self._programmaticallyRemovingCrops = True
        numRows = self._cropControlUi.cropListModel.rowCount()

        # This will trigger the signal that calls _onCropRemoved()
        self._cropControlUi.cropListModel.removeRow(numRows-1)
        self._updateCropShortcuts()

        self._programmaticallyRemovingCrops = False

    def _clearCropListGui(self):
        # Remove rows until we have the right number
        while self._cropControlUi.cropListModel.rowCount() > 0:
            self._removeLastCrop()

    def _onCropRemoved(self, parent, start, end):
        # Don't respond unless this actually came from the GUI
        if self._programmaticallyRemovingCrops:
            return

        assert start == end
        row = start

        oldcount = self._cropControlUi.cropListModel.rowCount() + 1
        # we need at least one crop
        if oldcount <= 1:
            return

        logger.debug("removing crop {} out of {}".format( row, oldcount ))

        if self._allowDeleteLastCropOnly:
            # make previous crop removable again
            if oldcount >= 2:
                self._cropControlUi.cropListModel.makeRowRemovable(oldcount - 2)

        # Remove the deleted crop's color from the color table so that renumbered crops keep their colors.
        oldColor = self._colorTable16.pop(row+1)

        # Recycle the deleted color back into the table (for the next crop to be added)
        self._colorTable16.insert(oldcount, oldColor)

        # Update the croplayer colortable with the new color mapping
        croplayer = self._getCropLayer()
        if croplayer is not None:
            croplayer.colorTable = self._colorTable16

        currentSelection = self._cropControlUi.cropListModel.selectedRow()
        if currentSelection == -1:
            # If we're deleting the currently selected row, then switch to a different row
            self.thunkEventHandler.post( self._resetCropSelection )

        e = self._cropControlUi.cropListModel.rowCount() > 0
        #self._gui_enableCropping(e)

        # If the gui list model isn't in sync with the operator, update the operator.
        #if len(self._croppingSlots.cropNames.value) > self._cropControlUi.cropListModel.rowCount():
        if len(self.topLevelOperatorView.Crops.value) > self._cropControlUi.cropListModel.rowCount():
            # Changing the deleteCrop input causes the operator (OpBlockedSparseArray)
            #  to search through the entire list of crops and delete the entries for the matching crop.
            #self._croppingSlots.cropDelete.setValue(row+1)
            del self.topLevelOperatorView.Crops[self._cropControlUi.cropListModel[row].name]

            # We need to "reset" the deleteCrop input to -1 when we're finished.
            #  Otherwise, you can never delete the same crop twice in a row.
            #  (Only *changes* to the input are acted upon.)
            self._croppingSlots.cropDelete.setValue(-1)

    def getLayer(self, name):
        """find a layer by name"""
        try:
            croplayer = next(filter(lambda l: l.name == name, self.layerstack))
        except StopIteration:
            return None
        else:
            return croplayer

    def _getCropLayer(self):
        return self.getLayer('Crops')

    def createCropLayer(self, direct=False):
        """
        Return a colortable layer that displays the crop slot data, along with its associated crop source.
        direct: whether this layer is drawn synchronously by volumina
        """
        cropOutput = self._croppingSlots.cropOutput
        if not cropOutput.ready():
            return (None, None)
        else:
            # Add the layer to draw the crops, but don't add any crops
            cropsrc = LazyflowSinkSource( self._croppingSlots.cropOutput,
                                           self._croppingSlots.cropInput)

            croplayer = ColortableLayer(cropsrc, colorTable = self._colorTable16, direct=direct )
            croplayer.name = "Crops"
            croplayer.ref_object = None

            return croplayer, cropsrc

    def setupLayers(self):
        """
        Sets up the crop layer for display by our base class (LayerViewerGui).
        If our subclass overrides this function to add his own layers,
        he **must** call this function explicitly.
        """
        layers = []

        # Crops
        croplayer, cropsrc = self.createCropLayer()
        if croplayer is not None:
            layers.append(croplayer)

            # Tell the editor where to draw crop data
            self.editor.setCropSink(cropsrc)

        # Side effect 1: We want to guarantee that the crop list
        #  is up-to-date before our subclass adds his layers
        self._updateCropList()

        # Side effect 2: Switch to navigation mode if crops aren't
        #  allowed on this image.
        cropsAllowedSlot = self._croppingSlots.cropsAllowed
        if cropsAllowedSlot.ready() and not cropsAllowedSlot.value:
            self._changeInteractionMode(Tool.Navigation)

        # Raw Input Layer
        if self._rawInputSlot is not None and self._rawInputSlot.ready():
            layer = self.createStandardLayerFromSlot( self._rawInputSlot )
            layer.name = "Raw Input"
            layer.visible = True
            layer.opacity = 1.0

            layers.append(layer)

        return layers


    def allowDeleteLastCropOnly(self, enabled):
        """
        In the TrackingWorkflow when cropping 0/1/2/.../N mergers we do not allow
        to remove another crop but the first, as the following processing steps
        assume that all previous cell counts are given.
        """
        self._allowDeleteLastCropOnly = enabled
