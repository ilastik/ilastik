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
# 		   http://ilastik.org/license.html
###############################################################################
# Python
from builtins import range
import os
from functools import partial
import logging
from future.utils import with_metaclass

logger = logging.getLogger(__name__)

# SciPy
import numpy

# PyQt
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QWidget
from qtpy.QtGui import QColor
from qtpy import uic

import vigra

# lazyflow
from lazyflow.stype import ArrayLike
from lazyflow.operators import OpSingleChannelSelector, OpWrapSlot
from lazyflow.operators.opReorderAxes import OpReorderAxes

# volumina
from volumina.api import (
    createDataSource,
    GrayscaleLayer,
    RGBALayer,
    ColortableLayer,
    AlphaModulatedLayer,
    LayerStackModel,
    generateRandomColors,
)
from volumina.volumeEditor import VolumeEditor
from volumina.utility import ShortcutManager
from volumina.interpreter import ClickReportingInterpreter

# ilastik
from ilastik.utility import bind
from ilastik.utility.gui import ThreadRouter, threadRouted
from ilastik.config import cfg as ilastik_config
from ilastik.widgets.viewerControls import ViewerControls

# ===----------------------------------------------------------------------------------------------------------------===


class LayerViewerGuiMetaclass(type(QWidget)):
    """
    Custom metaclass to enable the _after_init function.
    """

    def __call__(cls, *args, **kwargs):
        """
        This is where __init__ is called.
        Here we can call code to execute immediately before or after the *subclass* __init__ function.
        """
        # Base class first. (type is our baseclass)
        # type.__call__ calls instance.__init__ internally
        instance = super(LayerViewerGuiMetaclass, cls).__call__(*args, **kwargs)
        instance._after_init()
        return instance


class LayerViewerGui(with_metaclass(LayerViewerGuiMetaclass, QWidget)):
    """
    Implements an applet GUI whose central widget is a VolumeEditor
    and whose layer controls simply contains a layer list widget.
    Intended to be used as a superclass for applet GUI objects.

    Provides: Central widget (viewer), View Menu, and Layer controls
    Provides an EMPTY applet drawer widget.  Subclasses should replace it with their own applet drawer.
    """

    layersUpdated = Signal()

    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def centralWidget(self):
        return self

    def appletDrawer(self):
        return self._drawer

    def menus(self):
        debug_mode = ilastik_config.getboolean("ilastik", "debug")
        return [self.volumeEditorWidget.getViewMenu(debug_mode)]

    def viewerControlWidget(self):
        return self.__viewerControlWidget

    def stopAndCleanUp(self):
        self._stopped = True

        # Remove all layers
        self.layerstack.clear()

        # Unsubscribe to all signals
        for fn in self.__cleanup_fns:
            fn()

        for op in self._orphanOperators:
            op.cleanUp()

    ###########################################
    ###########################################

    def __init__(
        self,
        parentApplet,
        topLevelOperatorView,
        additionalMonitoredSlots=[],
        centralWidgetOnly=False,
        crosshair=True,
        is_3d_widget_visible=False,
    ):
        """
        Constructor.  **All** slots of the provided *topLevelOperatorView* will be monitored for changes.
        Changes include slot resize events, and slot ready/unready status changes.
        When a change is detected, the `setupLayers()` function is called, and the result is used to update the list of layers shown in the central widget.

        :param topLevelOperatorView: The top-level operator for the applet this GUI belongs to.
        :param additionalMonitoredSlots: Optional.  Can be used to add additional slots to the set of viewable layers (all slots from the top-level operator are already monitored).
        :param centralWidgetOnly: If True, provide only a central widget without drawer or viewer controls.
        """
        super(LayerViewerGui, self).__init__()

        self._stopped = False
        self._initialized = False
        self._need_update = True
        self.__cleanup_fns = []

        self.threadRouter = ThreadRouter(self)  # For using @threadRouted

        self.topLevelOperatorView = topLevelOperatorView

        observedSlots = []

        for slot in list(topLevelOperatorView.inputs.values()) + list(topLevelOperatorView.outputs.values()):
            if slot.level == 0 or slot.level == 1:
                observedSlots.append(slot)

        observedSlots += additionalMonitoredSlots

        self._orphanOperators = (
            []
        )  # Operators that are owned by this GUI directly (not owned by the top-level operator)
        self.observedSlots = []
        for slot in observedSlots:
            if slot.level == 0:
                if not isinstance(slot.stype, ArrayLike):
                    # We don't support visualization of non-Array slots.
                    continue
                # To be monitored and updated correctly by this GUI, slots must have level=1, but this slot is of level 0.
                # Pass it through a trivial "up-leveling" operator so it will have level 1 for our purposes.
                opPromoteInput = OpWrapSlot(parent=slot.operator.parent)
                opPromoteInput.Input.connect(slot)
                slot = opPromoteInput.Output
                self._orphanOperators.append(opPromoteInput)

            # Each slot should now be indexed as slot[layer_index]
            assert slot.level == 1
            self.observedSlots.append(slot)
            slot.notifyInserted(bind(self._handleLayerInsertion))
            self.__cleanup_fns.append(partial(slot.unregisterInserted, bind(self._handleLayerInsertion)))

            slot.notifyRemoved(bind(self._handleLayerRemoval))
            self.__cleanup_fns.append(partial(slot.unregisterRemoved, bind(self._handleLayerRemoval)))

            for i in range(len(slot)):
                self._handleLayerInsertion(slot, i)

        self.layerstack = LayerStackModel()
        self.saved_layer_visibilities = None

        self._initCentralUic()

        self._initEditor(crosshair=crosshair, is_3d_widget_visible=is_3d_widget_visible)
        self.__viewerControlWidget = None
        if not centralWidgetOnly:
            self.initViewerControlUi()  # Might be overridden in a subclass. Default implementation loads a standard layer widget.
            # self._drawer = QWidget( self )
            self.initAppletDrawerUi()  # Default implementation loads a blank drawer from drawer.ui.

        self._up_to_date = False

        # By default, we start out disabled until we have at least one layer.
        self.centralWidget().setEnabled(False)

    def _after_init(self):
        self._initialized = True

    def setNeedUpdate(self, slot=None):
        self._need_update = True
        if self.isVisible():
            if slot.graph:
                slot.graph.call_when_setup_finished(self.updateAllLayers)
            else:
                self.updateAllLayers()

    def showEvent(self, event):
        if self._need_update:
            self.updateAllLayers()
        super(LayerViewerGui, self).showEvent(event)

    def setupLayers(self):
        """
        Create a list of layers to be displayed in the central widget.
        Subclasses should override this method to create the list of layers that can be displayed.
        For debug and development purposes, the base class implementation simply generates layers for all topLevelOperatorView slots.
        """
        layers = []
        for multiLayerSlot in self.observedSlots:
            for j, slot in enumerate(multiLayerSlot):
                has_space = slot.meta.axistags and slot.meta.axistags.axisTypeCount(vigra.AxisType.Space) > 2
                if slot.ready() and has_space:
                    layer = self.createStandardLayerFromSlot(slot)

                    # Name the layer after the slot name.
                    if isinstance(multiLayerSlot.operator, OpWrapSlot):
                        # We attached an 'upleveling' operator, so look upstream for the real slot.
                        layer.name = multiLayerSlot.operator.Input.upstream_slot.name
                    else:
                        layer.name = multiLayerSlot.name + " " + str(j)
                    layers.append(layer)
        return layers

    def _handleLayerInsertion(self, slot, slotIndex):
        """
        The multislot providing our layers has a new item.
        Make room for it in the layer GUI and subscribe to updates.
        """
        # When the slot is ready, we'll replace the blank layer with real data
        slot[slotIndex].notifyReady(bind(self.setNeedUpdate))
        slot[slotIndex].notifyUnready(bind(self.setNeedUpdate))

        self.__cleanup_fns.append(partial(slot[slotIndex].unregisterReady, bind(self.setNeedUpdate)))
        self.__cleanup_fns.append(partial(slot[slotIndex].unregisterUnready, bind(self.setNeedUpdate)))

    def _handleLayerRemoval(self, slot, slotIndex):
        """
        An item is about to be removed from the multislot that is providing our layers.
        Remove the layer from the GUI.
        """
        self.setNeedUpdate(slot)

    def generateAlphaModulatedLayersFromChannels(self, slot):
        # TODO
        assert False

    @classmethod
    def createStandardLayerFromSlot(cls, slot, lastChannelIsAlpha=False, name=None, opacity=1.0, visible=True):
        """
        Convenience function.
        Generates a volumina layer using the given slot.
        Will be either a GrayscaleLayer or RGBALayer, depending on the channel metadata.

        :param slot: The slot to generate a layer from
        :param lastChannelIsAlpha: If True, the last channel in the slot is assumed to be an alpha channel.
        """
        numChannels = 1
        display_mode = "default"
        c_index = slot.meta.axistags.index("c")
        if c_index < len(slot.meta.axistags):
            numChannels = slot.meta.shape[c_index]
            display_mode = slot.meta.display_mode

        if display_mode == "" or display_mode == "default":
            ## Figure out whether the default should be rgba or grayscale
            if lastChannelIsAlpha:
                assert numChannels <= 4, (
                    "This function doesn't support alpha for slots with more than 4 channels.  "
                    "Your image has {} channels.".format(numChannels)
                )

            # Automatically select Grayscale or RGBA based on number of channels
            if numChannels == 2 or numChannels == 3:
                display_mode = "rgba"
            elif slot.meta.dtype == numpy.uint64:
                display_mode = "random-colortable"
            else:
                display_mode = "grayscale"

        # Override RGBA --> Grayscale if there's only 1 channel.
        if display_mode == "rgba" and numChannels == 1:
            display_mode = "grayscale"

        if display_mode == "grayscale":
            assert not lastChannelIsAlpha, "Can't have an alpha channel if there is no color channel"
            layer = cls._create_grayscale_layer_from_slot(slot, numChannels)
        elif display_mode == "rgba":
            assert numChannels > 2 or (
                numChannels == 2 and not lastChannelIsAlpha
            ), "Unhandled combination of channels.  numChannels={}, lastChannelIsAlpha={}, axistags={}".format(
                numChannels, lastChannelIsAlpha, slot.meta.axistags
            )
            layer = cls._create_rgba_layer_from_slot(slot, numChannels, lastChannelIsAlpha)
        elif display_mode == "random-colortable":
            layer = cls._create_random_colortable_layer_from_slot(slot)
        elif display_mode == "alpha-modulated":
            layer = cls._create_alpha_modulated_layer_from_slot(slot)
        elif display_mode == "binary-mask":
            layer = cls._create_binary_mask_layer_from_slot(slot)
        else:
            raise RuntimeError(f"unknown channel display mode: {display_mode}")

        layer.name = name or slot.name
        layer.visible = visible
        layer.opacity = opacity

        return layer

    @classmethod
    def _create_grayscale_layer_from_slot(cls, slot, n_channels):
        # FIXME: move all of this stuff into the class constructor. Same for all
        # _create_*layer_from_slot methods.
        source = createDataSource(slot)
        layer = GrayscaleLayer(source, window_leveling=True)
        layer.numberOfChannels = n_channels
        layer.set_normalize(0, (slot.meta.normalizeDisplay and slot.meta.drange) or None)
        return layer

    @classmethod
    def _create_random_colortable_layer_from_slot(cls, slot, num_colors=256):
        colortable = generateRandomColors(num_colors, clamp={"v": 1.0, "s": 0.5}, zeroIsTransparent=True)
        layer = ColortableLayer(createDataSource(slot), colortable)
        layer.colortableIsRandom = True
        return layer

    @classmethod
    def _create_alpha_modulated_layer_from_slot(cls, slot):
        layer = AlphaModulatedLayer(createDataSource(slot), tintColor=QColor(Qt.cyan), normalize=(0.0, 1.0))
        return layer

    @classmethod
    def _create_binary_mask_layer_from_slot(cls, slot):
        # 0: black, 1-255: transparent
        # This works perfectly for uint8.
        # For uint32, etc., values of 256,512, etc. will be appear 'off'.
        # But why would you use uint32 for a binary mask anyway?
        colortable = [QColor(0, 0, 0, 255).rgba()]
        colortable += 255 * [QColor(0, 0, 0, 0).rgba()]
        layer = ColortableLayer(createDataSource(slot), colortable)
        return layer

    @classmethod
    def _create_rgba_layer_from_slot(cls, slot, numChannels, lastChannelIsAlpha):
        bindex = aindex = None
        rindex, gindex = 0, 1
        if numChannels > 3 or (numChannels == 3 and not lastChannelIsAlpha):
            bindex = 2
        if lastChannelIsAlpha:
            aindex = numChannels - 1

        if numChannels >= 2:
            gindex = 1
        if numChannels >= 3:
            bindex = 2
        if numChannels >= 4:
            aindex = numChannels - 1

        redSource = None
        if rindex is not None:
            redProvider = OpSingleChannelSelector(parent=slot.operator.parent)
            redProvider.Input.connect(slot)
            redProvider.Index.setValue(rindex)
            redSource = createDataSource(redProvider.Output)
            redSource.additional_owned_ops.append(redProvider)

        greenSource = None
        if gindex is not None:
            greenProvider = OpSingleChannelSelector(parent=slot.operator.parent)
            greenProvider.Input.connect(slot)
            greenProvider.Index.setValue(gindex)
            greenSource = createDataSource(greenProvider.Output)
            greenSource.additional_owned_ops.append(greenProvider)

        blueSource = None
        if bindex is not None:
            blueProvider = OpSingleChannelSelector(parent=slot.operator.parent)
            blueProvider.Input.connect(slot)
            blueProvider.Index.setValue(bindex)
            blueSource = createDataSource(blueProvider.Output)
            blueSource.additional_owned_ops.append(blueProvider)

        alphaSource = None
        if aindex is not None:
            alphaProvider = OpSingleChannelSelector(parent=slot.operator.parent)
            alphaProvider.Input.connect(slot)
            alphaProvider.Index.setValue(aindex)
            alphaSource = createDataSource(alphaProvider.Output)
            alphaSource.additional_owned_ops.append(alphaProvider)

        layer = RGBALayer(red=redSource, green=greenSource, blue=blueSource, alpha=alphaSource)
        for i in range(4):
            if [redSource, greenSource, blueSource, alphaSource][i]:
                layer.set_normalize(i, (slot.meta.normalizeDisplay and slot.meta.drange) or None)

        return layer

    @threadRouted
    def updateAllLayers(self, slot=None):
        if self._stopped or not self._initialized:
            return
        if slot is not None and slot.ready() and slot.meta.axistags is None:
            # Don't update in response to value slots.
            return

        self._need_update = False

        # Ask for the updated layer list (usually provided by the subclass)
        newGuiLayers = self.setupLayers()

        # The order of the initial layerstack has to be static, where the "Raw Input" layer is at the stacks last position
        for i in range(len(newGuiLayers)):
            if newGuiLayers[i].name == "Raw Input":
                rlayer = newGuiLayers[i]
                newGuiLayers.remove(rlayer)
                newGuiLayers.append(rlayer)
                break

        for layer in newGuiLayers:
            assert not [l for l in self.layerstack if l is layer], (
                "You are attempting to re-use a layer ({}).  "
                "Your setupOutputs() function may not re-use layer objects.  "
                "The layerstack retains ownership of the layers you provide and "
                "may choose to clean and delete them without your knowledge.".format(layer.name)
            )

        newNames = set(l.name for l in newGuiLayers)
        if len(newNames) != len(newGuiLayers):
            msg = "All layers must have unique names.\n"
            msg += "You're attempting to use these layer names:\n"
            msg += str([l.name for l in newGuiLayers])
            raise RuntimeError(msg)

        # Old layers are deleted if
        # (1) They are not in the new set or
        # (2) Their data has changed
        for index, oldLayer in reversed(list(enumerate(self.layerstack))):
            if oldLayer.name not in newNames:
                needDelete = True
            else:
                newLayer = list(filter(lambda l: l.name == oldLayer.name, newGuiLayers))[0]
                needDelete = newLayer.isDifferentEnough(oldLayer)

            if needDelete:
                layer = self.layerstack[index]
                if hasattr(layer, "shortcutRegistration"):
                    action_info = layer.shortcutRegistration[1]
                    ShortcutManager().unregister(action_info)
                self.layerstack.selectRow(index)
                self.layerstack.deleteSelected()

        # If the datashape changed, tell the editor.
        # Happens during setup ([0,0,0,0,0] to image shape) and when switching scales (multiscale datasets)
        newDataShape = self.determineDatashape()
        if newDataShape is not None and self.editor.dataShape != newDataShape:
            self.editor.dataShape = newDataShape
            if self._isAnySlotPrefer2d():
                self.volumeEditorWidget.quadview.ensureMaximized(2)

            # Find the xyz midpoint
            midpos5d = [x // 2 for x in newDataShape]

            # center viewer there
            self.setViewerPos(midpos5d)

        # Insert all layers that aren't already in the layerstack
        # (Identified by the name attribute)
        existingNames = set(l.name for l in self.layerstack)
        for index, layer in enumerate(newGuiLayers):
            if layer.name not in existingNames:
                # Insert new
                self.layerstack.insert(index, layer)

                # If this layer has an associated shortcut, register it with the shortcut manager
                if hasattr(layer, "shortcutRegistration"):
                    ShortcutManager().register(*layer.shortcutRegistration)
            else:
                # Clean up the layer instance that the client just gave us.
                # We don't want to use it.
                layer.clean_up()

                # Move existing layer to the correct position
                stackIndex = self.layerstack.findMatchingIndex(lambda l: l.name == layer.name)
                self.layerstack.selectRow(stackIndex)
                while stackIndex > index:
                    self.layerstack.moveSelectedUp()
                    stackIndex -= 1
                while stackIndex < index:
                    self.layerstack.moveSelectedDown()
                    stackIndex += 1

        if len(self.layerstack) > 0:
            self.centralWidget().setEnabled(True)

        self.layersUpdated.emit()

    def determineDatashape(self):
        newDataShape = None
        for provider in self.observedSlots:
            for i, slot in enumerate(provider):
                if newDataShape is None:
                    newDataShape = self.getVoluminaShapeForSlot(slot)
        return newDataShape

    def getLayerByName(self, name):
        matches = [l for l in list(self.layerstack) if l.name == name]
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]
        assert False, "Found more than one matching layer with name {}".format(name)

    def toggle_show_raw(self, raw_layer_name="Raw Data"):
        """
        Convenience function.
        Hide all layers except for the raw data layer specified by the given layer name.
        The next time this function is called, restore previous layer visibility states.
        """
        if self.saved_layer_visibilities:
            for layer in self.layerstack:
                layer.visible = self.saved_layer_visibilities[layer.name]
            self.saved_layer_visibilities = None
        else:
            self.saved_layer_visibilities = {layer.name: layer.visible for layer in self.layerstack}
            for layer in self.layerstack:
                layer.visible = False
            self.getLayerByName(raw_layer_name).visible = True

    @threadRouted
    def setViewerPos(self, pos, setTime=False, setChannel=False):
        try:
            pos5d = self.validatePos(pos, dims=5)

            # set xyz position
            pos3d = pos5d[1:4]
            self.editor.posModel.slicingPos = pos3d

            # set time and channel if requested
            if setTime:
                self.editor.posModel.time = pos5d[0]
            if setChannel:
                self.editor.posModel.channel = pos5d[4]

            self.editor.navCtrl.panSlicingViews(pos3d, [0, 1, 2])
            for i in range(3):
                self.editor.navCtrl.changeSliceAbsolute(pos3d[i], i)

        except Exception as e:
            logger.warning("Failed to navigate to position (%s): %s" % (pos, e))
        return

    def validatePos(self, pos, dims=5):
        if not isinstance(pos, list):
            raise Exception("Wrong data format")
        if not len(pos) == dims:
            raise Exception("Wrong data format")
        ds = self.editor.dataShape
        for i in range(dims):
            try:
                pos[i] = max(0, min(int(pos[i]), ds[i] - 1))
            except:
                pos[i] = 0
        return pos

    @classmethod
    def getVoluminaShapeForSlot(self, slot):
        shape = None
        if slot.ready() and slot.meta.axistags is not None:
            # Use an OpReorderAxes adapter to transpose the shape for us.
            op5 = OpReorderAxes(parent=slot.operator.parent)
            op5.Input.connect(slot)
            op5.AxisOrder.setValue("txyzc")
            shape = op5.Output.meta.shape

            # We just needed the operator to determine the transposed shape.
            # Disconnect it so it can be garbage collected.
            op5.Input.disconnect()
            op5.cleanUp()
        return shape

    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        Subclasses should override this if they provide their own viewer control widget.
        """
        self.__viewerControlWidget = ViewerControls()

        # The editor's layerstack is in charge of which layer movement buttons are enabled
        model = self.editor.layerStack

        if self.__viewerControlWidget is not None:
            self.__viewerControlWidget.setupConnections(model)

    def initAppletDrawerUi(self):
        """
        By default, this base class provides a blank applet drawer.
        Override this in a subclass to get a real applet drawer.
        """
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir + "/drawer.ui")

    def getAppletDrawerUi(self):
        return self._drawer

    def _initCentralUic(self):
        """
        Load the GUI from the ui file into this class and connect it with event handlers.
        """
        # Load the ui file into this class (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        uic.loadUi(localDir + "/centralWidget.ui", self)

    def _initEditor(self, crosshair, is_3d_widget_visible):
        """
        Initialize the Volume Editor GUI.
        """
        self.editor = VolumeEditor(
            self.layerstack, parent=self, crosshair=crosshair, is_3d_widget_visible=is_3d_widget_visible
        )

        # Replace the editor's navigation interpreter with one that has extra functionality
        self.clickReporter = ClickReportingInterpreter(self.editor.navInterpret, self.editor.posModel)
        self.editor.setNavigationInterpreter(self.clickReporter)
        self.clickReporter.rightClickReceived.connect(self._handleEditorRightClick)
        self.clickReporter.leftClickReceived.connect(self._handleEditorLeftClick)
        self.clickReporter.toolTipReceived.connect(self._handleEditorToolTip)

        clickReporter2 = ClickReportingInterpreter(self.editor.brushingInterpreter, self.editor.posModel)
        clickReporter2.rightClickReceived.connect(self._handleEditorRightClick)
        self.editor.brushingInterpreter = clickReporter2

        self.editor.setInteractionMode("navigation")
        self.volumeEditorWidget.init(self.editor)

        self.editor._lastImageViewFocus = 0

        # Zoom at a 1-1 scale to avoid loading big datasets entirely...
        for view in self.editor.imageViews:
            view.doScaleTo(1)

        # Should we default to 2D?
        if self._isAnySlotPrefer2d():
            # Default to Z (axis 2 in the editor)
            self.volumeEditorWidget.quadview.ensureMaximized(2)

    def _isAnySlotPrefer2d(self):
        prefer_2d = False
        for multislot in self.observedSlots:
            for slot in multislot:
                if slot.ready() and slot.meta.prefer_2d:
                    prefer_2d = True
                    break
        return prefer_2d

    def _convertPositionToDataSpace(self, voluminaPosition):
        taggedPosition = {k: p for k, p in zip("txyzc", voluminaPosition)}

        # Find the first lazyflow layer in the stack
        # We assume that all lazyflow layers have the same axistags
        dataTags = None
        for layer in self.layerstack:
            for datasource in layer.datasources:
                try:  # not all datasources have the dataSlot property, find out by trying
                    dataTags = datasource.dataSlot.meta.axistags
                    if dataTags is not None:
                        break
                except AttributeError:
                    pass

        if dataTags is None:
            raise RuntimeError(
                "Can't convert mouse click coordinates from volumina-5d: Could not find a lazyflow data source in any layer."
            )
        position = ()
        for tag in dataTags:
            position += (taggedPosition[tag.key],)

        return position

    def _handleEditorRightClick(self, position5d, globalWindowCoordinate):
        if len(self.layerstack) > 0:
            dataPosition = self._convertPositionToDataSpace(position5d)
            self.handleEditorRightClick(dataPosition, globalWindowCoordinate)

    def _handleEditorLeftClick(self, position5d, globalWindowCoordinate):
        if len(self.layerstack) > 0:
            dataPosition = self._convertPositionToDataSpace(position5d)
            self.handleEditorLeftClick(dataPosition, globalWindowCoordinate)

    def handleEditorRightClick(self, position5d, globalWindowCoordinate):
        # Override me
        pass

    def handleEditorLeftClick(self, position5d, globalWindowCoordiante):
        # Override me
        pass

    def _handleEditorToolTip(self, position5d, globalWindowCoordinate):
        if len(self.layerstack) > 0:
            dataPosition = self._convertPositionToDataSpace(position5d)
            self.handleEditorToolTip(dataPosition, globalWindowCoordinate)

    def handleEditorToolTip(self, position5d, globalWindowCoordinate):
        # Override me
        pass
