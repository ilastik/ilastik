# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

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
