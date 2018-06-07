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
from lazyflow.utility.orderedSignal import OrderedSignal
from abc import ABCMeta, abstractproperty, abstractmethod
from future.utils import with_metaclass

class Applet( with_metaclass(ABCMeta, object) ):
    """
    Base class for all applets.  The shell and workflow depend on this interface only.
    Applets can subclass from this class directly, but in most cases it is easier to 
    subclass :py:class:`StandardApplet<ilastik.applets.base.standardApplet.StandardApplet>`.
    """

    _base_initialized = False

    def __init__( self, name, syncWithImageIndex=True, interactive=True ):
        """
        Constructor.
        Subclasses must call this base implementation in their own ``__init__`` methods.
        If they fail to do so, the shell raises an exception.

        :param name: The applet's name, which will appear as the applet drawer title.
        :param syncWithImageIndex: If True, the shell/workflow will add an image lane to this applet for each image in the interactive workflow. 
        :param interactive: If False, the applet controls won't be shown in the applet bar GUI.
        """
        self.name = name
        self.syncWithImageIndex = syncWithImageIndex
        self.__interactive = interactive
        self.busy = False

        #: Progress signal.
        #: When the applet is doing something time-consuming, this signal tells the shell to show a progress bar.
        #: Signature: ``__call__(percentComplete, canceled=False)``
        #:
        #: .. note:: To update the progress bar correctly, the shell expects that progress updates always 
        #:           begin with at least one zero update and end with at least one 100 update.
        #:           That is:
        #:           ``self.progressSignal(0)`` ... more updates ... ``self.progressSignal(100)``
        self.progressSignal = OrderedSignal()

        #: Shell request signal is used to trigger certain shell actions.
        #: Signature: ``__call__(request)``
        #:  where ``request`` is an integer corresponding to the action the shell should take.  
        #: The allowable actions are enumerated in the :py:class:`ShellRequest` class.
        #: Example invocation: ``self.shellRequest(ShellRequest.RequestSave)``
        self.shellRequestSignal = OrderedSignal()

        #: This signal informs the workflow that something has changed that might
        #:  affect the usability of various applets in the workflow.
        #: Signature: ``emit()``
        self.appletStateUpdateRequested = OrderedSignal()

        #: This signal tells the shell to send the dict 'data' to the (TCP) server 
        #: 'name' (if connected)
        #: Signature: ``__call__(servername, data)``
        self.sendMessageToServer = OrderedSignal()

        self._base_initialized = True

    @property
    def interactive(self):
        return self.__interactive

    @abstractproperty
    def topLevelOperator(self):
        """
        Abstract property.
        The applet's Top Level Operator, which is a single operator for all computation performed by the applet.
        Each applet has exactly one top-level operator for performing computations.
        Workflow managers can connect the top-level operator of one applet to others.
        """
        return None

    @abstractmethod
    def getMultiLaneGui(self):
        """
        Abstract method.
        Provides the applet's GUI, which must be an instance of :py:class:`AppletGuiInterface<ilastik.applets.base.appletGuiInterface.AppletGuiInterface>`.
        """
        raise NotImplementedError

    @property
    def dataSerializers(self):
        """
        A list of dataSerializer objects for loading/saving any project data the applet is responsible for.
        Each serializer must be an instance of :py:class:`AppletSerializer<ilastik.applets.base.appletSerializer.AppletSerializer>`
        Subclasses should override this property.  By default, returns [].
        """ 
        return []

    @property
    def base_initialized(self):
        # Do not override this property.
        # Used by the shell to ensure that Applet.__init__ was called by your subclass.
        return self._base_initialized


class DatasetConstraintError(Exception):
    def __init__(self, appletName, message, unfixable=False, fixing_dialogs=[]):
        """
        Args:
            fixing_dialogs: list of functions to show dialogs which can alleviate the dataset constraint. 
        """
        super().__init__()
        self.appletName = appletName
        self.message = message
        self.unfixable = unfixable
        self.fixing_dialogs = fixing_dialogs

    def __str__(self):
        return "Constraint of '{}' applet was violated: {}".format(self.appletName, self.message)

class ShellRequest(object):
    """
    This class enumerates the actions that applets can ask the shell to perform via :py:attr:`Applet.shellRequestSignal`.
    At the moment, there is only one supported action.
    """
    #: Request that the shell perform a "save project" action.
    RequestSave = 0
