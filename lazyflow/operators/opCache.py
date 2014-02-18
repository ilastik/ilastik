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

#lazyflow
from lazyflow.graph import Operator
from lazyflow.operators.arrayCacheMemoryMgr import ArrayCacheMemoryMgr

class OpCache(Operator):
    """Implements the interface for a caching operator
    """
    
    def __init__(self, parent=None, graph=None):
        super(OpCache, self).__init__(parent=parent, graph=graph)
            
    def generateReport(self, report):
        raise NotImplementedError()
        
    def usedMemory(self):
        """used memory in bytes"""
        return 0 #overwrite me
    
    def fractionOfUsedMemoryDirty(self):
        """fraction of the currently used memory that is marked as dirty"""
        return 0 #overwrite me

    def lastAccessTime(self):
        """timestamp of last access (time.time())"""
        return 0 #overwrite me
    
    def _after_init(self):
        """
        Overridden from Operator
        """
        super( OpCache, self )._after_init()

        # Register with the manager here, AFTER we're fully initialized
        # Otherwise it isn't safe for the manager to poll our stats.
        if self.parent is None or not isinstance(self.parent, OpCache):
            ArrayCacheMemoryMgr.instance.addNamedCache(self)
