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
from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu, QWidget


def _has_attribute(cls, attr):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False


def _has_attributes(cls, attrs):
    return True if all(_has_attribute(cls, a) for a in attrs) else False


class VolumeViewerGui(with_metaclass(ABCMeta, object)):
    """
    This class defines the methods which all GUIs with a volume editor/viewer should implement
    """

    def __init__(self, topLevelOperatorView):
        pass

    @abstractmethod
    def setViewerPos(self, pos5d):
        """
        Abstract method. Manually set the viewer position.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is VolumeViewerGui:
            return _has_attribute(C, "setViewerPos")
        return NotImplemented


class AppletGuiInterface(with_metaclass(ABCMeta, object)):
    """
    This is the abstract interface to which all applet GUI classes should adhere.
    """

    def __init__(self, topLevelOperatorView):
        pass

    @abstractmethod
    def centralWidget(self) -> Union["QWidget", None]:
        """
        Return the widget that will be displayed in the main viewer area.
        """
        raise NotImplementedError

    @abstractmethod
    def appletDrawer(self) -> Union["QWidget", None]:
        """
        Return the drawer widget for this applet.
        """
        raise NotImplementedError

    @abstractmethod
    def menus(self) -> Union[List["QMenu"], None]:
        """
        Return a list of QMenu widgets to be shown in the menu bar when this applet is visible.
        """
        raise NotImplementedError

    @abstractmethod
    def viewerControlWidget(self) -> Union["QWidget", None]:
        """
        Return the widget that controls how the content of the central widget is displayed.
        Typically this consists of a layer list control.
        """
        raise NotImplementedError

    @abstractmethod
    def setEnabled(self, enabled):
        """
        Enable or disable the gui, including applet drawer, central widget, menus, and viewer controls.
        """
        raise NotImplementedError

    @abstractmethod
    def setImageIndex(self, imageIndex: int):
        """
        Called by the shell when the user has switched the input image he wants to view.
        The GUI should respond by updating the content of the central widget.
        Note: Single-image GUIs do not need to provide this function.
        """
        raise NotImplementedError

    @abstractmethod
    def imageLaneAdded(self, laneIndex: int):
        """
        Called when a new image lane has been added to the workflow, and the GUI should respond appropriately.
        Note: The default GUI provided by StandardApplet overrides this for you.
        """
        raise NotImplementedError

    @abstractmethod
    def imageLaneRemoved(self, laneIndex: int, finalLength: int):
        """
        Called when a new image lane is about to be removed from the workflow, and the GUI should respond appropriately.
        The GUI should clean up any resourecs it owns.
        Note: The default GUI provided by StandardApplet overrides this for you.
        """
        raise NotImplementedError

    @abstractmethod
    def stopAndCleanUp(self):
        """
        Called when the GUI is about to be destroyed.
        The gui should stop updating all data views and should clean up any resources it created (e.g. orphan operators).
        """
        raise NotImplementedError

    @abstractmethod
    def allowLaneSelectionChange(self):
        """
        Called by the shell to determine if the shell's lane selection combobox should be displayed.
        Return False if your applet GUI handles switching between lanes itself (e.g. DataSelection, DataExport),
        or if the notion of lanes doesn't apply to this applet (e.g. DataSelection, BatchProcessing).
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is AppletGuiInterface:
            requiredMethods = [
                "centralWidget",
                "appletDrawer",
                "menus",
                "viewerControlWidget",
                "setEnabled",
                "setImageIndex",
                "imageLaneAdded",
                "imageLaneRemoved",
                "allowLaneSelectionChange",
                "stopAndCleanUp",
            ]
            return True if _has_attributes(C, requiredMethods) else False
        return NotImplemented
