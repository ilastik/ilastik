#Python
import gc
import time
import threading
import logging
import gc
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)

#external dependencies
import blist
import psutil

#lazyflow
from lazyflow.utility import OrderedSignal

class MemInfoNode:
    def __init__(self):
        self.type = None
        self.id = None
        self.usedMemory = None
        self.dtype = None
        self.roi = None
        self.fractionOfUsedMemoryDirty = None
        self.lastAccessTime = None
        self.name = None
        self.children = []

class ArrayCacheMemoryMgr(threading.Thread):
    
    totalCacheMemory = OrderedSignal()

    loggingName = __name__ + ".ArrayCacheMemoryMgr"
    logger = logging.getLogger(loggingName)
    traceLogger = logging.getLogger("TRACE." + loggingName)

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

        self.caches = self._new_list()
        self.namedCaches = []

        self._max_usage = 85
        self._target_usage = 70
        self._lock = threading.Lock()
        self._last_usage = 0

    def _new_list(self):
        def getPrio(array_cache):
            return array_cache._cache_priority
        return blist.sortedlist((), getPrio)

    def addNamedCache(self, array_cache):
        """add a cache to a special list of named caches
        
           The list of named caches should contain only top-level caches.
           This way, when showing memory usage, we can provide a tree-view, where the
           named caches are the top-level items and the user can then drill down into the caches
           that are children of the top-level caches.
        """
        self.namedCaches.append(array_cache)

    def add(self, array_cache):
        with self._lock:
            self.caches.add(array_cache)

    def remove(self, array_cache):
        with self._lock:
            try:
                self.caches.remove(array_cache)
            except ValueError:
                pass

    def run(self):
        while True:
            vmem = psutil.virtual_memory()
            mem_usage = vmem.percent
            mem_usage_gb = (vmem.total - vmem.available) / (1e9)
            delta = abs(self._last_usage - mem_usage)
            if delta > 10 or self.logger.level == logging.DEBUG:
                cpu_usages = psutil.cpu_percent(interval=1, percpu=True)
                avg = sum(cpu_usages) / len(cpu_usages)
                self.logger.info( "RAM: {:1.3f} GB ({:02.0f}%), CPU: Avg={:02.0f}%, {}".format( mem_usage_gb, mem_usage, avg, cpu_usages ))
            if delta > 10:
                self._last_usage = mem_usage

            #calculate total memory usage and send as signal
            tot = 0.0
            for c in self.namedCaches:
                tot += c.usedMemory()
            self.totalCacheMemory(tot)
                
            time.sleep(10)

            if mem_usage > self._max_usage:
                self.logger.info("freeing memory...")
                with self._lock:
                    count = 0
                    not_freed = []
                    old_length = len(self.caches)
                    new_caches = self._new_list()
                    self.traceLogger.debug("Updating {} caches".format( len(self.caches) ))
                    for c in iter(self.caches):
                        c._updatePriority(c._last_access)
                        new_caches.add(c)
                    self.caches = new_caches
                    gc.collect()
                    self.traceLogger.debug("Target mem usage: {}".format(self._target_usage))
                    while mem_usage > self._target_usage and len(self.caches) > 0:
                        self.traceLogger.debug("Mem usage: {}".format(mem_usage))
                        last_cache = self.caches.pop(-1)
                            
                        freed = last_cache._freeMemory(refcheck = True)
                        self.traceLogger.debug("Freed: {}".format(freed))
                        mem_usage = psutil.phymem_usage().percent
                        count += 1
                        if freed == 0:
                            # store the caches which could not be freed
                            not_freed.append(last_cache)

                gc.collect()

                self.logger.info("freed %d/%d blocks, new usage = %f%%" % (count,old_length, mem_usage))
                
                for c in not_freed:
                    # add the caches which could not be freed
                    self.add(c)
