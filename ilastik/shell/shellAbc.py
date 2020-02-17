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

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Type

from ilastik.utility.abc import StrictABC

if TYPE_CHECKING:
    from ilastik.applets.base.applet import Applet
    from ilastik.workflow import Workflow


class ShellABC(StrictABC):
    @property
    @abstractmethod
    def workflow(self):
        pass

    @property
    @abstractmethod
    def currentImageIndex(self) -> int:
        pass

    @abstractmethod
    def createAndLoadNewProject(self, newProjectFilePath: str, workflow_class: Type[Workflow]) -> None:
        pass

    @abstractmethod
    def openProjectFile(self, projectFilePath: str) -> None:
        pass

    @abstractmethod
    def setAppletEnabled(self, applet: Applet, enabled: bool) -> None:
        pass

    @abstractmethod
    def isAppletEnabled(self, applet: Applet) -> bool:
        pass

    @abstractmethod
    def enableProjectChanges(self, enabled: bool) -> None:
        pass
