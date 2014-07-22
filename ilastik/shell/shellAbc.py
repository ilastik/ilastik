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
from abc import ABCMeta, abstractmethod, abstractproperty

def _has_attribute( cls, attr ):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False

def _has_attributes( cls, attrs ):
    return True if all(_has_attribute(cls, a) for a in attrs) else False

class ShellABC(object):
    """
    This ABC defines the minimum interface that both the IlastikShell and HeadlessShell must implement.
    """
    
    __metaclass__ = ABCMeta

    @abstractproperty
    def workflow(self):
        raise NotImplementedError

    @abstractmethod
    def createAndLoadNewProject(self, newProjectFilePath, workflow_class):
        """
        """
        raise NotImplementedError

    @abstractmethod
    def openProjectFile(self, projectFilePath):
        """
        """
        raise NotImplementedError

    def setAppletEnabled(self, applet, enabled):
        pass

    def enableProjectChanges(self, enabled):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is ShellABC:
            return _has_attributes(C, ['workflow', 'createAndLoadNewProject', 'openProjectFile', 'setAppletEnabled'])
        return NotImplemented
