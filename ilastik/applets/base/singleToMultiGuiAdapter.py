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
from ilastik.applets.base.appletGuiInterface import AppletGuiInterface


class SingleToMultiGuiAdapter(AppletGuiInterface):
    """
    Utility class used by the StandardApplet to wrap several single-image
    GUIs into one multi-image GUI, which is what the shell/Applet API requires.
    """

    def __init__(self, parentApplet, singleImageGuiFactory, topLevelOperator):
        self.singleImageGuiFactory = singleImageGuiFactory
        self._imageLaneIndex = None
        self._guis = []
        self._tempDrawers = {}
        self.topLevelOperator = topLevelOperator
        self._enabled = False

    def currentGui(self, fallback_on_lane_0=False):
        """
        Return the single-image GUI for the currently selected image lane.
        If it doesn't exist yet, create it.
        """
        if self._imageLaneIndex is None:
            if fallback_on_lane_0:
                self._imageLaneIndex = 0
            else:
                return None

        if self._imageLaneIndex >= len(self._guis):
            return None

        # Create first if necessary
        if self._guis[self._imageLaneIndex] is None:
            self._guis[self._imageLaneIndex] = self.singleImageGuiFactory(self._imageLaneIndex)
        return self._guis[self._imageLaneIndex]

    def appletDrawer(self):
        """
        Return the applet drawer of the current single-image gui.
        """
        if self.currentGui() is not None:
            self._tempDrawers[self._imageLaneIndex] = self.currentGui().appletDrawer()
            return self.currentGui().appletDrawer()

        if self._imageLaneIndex not in self._tempDrawers:
            from qtpy.QtWidgets import QWidget

            self._tempDrawers[self._imageLaneIndex] = QWidget()
        return self._tempDrawers[self._imageLaneIndex]

    def centralWidget(self):
        """
        Return the central widget of the currently selected single-image gui.
        """
        current_gui = self.currentGui()
        if current_gui is None:
            return None
        return current_gui.centralWidget()

    def secondaryControlsWidget(self):
        current_gui = self.currentGui()
        if current_gui is None:
            return None
        return current_gui.secondaryControlsWidget()

    def menus(self):
        """
        Return the menus of the currently selected single-image gui.
        """
        current_gui = self.currentGui()
        if current_gui is None:
            return None
        return current_gui.menus()

    def viewerControlWidget(self):
        """
        Return the viewer control widget for the currently selected single-image gui.
        """
        if self.currentGui() is None:
            return None
        return self.currentGui().viewerControlWidget()

    def setImageIndex(self, imageIndex):
        """
        Called by the shell when the user has changed the currently selected image lane.
        """
        self._imageLaneIndex = imageIndex

    def stopAndCleanUp(self):
        """
        Called by the workflow when the project is closed and the GUIs are about to be discarded.
        """
        for gui in self._guis:
            if gui is not None:
                gui.stopAndCleanUp()
        # Discard all sub-guis.
        self._guis = []

    def imageLaneAdded(self, laneIndex):
        """
        Called by the workflow when a new image lane has been created.
        """
        assert len(self._guis) == laneIndex
        # We DELAY creating the GUI for this lane until the shell actually needs to view it.
        self._guis.append(None)

    def imageLaneRemoved(self, laneIndex, finalLength):
        """
        Called by the workflow when an image lane has been destroyed.
        """
        if len(self._guis) > finalLength:
            # Remove the GUI and clean it up.
            gui = self._guis.pop(laneIndex)
            if gui is not None:
                gui.stopAndCleanUp()

    def allowLaneSelectionChange(self):
        return True

    def setEnabled(self, enabled):
        self._enabled = enabled
        for gui in [x for x in self._guis if x]:
            gui.setEnabled(enabled)
        for blank_drawer in list(self._tempDrawers.values()):
            # Late import here to avoid importing qtpy in headless mode.
            import qtpy.compat

            if qtpy.compat.isalive(blank_drawer):
                blank_drawer.setEnabled(enabled)

    def isEnabled(self):
        return self._enabled

    def getGuis(self):
        return self._guis
