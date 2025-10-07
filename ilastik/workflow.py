###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
from abc import abstractproperty, abstractmethod
from lazyflow.graph import Operator, Graph
from string import ascii_uppercase
from ilastik.shell.shellAbc import ShellABC
import logging

from typing import List, Tuple, Type, TYPE_CHECKING, Iterator, Optional, Union

if TYPE_CHECKING:
    from qtpy.QtWidgets import QMenu


logger = logging.getLogger(__name__)


class Workflow(Operator):
    """
    Base class for all workflows.
    """

    name = "Workflow (base class)"
    workflowDisplayName = None  # override in your own workflow if you need it different from name
    #: Should workflow added to start widget
    show_in_startup_menu = True

    @abstractproperty
    def applets(self):
        """
        Abstract property. Return the list of applets that are owned by this workflow.
        """
        return []

    @abstractproperty
    def imageNameListSlot(self):
        """
        Abstract property.  Return the "image name list" slot, which lists the names of
        all image lanes (i.e. files) currently loaded by the workflow.
        This slot is typically provided by the DataSelection applet via its ImageName slot.
        """
        return None

    @property
    def workflowName(self):
        originalName = self.__class__.__name__
        wname = originalName[0]
        for i in originalName[1:]:
            if i in ascii_uppercase:
                wname += " "
            wname += i
        if wname.endswith(" Workflow"):
            wname = wname[:-9]

        return wname

    @property
    def workflowDescription(self):
        return None

    @property
    def defaultAppletIndex(self):
        return 0

    @property
    def shell(self):
        return self._shell

    @abstractmethod
    def connectLane(self, laneIndex):
        """
        When a new image lane has been added to the workflow, this workflow base class does the following:

        1) Create room for the new image lane by adding a lane to each applet's topLevelOperator
        2) Ask the subclass to hook up the new image lane by calling this function.
        """
        raise NotImplementedError

    def prepareForNewLane(self, laneIndex):
        """
        Workflows may override this method to prepare for a new
        lane, before the new lane is actually inserted.

        For example they may copy cache states that will be invalidated by
        the insertion of the new lane, and restore those caches at the end
        of connectLane().
        """
        pass

    def handleNewLanesAdded(self):
        """
        Called immediately after a new lane is fully initialized with data.
        If a workflow wants to restore state previously saved in prepareForNewLane(),
        this is the place to do it.

        This function must be called by any code that can add new lanes to the workflow and initialize them.
        That happens in only two places: The DataSelectionGui, and the BatchProcessingApplet.
        """
        pass

    def onProjectLoaded(self, projectManager):
        """
        Called by the project manager after the project is loaded (deserialized).
        Extra workflow initialization be done here.
        """
        pass

    def handleAppletStateUpdateRequested(self):
        """
        Called when an applet has fired the :py:attr:`Applet.statusUpdateSignal`
        Workflow subclasses should reimplement this method to enable/disable applet gui's
        """
        pass

    def handleSendMessageToServer(self, name, data):
        try:
            server = self._shell.socketServer
            server.send(name, data)
        except Exception as e:
            logger.error("Failed sending message to server '%s': %s" % (name, e))

    def postprocessClusterSubResult(self, roi, result, blockwise_fileset):
        pass

    def __init__(
        self, shell, headless=False, workflow_cmdline_args=(), project_creation_args=(), parent=None, graph=None
    ):
        """
        Constructor.  Subclasses MUST call this in their own ``__init__`` functions.
        The parent and graph parameters will be passed directly to the Operator base class. If both are None,
        a new Graph is instantiated internally.

        :param headless: Set to True if this workflow is being instantiated by a "headless" script,
                         in which case the workflow should not attempt to access applet GUIs.
        :param workflow_cmdline_args: a (possibly empty) sequence of arguments to control
                                      the workflow from the command line
        :param project_creation_args: The original workflow_cmdline_args used when the project was first created.
        :param parent: The parent operator of the workflow or None (see also: Operator)
        :param graph: The graph instance the workflow is assigned to (see also: Operator)

        """

        assert isinstance(shell, ShellABC), "Expected an instance of IlastikShell or HeadlessShell.  Got {}".format(
            shell
        )
        if not (parent or graph):
            graph = Graph()
        super(Workflow, self).__init__(parent=parent, graph=graph)
        self._shell = shell
        self._headless = headless

    def cleanUp(self):
        """
        The user closed the project, so this workflow is being destroyed.
        Tell the applet GUIs to stop processing data, and free any resources that are owned by this workflow or its applets.
        """
        if not self._headless:
            # Stop and clean up the GUIs before we invalidate the operators they depend on.
            for a in self.applets:
                a.getMultiLaneGui().stopAndCleanUp()

        # Clean up the graph as usual.
        super(Workflow, self).cleanUp()

    def menus(self) -> Union[List["QMenu"], None]:
        """
        Returns an iterable of QMenus to be added to the GUI

        Returns:
            iterable:       QMenus to be added to the GUI
        """

        return []

    @classmethod
    def getSubclass(cls, name):
        for subcls in cls.all_subclasses:
            if subcls.__name__ == name:
                return subcls
        raise RuntimeError(f"No known workflow class has name {name}")

    def _after_init(self):
        """
        Overridden from Operator.
        """
        Operator._after_init(self)

        # When a new image is added to the workflow, each applet should get a new lane.
        self.imageNameListSlot.notifyInserted(self._createNewImageLane)
        self.imageNameListSlot.notifyRemove(self._removeImageLane)

        for applet in self.applets:
            applet.appletStateUpdateRequested.subscribe(self.handleAppletStateUpdateRequested)
            applet.sendMessageToServer.subscribe(self.handleSendMessageToServer)

    def _createNewImageLane(self, multislot, index, *args):
        """
        A new image lane is being added to the workflow.  Add a new lane to each applet and hook it up.
        """
        self.prepareForNewLane(index)

        for a in self.applets:
            if a.syncWithImageIndex and a.topLevelOperator is not None:
                a.topLevelOperator.addLane(index)

        self.connectLane(index)

        if not self._headless:
            for a in self.applets:
                a.getMultiLaneGui().imageLaneAdded(index)

    def _removeImageLane(self, multislot, index, finalLength):
        """
        An image lane is being removed from the workflow.  Remove it from each of the applets.
        """
        if not self._headless:
            for a in self.applets:
                a.getMultiLaneGui().imageLaneRemoved(index, finalLength)

        for a in self.applets:
            if a.syncWithImageIndex and a.topLevelOperator is not None:
                a.topLevelOperator.removeLane(index, finalLength)


def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__() for g in all_subclasses(s)]


def getAvailableWorkflows() -> Iterator[Tuple[Type[Workflow], str, str]]:
    """
    This function used to iterate over all workflows that have been imported so far,
    but now we rely on the explicit list in workflows/__init__.py,
    and add any extra auto-discovered workflows at the end.

    Yields:
        tuple of workflow_class, workflow_name, workflow_display_name
        where
        * workflow_class can be used by the shell to instantiate a new workflow/project,
        * workflow_name is a string representation (that should not change) that is also
          saved in projects and used to identify the workflow,
        * workflow_display_name is a human readable version of the workflow string to be presented
          to the user.
    """
    alreadyListed = set()

    from . import workflows

    def _makeWorkflowTuple(workflow_cls: Type[Workflow]):
        if isinstance(workflow_cls.workflowName, str):
            if workflow_cls.workflowDisplayName is None:
                workflow_cls.workflowDisplayName = workflow_cls.workflowName
            return workflow_cls, workflow_cls.workflowName, workflow_cls.workflowDisplayName
        else:
            originalName = workflow_cls.__name__
            wname = originalName[0]
            for i in originalName[1:]:
                if i in ascii_uppercase:
                    wname += " "
                wname += i
            if wname.endswith(" Workflow"):
                wname = wname[:-9]
            if workflow_cls.workflowDisplayName is None:
                workflow_cls.workflowDisplayName = wname

            return workflow_cls, wname, workflow_cls.workflowDisplayName

    for W in all_subclasses(Workflow):
        if W.__name__ in alreadyListed:
            continue
        alreadyListed.add(W.__name__)
        # this is a hack to ensure the base object workflow does not
        # appear in the list of available workflows.
        try:
            isbase = "base" in W.workflowName.lower()
        except:
            isbase = False

        if isbase:
            continue

        yield _makeWorkflowTuple(W)


def getWorkflowFromName(name: str) -> Optional[Type[Workflow]]:
    """return workflow by naming its workflowName variable"""
    for w, _name, _displayName in getAvailableWorkflows():
        if _name == name or w.__name__ == name or _displayName == name:
            return w
    return None
