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
import ilastik.utility

class ProjectMetadata(object):
    """
    Stores project metadata.
    Fires a signal if the metadata is changed.
    """
    def __init__(self):
        # This signal notifies subscribers that an item of metadata was changed
        self.changedSignal = ilastik.utility.SimpleSignal()

        self._projectName = ""
        self._labeler = ""
        self._description = ""

    @property
    def projectName(self):
        return self._projectName
    
    @projectName.setter
    def projectName(self, newProjectName):
        self._projectName = newProjectName
        self.changedSignal.emit()    

    @property
    def labeler(self):
        return self._labeler
    
    @labeler.setter
    def labeler(self, newLabeler):
        self._labeler = newLabeler
        self.changedSignal.emit()
        
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, newDescription):
        self._description = newDescription
        self.changedSignal.emit()
