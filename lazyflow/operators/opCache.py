###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
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
