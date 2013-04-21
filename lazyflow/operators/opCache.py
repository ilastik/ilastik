#lazyflow
from lazyflow.graph import Operator
from lazyflow.operators.arrayCacheMemoryMgr import ArrayCacheMemoryMgr

class OpCache(Operator):
    """Implements the interface for a caching operator
    """
    
    def __init__(self, parent=None, graph=None):
        super(OpCache, self).__init__(parent=parent, graph=graph)
        if parent is None or not isinstance(parent, OpCache):
            ArrayCacheMemoryMgr.instance.addNamedCache(self)
            
    def generateReport(self, report):
        pass
        
    def usedMemory(self):
        """used memory in bytes"""
        return 0 #overwrite me
    
    def fractionOfUsedMemoryDirty(self):
        """fraction of the currently used memory that is marked as dirty"""
        return 0 #overwrite me

    def lastAccessTime(self):
        """timestamp of last access (time.time())"""
        return 0 #overwrite me
    