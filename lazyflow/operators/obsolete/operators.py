import lazyflow
import numpy

from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view, TinyVector
from Queue import Empty
from collections import deque
from lazyflow.h5dumprestore import stringToClass
import greenlet, threading
import vigra
import copy
import gc
import sys
import weakref
from threading import current_thread, Lock, RLock
from lazyflow import request
import generic
import itertools
from lazyflow.rtype import SubRegion
import time
from functools import partial
import threading
import psutil
import gc

try:
    import blist
    has_blist = True
except:
    has_blist = False
    err =  "##############################################################"
    err += "#                                                            #"
    err += "#           please install blist (easy_install blist)        #"
    err += "#           otherwise OpSparseLabelArray will be missing     #"
    err += "#                                                            #"
    err += "##############################################################"
    raise RuntimeError(err)

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger("TRACE." + __name__)
from lazyflow.tracer import Tracer

class OpArrayPiper(Operator):
    name = "ArrayPiper"
    description = "simple piping operator"

    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]

    def setupOutputs(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"].meta.assignFrom(inputSlot.meta)

    def execute(self, slot, roi, result):
        key = roi.toSlice()
        req = self.inputs["Input"][key].writeInto(result)
        req.wait()
        return result

    def notifyDirty(self,slot,key):
        # Check for proper name because subclasses may define extra inputs.
        # (but decline to override notifyDirty)
        if slot.name == 'Input':
            self.outputs["Output"].setDirty(key)
        else:
            # If some input we don't know about is dirty (i.e. we are subclassed by an operator with extra inputs),
            # then mark the entire output dirty.  This is the correct behavior for e.g. 'sigma' inputs.
            self.outputs["Output"].setDirty(slice(None))

    def setInSlot(self, slot, key, value):
        self.outputs["Output"][key] = value

    @property
    def shape(self):
        return self.outputs["Output"].meta.shape

    @property
    def dtype(self):
        return self.outputs["Output"].meta.dtype



class OpMultiArrayPiper(Operator):
    name = "MultiArrayPiper"
    description = "simple piping operator"

    inputSlots = [MultiInputSlot("MultiInput")]
    outputSlots = [MultiOutputSlot("MultiOutput")]

    def setupOutputs(self):
        inputSlot = self.inputs["MultiInput"]

        self.outputs["MultiOutput"].resize(len(inputSlot)) #clearAllSlots()
        for i,islot in enumerate(self.inputs["MultiInput"]):
            oslot = self.outputs["MultiOutput"][i]
            if islot.partner is not None:
                oslot._dtype = islot.meta.dtype
                oslot._shape = islot.meta.shape
                oslot._axistags = islot.meta.axistags

    def notifySubSlotInsert(self,slots,indexes):
        self.outputs["MultiOutput"]._insertNew(indexes[0])

    def notifySubSlotRemove(self, slots, indexes):
        self.outputs["MultiOutput"].pop(indexes[0])

    def notifySubSlotResize(self,slots,indexes,size,event):
        self.outputs["MultiOutput"].resize(size,event = event)

    def getOutSlot(self, slot, key, result):
        raise RuntimeError("OpMultiPipler does not support getOutSlot")

    def getSubOutSlot(self, slots, indexes, key, result):
        req = self.inputs["MultiInput"][indexes[0]][key].writeInto(result)
        res = req.wait()
        return res

    def setInSlot(self, slot, key, value):
        raise RuntimeError("OpMultiPipler does not support setInSlot")

    def setSubInSlot(self,multislot,slot,index, key,value):
        pass

    def notifySubSlotDirty(self,slots,indexes,key):
        self.outputs["MultiOutput"][indexes[0]].setDirty(key)

class OpMultiMultiArrayPiper(Operator):
    name = "MultiMultiArrayPiper"
    description = "simple piping operator"

    inputSlots = [MultiInputSlot("MultiInput", level = 2)]
    outputSlots = [MultiOutputSlot("MultiOutput", level = 2)]

    def setupOutputs(self):
        inputSlot = self.inputs["MultiInput"]

        self.outputs["MultiOutput"].resize(len(inputSlot)) #clearAllSlots()
        for i,mislot in enumerate(self.inputs["MultiInput"]):
            self.outputs["MultiOutput"][i].resize(len(mislot))
            for ii,islot in enumerate(mislot):
                oslot = self.outputs["MultiOutput"][i][ii]
                if islot.partner is not None:
                    oslot.meta.dtype = islot.meta.dtype
                    oslot.meta.shape = islot.meta.shape
                    oslot.meta.axistags = islot.meta.axistags

    def getOutSlot(self, slot, key, result):
        raise RuntimeError("OpMultiMultiPipler does not support getOutSlot")

    def getSubOutSlot(self, slots, indexes, key, result):
        req = self.inputs["MultiInput"][indexes[0]][indexes[1]][key].writeInto(result)
        res = req()
        return res

    def setInSlot(self, slot, key, value):
        raise RuntimeError("OpMultiPipler does not support setInSlot")

    def setSubInSlot(self,multislot,slot,index, key,value):
        pass

    def notifySubSlotDirty(self,slots,indexes,key):
        self.outputs["Output"][indexes[0]][indexes[1]].setDirty(key)



try:
    from  lazyflow.drtile import drtile
except:
    raise RuntimeError("Error importing drtile, please use cmake to compile lazyflow.drtile !")

class BlockQueue(object):
    __slots__ = ["queue","lock"]

    def __init__(self):
        self.queue = None
        self.lock = threading.Lock()

class FakeGetItemRequestObject(object):
    def __init__(self,gr):
        self.greenlet = gr
        self.lock = threading.Lock()
        self.thread = threading.current_thread()
        self.requestID = self.thread.runningRequestID

        if hasattr(self.thread, "currentRequestLevel"):
            self.requestLevel = self.thread.currentRequestLevel + 1
        else:
            self.requestLevel = 1
            self.thread = graph.workers[0]

class OpRequestSplitter(OpArrayPiper):
    name = "RequestSplitter"
    description = "split requests into two parts along longest axis"
    category = "misc"

    def getOutSlot(self, slot, key, result):
        start, stop = sliceToRoi(key, self.shape)

        diff = stop-start

        splitDim = numpy.argmax(diff[:-1])
        splitPos = start[splitDim] + diff[splitDim] / 2

        stop2 = stop.copy()
        stop2[splitDim] = splitPos
        start2 = start.copy()
        start2[splitDim] = splitPos


        destStart = start -start # zeros
        destStop = stop - start

        destStop2 = destStop.copy()
        destStop2[splitDim] = diff[splitDim] / 2
        destStart2 = destStart.copy()
        destStart2[splitDim] = diff[splitDim] / 2

        writeKey1 = roiToSlice(destStart,destStop2)
        writeKey2 = roiToSlice(destStart2,destStop)

        key1 = roiToSlice(start,stop2)
        key2 = roiToSlice(start2,stop)

        req1 = self.inputs["Input"][key1].writeInto(result[writeKey1])
        req2 = self.inputs["Input"][key2].writeInto(result[writeKey2])
        req1.wait()
        req2.wait()

def fastWhere(cond, A, B, dtype):
    nonz = numpy.nonzero(cond)
    res = numpy.ndarray(cond.shape, dtype)
    res[:] = B
    if isinstance(A,numpy.ndarray):
        res[nonz] = A[nonz]
    else:
        res[nonz] = A
    return res



class ArrayCacheMemoryMgr(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

        self.caches = self._new_list()

        self._max_usage = 85
        self._target_usage = 70
        self._lock = threading.Lock()
        self._last_usage = 0

    def _new_list(self):
        def getPrio(array_cache):
            return array_cache._cache_priority
        return blist.sortedlist((), getPrio)

    def add(self, array_cache):
        self._lock.acquire()
        self.caches.add(array_cache)
        self._lock.release()

    def remove(self, array_cache):
        self._lock.acquire()
        try:
            self.caches.remove(array_cache)
        except ValueError:
            pass
        self._lock.release()

    def run(self):
        while True:
            time.sleep(2)      
            mem_usage = psutil.phymem_usage().percent

            delta = abs(self._last_usage - mem_usage)
            if delta > 10:
                logger.info("Memory Manager: usage = %f%%" % mem_usage)
                self._last_usage = mem_usage

            if mem_usage > self._max_usage:
                logger.info("Memory Manager: freeing memory...")
                self._lock.acquire()
                count = 0
                not_freed = []
                old_length = len(self.caches)
                new_caches = self._new_list()
                for c in iter(self.caches):
                    c._updatePriority(c._last_access)
                    new_caches.add(c)
                self.caches = new_caches
                gc.collect()
                while mem_usage > self._target_usage and len(self.caches) > 0:
                    last_cache = self.caches.pop(-1)
                    freed = last_cache._freeMemory(refcheck = False)
                    mem_usage = psutil.phymem_usage().percent
                    count += 1
                    if freed == 0:
                        # store the caches which could not be freed
                        not_freed.append(last_cache)
                self._lock.release()
                gc.collect()
                if mem_usage < self._target_usage:
                    logger.info("Memory Manager: freed %d/%d blocks, new usage = %f%%" % (count,old_length, mem_usage))
                else:
                    logger.info("Memory Manager: freed all (%d/%d) blocks, new usage = %f%%, failed goal of %f since all other blocks are currently in use." % (count, old_length,mem_usage, self._target_usage))
                
                for c in not_freed:
                    # add the caches which could not be freed
                    self.add(c)




# create global Memory Manager instance
if not hasattr(ArrayCacheMemoryMgr, "instance"):
    mgr = ArrayCacheMemoryMgr() 
    setattr(ArrayCacheMemoryMgr, "instance" ,mgr)
    mgr.start()


class OpArrayCache(OpArrayPiper):
    name = "ArrayCache"
    description = "numpy.ndarray caching class"
    category = "misc"

    inputSlots = [InputSlot("Input"), InputSlot("blockShape", value = 64), InputSlot("fixAtCurrent", value = False)]
    outputSlots = [OutputSlot("Output")]

    loggingName = __name__ + ".OpArrayCache"
    logger = logging.getLogger(loggingName)
    traceLogger = logging.getLogger("TRACE." + loggingName)

    # Block states
    IN_PROCESS = 0
    DIRTY = 1
    CLEAN = 2
    FIXED_DIRTY = 3

    def __init__(self, *args, **kwargs):
        with Tracer(self.traceLogger):
            super( OpArrayPiper, self ).__init__(*args, **kwargs)
            self._origBlockShape = 64
            self._blockShape = None
            self._dirtyShape = None
            self._blockState = None
            self._dirtyState = None
            self._fixed = False
            self._cache = None
            self._lock = Lock()
            self._cacheLock = request.Lock()#greencall.Lock()
            self._lazyAlloc = True
            self._cacheHits = 0
            self.graph._registerCache(self)
            self._has_fixed_dirty_blocks = False
            self._memory_manager = ArrayCacheMemoryMgr.instance
            self._running = 0
            lazyflow.verboseMemory = True

    def _memorySize(self):
        if self._cache is not None:
            return self._cache.nbytes
        else:
            return 0

    def _freeMemory(self, refcheck = True):
        with Tracer(self.traceLogger):
            self._cacheLock.acquire()
            freed  = self._memorySize()
            if self._cache is not None:
                fshape = self._cache.shape
                try:
                    self._cache.resize((1,), refcheck = refcheck)
                except ValueError:
                    freed = 0
                    if lazyflow.verboseMemory:
                        self.logger.warn("OpArrayCache: freeing failed due to view references")
                if freed > 0:
                    if lazyflow.verboseMemory:
                        self.logger.debug("OpArrayCache: freed cache of shape:{}".format(fshape))
    
                    self._lock.acquire()
                    self._blockState[:] = OpArrayCache.DIRTY
                    del self._cache
                    self._cache = None
                    self._lock.release()
            self._cacheLock.release()
            return freed

    def _allocateManagementStructures(self):
        with Tracer(self.traceLogger):
            if type(self._origBlockShape) != tuple:
                self._blockShape = (self._origBlockShape,)*len(self.shape)
            else:
                self._blockShape = self._origBlockShape
    
            self._blockShape = numpy.minimum(self._blockShape, self.shape)
    
            self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
    
            if lazyflow.verboseMemory:
                self.logger.debug("Configured OpArrayCache with shape={}, blockShape={}, dirtyShape={}, origBlockShape={}".format(self.shape, self._blockShape, self._dirtyShape, self._origBlockShape))
    
            # if the entry in _dirtyArray differs from _dirtyState
            # the entry is considered dirty
            self._blockQuery = numpy.ndarray(self._dirtyShape, dtype=object)
            self._blockState = OpArrayCache.DIRTY * numpy.ones(self._dirtyShape, numpy.uint8)
    
            _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
            _blockNumbers.shape = self._dirtyShape
    
            _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
            _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)
    
    
    #        self._blockNumbers = _blockNumbers
    #        self._blockIndices = _blockIndices
    #
            self._blockState[:]= OpArrayCache.DIRTY
            self._dirtyState = OpArrayCache.CLEAN
    
            # allocate queryArray object
            self._flatBlockIndices =  _blockIndices[:]
            self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)
    #        for p in self._flatBlockIndices:
    #            self._blockQuery[p] = BlockQueue()


    def _allocateCache(self):
        with Tracer(self.traceLogger):
            self._cacheLock.acquire()
            self._last_access = None
            self._cache_priority = 0
            self._running = 0

            if self._cache is None or (self._cache.shape != self.shape):
                mem = numpy.zeros(self.shape, dtype = self.dtype)
                if lazyflow.verboseMemory:
                    self.logger.debug("OpArrayCache: Allocating cache (size: %dbytes)" % mem.nbytes)
                self.graph._notifyMemoryAllocation(self, mem.nbytes)
                if self._blockState is None:
                    self._allocateManagementStructures()
                self._cache = mem
            self._memory_manager.add(self)
            self._cacheLock.release()

    def setupOutputs(self):
        with Tracer(self.traceLogger):
            reconfigure = False
            if  self.inputs["fixAtCurrent"].ready():
                self._fixed =  self.inputs["fixAtCurrent"].value
    
            if self.inputs["blockShape"].ready() and self.inputs["Input"].ready():
                newBShape = self.inputs["blockShape"].value
                if self._origBlockShape != newBShape and self.inputs["Input"].ready():
                    reconfigure = True
                self._origBlockShape = newBShape
                OpArrayPiper.setupOutputs(self)
    
            if reconfigure and self.shape is not None:
                self._lock.acquire()
                self._allocateManagementStructures()
                if not self._lazyAlloc:
                    self._allocateCache()
                self._lock.release()



    def notifyDirty(self, slot, key):
        if slot == self.inputs["Input"]:
            start, stop = sliceToRoi(key, self.shape)

            with self._lock:
                if self._cache is not None:
                    blockStart = numpy.floor(1.0 * start / self._blockShape)
                    blockStop = numpy.ceil(1.0 * stop / self._blockShape)
                    blockKey = roiToSlice(blockStart,blockStop)
                    if self._fixed:
                        # If this block was clean before we became fixed and now it's dirty,
                        #  mark it so we can notify downstream operators that this block is dirty once we become unfixed.
                        # We only care about blocks that weren't already dirty (because the downstream operators were 
                        #  already notified of any blocks that were dirty before we became fixed.)
                        self._blockState[blockKey] = numpy.where(self._blockState[blockKey] != OpArrayCache.DIRTY, 
                                                                 OpArrayCache.FIXED_DIRTY,
                                                                 self._blockState[blockKey])
                        self._has_fixed_dirty_blocks = True
                    else:
                        self._blockState[blockKey] = OpArrayCache.DIRTY

            if not self._fixed:
                self.outputs["Output"].setDirty(key)
        if slot == self.inputs["fixAtCurrent"]:
            if self.inputs["fixAtCurrent"].ready():
                self._fixed = self.inputs["fixAtCurrent"].value
                if not self._fixed and self._cache is not None and self._has_fixed_dirty_blocks:
                    # We've become unfixed, so we need to notify downstream 
                    #  operators of every block that became dirty while we were fixed.
                    # Convert all FIXED_DIRTY states into DIRTY states
                    with self._lock:
                        cond = (self._blockState[...] == OpArrayCache.FIXED_DIRTY)
                        self._blockState[...]  = fastWhere(cond, OpArrayCache.DIRTY, self._blockState, numpy.uint8)
                        self._has_fixed_dirty_blocks = False
                    newDirtyBlocks = numpy.transpose(numpy.nonzero(cond))
                    
                    # To avoid lots of setDirty notifications, we simply merge all the dirtyblocks into one single superblock.
                    # This should be the best option in most cases, but could be bad in some cases.
                    # TODO: Optimize this by merging the dirty blocks via connected components or something.
                    cacheShape = numpy.array(self._cache.shape)
                    dirtyStart = cacheShape
                    dirtyStop = [0] * len(cacheShape)
                    for index in newDirtyBlocks:
                        blockStart = index * self._blockShape
                        blockStop = numpy.minimum(blockStart + self._blockShape, cacheShape)
                        
                        dirtyStart = numpy.minimum(dirtyStart, blockStart)
                        dirtyStop = numpy.maximum(dirtyStop, blockStop)

                    if len(newDirtyBlocks > 0):
                        self.Output.setDirty( dirtyStart, dirtyStop )

    def _updatePriority(self, new_access = None):
        if self._last_access is None:
            self._last_access = new_access or time.time()
        cur_time = time.time()
        delta = cur_time - self._last_access + 1e-9

        self._last_access = cur_time
        new_prio = 0.5 * self._cache_priority + delta
        self._cache_priority = new_prio

        


    def execute(self,slot,roi,result):
        #return
        key = roi.toSlice()

        start, stop = sliceToRoi(key, self.shape)

        self.traceLogger.debug("Acquiring ArrayCache lock...")
        self._lock.acquire()
        self.traceLogger.debug("ArrayCache lock acquired.")

        ch = self._cacheHits
        ch += 1
        self._cacheHits = ch

        cacheView = self._cache #prevent freeing of cache during running this function

        if self._cache is None:
            self._allocateCache()
        if self._running == 0:
            self._memory_manager.remove(self)
        self._running += 1

        blockStart = (1.0 * start / self._blockShape).floor()
        blockStop = (1.0 * stop / self._blockShape).ceil()
        blockKey = roiToSlice(blockStart,blockStop)

        blockSet = self._blockState[blockKey]

        # this is a little optimization to shortcut
        # many lines of python code when all data is
        # is already in the cache:
        if numpy.logical_or(blockSet == OpArrayCache.CLEAN, blockSet == OpArrayCache.FIXED_DIRTY).all():
            result[:] = self._cache[roiToSlice(start, stop)]
            self._running -= 1
            self._updatePriority()
            if self._running == 0:
                self._memory_manager.add(self)
            cacheView = None
            self._lock.release()
            return

        inProcessQueries = numpy.unique(numpy.extract( blockSet == OpArrayCache.IN_PROCESS, self._blockQuery[blockKey]))

        cond = (blockSet == OpArrayCache.DIRTY)
        tileWeights = fastWhere(cond, 1, 128**3, numpy.uint32)
        trueDirtyIndices = numpy.nonzero(cond)

        tileArray = drtile.test_DRTILE(tileWeights, 128**3).swapaxes(0,1)

        dirtyRois = []
        half = tileArray.shape[0]/2
        dirtyRequests = []

        def onCancel(req):
            return False # indicate that this request cannot be canceled

        self.traceLogger.debug("Creating cache input requests")
        for i in range(tileArray.shape[1]):

            drStart3 = tileArray[:half,i]
            drStop3 = tileArray[half:,i]
            drStart2 = drStart3 + blockStart
            drStop2 = drStop3 + blockStart
            drStart = drStart2*self._blockShape
            drStop = drStop2*self._blockShape

            drStop = numpy.minimum(drStop, self.shape)
            drStart = numpy.minimum(drStart, self.shape)

            key3 = roiToSlice(drStart3,drStop3)
            key2 = roiToSlice(drStart2,drStop2)

            key = roiToSlice(drStart,drStop)

            if not self._fixed:
                dirtyRois.append([drStart,drStop])

                req = self.inputs["Input"][key].writeInto(self._cache[key])

                req.onCancel(onCancel)

                dirtyRequests.append((req,key2, key3))

                self._blockQuery[key2] = req

                #sanity check:
                if (self._blockState[key2] != OpArrayCache.DIRTY).any():
                    print "original condition", cond
                    print "original tilearray", tileArray, tileArray.shape
                    print "original tileWeights", tileWeights, tileWeights.shape
                    print "sub condition", self._blockState[key2] == OpArrayCache.DIRTY
                    print "START, STOP", drStart2, drStop2
                    import h5py
                    f = h5py.File("test.h5", "w")
                    f.create_dataset("data",data = tileWeights)
                    print "%r \n %r \n %r\n %r\n %r \n%r" % (key2, blockKey,self._blockState[key2], self._blockState[blockKey][trueDirtyIndices],self._blockState[blockKey],tileWeights)
                    assert 1 == 2
        # indicate the inprocessing state, by setting array to 0 (i.e. IN_PROCESS)
        if not self._fixed:
            blockSet[:]  = fastWhere(cond, OpArrayCache.IN_PROCESS, blockSet, numpy.uint8)
        else:
            # Someone asked for some dirty blocks while we were fixed.
            # Mark these blocks to be signaled as dirty when we become unfixed
            blockSet[:]  = fastWhere(cond, OpArrayCache.FIXED_DIRTY, blockSet, numpy.uint8)
            self._has_fixed_dirty_blocks = True
        self._lock.release()

        temp = itertools.count(0)

        #wait for all requests to finish
        self.traceLogger.debug( "Firing all {} cache input requests...".format(len(dirtyRequests)) )
        for req, reqBlockKey, reqSubBlockKey in dirtyRequests:
            res = req.wait()
        self.traceLogger.debug( "All cache input requests received." )

        # indicate the finished inprocess state (i.e. CLEAN)
        if not self._fixed and temp.next() == 0:
            with self._lock:
                blockSet[:] = fastWhere(cond, OpArrayCache.CLEAN, blockSet, numpy.uint8)
                self._blockQuery[blockKey] = fastWhere(cond, None, self._blockQuery[blockKey], object)


        #wait for all in process queries
        for req in inProcessQueries:
            req.wait()
            req.clean()

        # finally, store results in result area
        self._lock.acquire()
        if self._cache is not None:
            result[:] = self._cache[roiToSlice(start, stop)]
        else:
            self.traceLogger.debug( "WAITING FOR INPUT WITH THE CACHE LOCK LOCKED!" )
            self.inputs["Input"][roiToSlice(start, stop)].writeInto(result).wait()
            self.traceLogger.debug( "INPUT RECEIVED WITH THE CACHE LOCK LOCKED." )
        self._running -= 1
        self._updatePriority()
        if self._running == 0:
            self._memory_manager.add(self)
        cacheView = None

        self._lock.release()

    def setInSlot(self, slot, key, value):
        if slot == self.inputs["Input"]:
            ch = self._cacheHits
            ch += 1
            self._cacheHits = ch
            start, stop = sliceToRoi(key, self.shape)
            blockStart = numpy.ceil(1.0 * start / self._blockShape)
            blockStop = numpy.floor(1.0 * stop / self._blockShape)
            blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
            blockKey = roiToSlice(blockStart,blockStop)

            if (self._blockState[blockKey] != OpArrayCache.CLEAN).any():
                start2 = blockStart * self._blockShape
                stop2 = blockStop * self._blockShape
                stop2 = numpy.minimum(stop2, self.shape)
                key2 = roiToSlice(start2,stop2)
                self._lock.acquire()
                if self._cache is None:
                    self._allocateCache()
                self._cache[key2] = value[roiToSlice(start2-start,stop2-start)]
                self._blockState[blockKey] = self._dirtyState
                self._blockQuery[blockKey] = None
                self._lock.release()

            #pass request on
            #if not self._fixed:
            #    self.outputs["Output"][key] = value
        if slot == self.inputs["fixAtCurrent"]:
            self._fixed = value
            assert 1==2



    def dumpToH5G(self, h5g, patchBoard):
        h5g.dumpSubObjects({
                    "graph": self.graph,
                    "inputs": self.inputs,
                    "outputs": self.outputs,
                    "_origBlockShape" : self._origBlockShape,
                    "_blockShape" : self._blockShape,
                    "_dirtyShape" : self._dirtyShape,
                    "_blockState" : self._blockState,
                    "_dirtyState" : self._dirtyState,
                    "_cache" : self._cache,
                    "_lazyAlloc" : self._lazyAlloc,
                    "_cacheHits" : self._cacheHits,
                    "_fixed" : self._fixed
                },patchBoard)


    @classmethod
    def reconstructFromH5G(cls, h5g, patchBoard):

        g = h5g["graph"].reconstructObject(patchBoard)

        op = stringToClass(h5g.attrs["className"])(g)

        patchBoard[h5g.attrs["id"]] = op
        h5g.reconstructSubObjects(op, {
                    "inputs": "inputs",
                    "outputs": "outputs",
                    "_origBlockShape" : "_origBlockShape",
                    "_blockShape" : "_blockShape",
                    "_blockState" : "_blockState",
                    "_dirtyState" : "_dirtyState",
                    "_dirtyShape" : "_dirtyShape",
                    "_cache" : "_cache",
                    "_lazyAlloc" : "_lazyAlloc",
                    "_cacheHits" : "_cacheHits",
                    "_fixed" : "_fixed"
                },patchBoard)

        setattr(op, "_blockQuery", numpy.ndarray(op._dirtyShape, dtype = object))

        return op


if has_blist:
    class OpSparseLabelArray(Operator):
        name = "Sparse Label Array"
        description = "simple cache for sparse label arrays"

        inputSlots = [InputSlot("Input", optional = True),
                      InputSlot("shape"),
                      InputSlot("eraser"),
                      InputSlot("deleteLabel", optional = True)]

        outputSlots = [OutputSlot("Output"),
                       OutputSlot("nonzeroValues"),
                       OutputSlot("nonzeroCoordinates"),
                       OutputSlot("maxLabel")]

        def __init__(self, *args, **kwargs):
            super(OpSparseLabelArray, self).__init__( *args, **kwargs )
            self.lock = threading.Lock()
            self._denseArray = None
            self._sparseNZ = None
            self._oldShape = (0,)
            self._maxLabel = 0            

        def setupOutputs(self):
            if (self._oldShape != self.inputs["shape"].value).all():
                shape = self.inputs["shape"].value
                self._oldShape = shape
                self.outputs["Output"].meta.dtype = numpy.uint8
                self.outputs["Output"].meta.shape = shape
                self.outputs["Output"].meta.axistags = vigra.defaultAxistags(len(shape))

                self.inputs["Input"].meta.shape = shape


                self.outputs["nonzeroValues"].meta.dtype = object
                self.outputs["nonzeroValues"].meta.shape = (1,)
                self.outputs["nonzeroValues"].meta.axistags = vigra.defaultAxistags(1)

                self.outputs["nonzeroCoordinates"].meta.dtype = object
                self.outputs["nonzeroCoordinates"].meta.shape = (1,)
                self.outputs["nonzeroCoordinates"].meta.axistags = vigra.defaultAxistags(1)

                self._denseArray = numpy.zeros(shape, numpy.uint8)
                self._sparseNZ =  blist.sorteddict()

            if self.inputs["deleteLabel"].ready() and self.inputs["deleteLabel"].value != -1:
                labelNr = self.inputs["deleteLabel"].value

                neutralElement = 0
                self.inputs["deleteLabel"].setValue(-1) #reset state of inputslot
                self.lock.acquire()

                # Find the entries to remove
                updateNZ = numpy.nonzero(numpy.where(self._denseArray == labelNr,1,0))
                if len(updateNZ)>0:
                    # Convert to 1-D indexes for the raveled version
                    updateNZRavel = numpy.ravel_multi_index(updateNZ, self._denseArray.shape)                                        
                    # Zero out the entries we don't want any more
                    self._denseArray.ravel()[updateNZRavel] = neutralElement
                    # Remove the zeros from the sparse list
                    for index in updateNZRavel:
                        self._sparseNZ.pop(index)
                # Labels are continuous values: Shift all higher label values down by 1.
                self._denseArray[:] = numpy.where(self._denseArray > labelNr, self._denseArray - 1, self._denseArray)
                self._maxLabel = self._denseArray.max()
                self.lock.release()
                self.outputs["nonzeroValues"].setDirty(slice(None))
                self.outputs["nonzeroCoordinates"].setDirty(slice(None))
                self.outputs["Output"].setDirty(slice(None))
                self.outputs["maxLabel"].setValue(self._maxLabel)

        def getOutSlot(self, slot, key, result):
            self.lock.acquire()
            assert(self.inputs["eraser"].ready() == True and self.inputs["shape"].ready() == True), "OpDenseSparseArray:  One of the neccessary input slots is not ready: shape: %r, eraser: %r" % (self.inputs["eraser"].ready(), self.inputs["shape"].ready())
            if slot.name == "Output":
                result[:] = self._denseArray[key]
            elif slot.name == "nonzeroValues":
                result[0] = numpy.array(self._sparseNZ.values())
            elif slot.name == "nonzeroCoordinates":
                result[0] = numpy.array(self._sparseNZ.keys())
            elif slot.name == "maxLabel":
                result[0] = self._maxLabel
            self.lock.release()
            return result

        def setInSlot(self, slot, key, value):
            assert value.dtype == self._denseArray.dtype, "Labels must be {}".format(self._denseArray.dtype)
            assert isinstance(value, numpy.ndarray)            
            if type(value) != numpy.ndarray:
                # vigra.VigraArray doesn't handle advanced indexing correctly,
                #   so convert to numpy.ndarray first
                value = value.view(numpy.ndarray)
            
            shape = self.inputs["shape"].value
            eraseLabel = self.inputs["eraser"].value
            neutralElement = 0

            self.lock.acquire()
            #fix slicing of single dimensions:
            start, stop = sliceToRoi(key, shape, extendSingleton = False)
            start = start.floor()
            stop = stop.floor()

            tempKey = roiToSlice(start-start, stop-start) #, hardBind = True)

            stop += numpy.where(stop-start == 0,1,0)

            key = roiToSlice(start,stop)

            updateShape = tuple(stop-start)

            update = self._denseArray[key].copy()

            update[tempKey] = value

            startRavel = numpy.ravel_multi_index(numpy.array(start, numpy.int32),shape)

            #insert values into dict
            updateNZ = numpy.nonzero(numpy.where(update != neutralElement,1,0))
            updateNZRavelSmall = numpy.ravel_multi_index(updateNZ, updateShape)

            if isinstance(value, numpy.ndarray):
                valuesNZ = value.ravel()[updateNZRavelSmall]
            else:
                valuesNZ = value

            updateNZRavel = numpy.ravel_multi_index(updateNZ, shape)
            updateNZRavel += startRavel

            self._denseArray.ravel()[updateNZRavel] = valuesNZ

            valuesNZ = self._denseArray.ravel()[updateNZRavel]

            self._denseArray.ravel()[updateNZRavel] =  valuesNZ

            td = blist.sorteddict(zip(updateNZRavel.tolist(),valuesNZ.tolist()))

            self._sparseNZ.update(td)

            #remove values to be deleted
            updateNZ = numpy.nonzero(numpy.where(update == eraseLabel,1,0))
            if len(updateNZ)>0:
                updateNZRavel = numpy.ravel_multi_index(updateNZ, shape)
                updateNZRavel += startRavel
                self._denseArray.ravel()[updateNZRavel] = neutralElement
                for index in updateNZRavel:
                    self._sparseNZ.pop(index)

            # Update our maxlabel
            self._maxLabel = self._denseArray.max()

            self.lock.release()

            # Set our max label dirty if necessary
            self.outputs["maxLabel"].setValue(self._maxLabel)
            self.outputs["Output"].setDirty(key)
        
        def propagateDirty(self, inputSlot, roi):
            if inputSlot == self.Input:
                self.Output.setDirty(roi)
            else:
                # All other inputs are single-value inputs that will trigger
                #  a new call to setupOutputs, which already sets the outputs dirty.
                # (See above.) 
                pass


    class OpBlockedSparseLabelArray(Operator):
        name = "Blocked Sparse Label Array"
        description = "simple cache for sparse label arrays"

        inputSlots = [InputSlot("Input", optional = True),
                      InputSlot("shape"),
                      InputSlot("eraser"),
                      InputSlot("deleteLabel", optional = True),
                      InputSlot("blockShape")]

        outputSlots = [OutputSlot("Output"),
                       OutputSlot("nonzeroValues"),
                       OutputSlot("nonzeroCoordinates"),
                       OutputSlot("nonzeroBlocks"),
                       OutputSlot("maxLabel")]

        loggerName = __name__ + ".OpBlockedSparseLabelArray"
        logger = logging.getLogger(loggerName)
        traceLogger = logging.getLogger("TRACE." + loggerName)

        def __init__(self, *args, **kwargs):
            with Tracer(self.traceLogger):
                super(OpBlockedSparseLabelArray, self).__init__( *args, **kwargs )
                self.lock = threading.Lock()
    
                self._sparseNZ = None
                self._labelers = {}
                self._oldMaxLabels = {}
                self._cacheShape = None
                self._cacheEraser = None
                self._maxLabel = 0
                self._maxLabelHistogram = numpy.zeros((1024,), numpy.uint32) # keeps track of how many sub- OpSparseLabelArrays vote for a vertain maxLabel
                self.deleteLabel.setValue(-1)
    
        def setupOutputs(self):
            with Tracer(self.traceLogger):
                if self.inputs["shape"].ready():
                    self._cacheShape = self.inputs["shape"].value
    
                    # FIXME: This is a super-special case because we are changing an INPUT shape from within setupOutputs!
                    if self.inputs["Input"].meta.shape != self._cacheShape:
                        self.inputs["Input"].meta.shape = self._cacheShape
                        # If we're wrapped, then we have to propagate this shape change BACKWARDS.
                        if self.inputs['Input'].partner is not None:
                            self.inputs['Input'].partner.meta.shape = self._cacheShape
                        #self.inputs["Input"]._changed()
    
                    self.outputs["Output"].meta.dtype = numpy.uint8
                    self.outputs["Output"].meta.shape = self._cacheShape
                    self.outputs["Output"].meta.axistags = vigra.defaultAxistags(len(self._cacheShape)) # Default if no input tags
    
                    # Copy axis tags from input if possible
                    inputAxisTags = self.inputs["Input"].meta.axistags
                    if inputAxisTags is not None:
                        self.outputs["Output"].meta.axistags = copy.copy(inputAxisTags)
    
                    self.outputs["nonzeroValues"].meta.dtype = object
                    self.outputs["nonzeroValues"].meta.shape = (1,)
                    self.outputs["nonzeroValues"].meta.axistags = vigra.defaultAxistags(1)
    
                    self.outputs["nonzeroCoordinates"].meta.dtype = object
                    self.outputs["nonzeroCoordinates"].meta.shape = (1,)
                    self.outputs["nonzeroCoordinates"].meta.axistags = vigra.defaultAxistags(1)
    
                    self.outputs["nonzeroBlocks"].meta.dtype = object
                    self.outputs["nonzeroBlocks"].meta.shape = (1,)
                    self.outputs["nonzeroBlocks"].meta.axistags = vigra.defaultAxistags(1)
    
                    self.outputs["maxLabel"].setValue(0)
    
                    #Filled on request
                    self._sparseNZ =  blist.sorteddict()
    
                if self.inputs["eraser"].ready():
                    self._cacheEraser = self.inputs["eraser"].value
                    for l in self._labelers.values():
                        l.inputs['eraser'].setValue(self._cacheEraser)
    
                if self.inputs["blockShape"].ready():
                    self._origBlockShape = self.inputs["blockShape"].value
    
                    if type(self._origBlockShape) != tuple:
                        self._blockShape = (self._origBlockShape,)*len(self._cacheShape)
                    else:
                        self._blockShape = self._origBlockShape
    
                    self._blockShape = numpy.minimum(self._blockShape, self._cacheShape)
    
                    self._dirtyShape = numpy.ceil(1.0 * numpy.array(self._cacheShape) / numpy.array(self._blockShape))
    
                    if lazyflow.verboseMemory:
                        print "Reconfigured Sparse labels with ", self._cacheShape, self._blockShape, self._dirtyShape, self._origBlockShape
                    #FIXME: we don't really need this blockState thing
                    self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)
    
                    _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
                    _blockNumbers.shape = self._dirtyShape
    
                    _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
                    _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)
    
    
                    self._blockNumbers = _blockNumbers
                    #self._blockIndices = _blockIndices
    
                    # allocate queryArray object
                    self._flatBlockIndices =  _blockIndices[:]
                    self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)


                if self.inputs["deleteLabel"].ready():
                    for l in self._labelers.values():
                        l.inputs["deleteLabel"].setValue(self.inputs['deleteLabel'].value)

        def execute(self, slot, roi, result):
            with Tracer(self.traceLogger):
                key = roi.toSlice()
                self.lock.acquire()
                assert(self.inputs["eraser"].ready() == True and self.inputs["shape"].ready() == True and self.inputs["blockShape"].ready()==True), \
                "OpBlockedSparseLabelArray:  One of the neccessary input slots is not ready: shape: %r, eraser: %r" % \
                (self.inputs["eraser"].ready(), self.inputs["shape"].ready())
                if slot.name == "Output":
                        #result[:] = self._denseArray[key]
                        #find the block key
                    start, stop = sliceToRoi(key, self._cacheShape)
                    blockStart = (1.0 * start / self._blockShape).floor()
                    blockStop = (1.0 * stop / self._blockShape).ceil()
                    blockKey = roiToSlice(blockStart,blockStop)
                    innerBlocks = self._blockNumbers[blockKey]
                    if lazyflow.verboseRequests:
                        print "OpBlockedSparseLabelArray %r: request with key %r for %d inner Blocks " % (self,key, len(innerBlocks.ravel()))
                    for b_ind in innerBlocks.ravel():
                        #which part of the original key does this block fill?
                        offset = self._blockShape*self._flatBlockIndices[b_ind]
                        bigstart = numpy.maximum(offset, start)
                        bigstop = numpy.minimum(offset + self._blockShape, stop)
    
                        smallstart = bigstart-offset
                        smallstop = bigstop - offset
    
                        bigkey = roiToSlice(bigstart-start, bigstop-start)
                        smallkey = roiToSlice(smallstart, smallstop)
                        if not b_ind in self._labelers or not self._labelers[b_ind].Output.ready():
                            result[bigkey]=0
                        else:
                            try:
                                labeler = self._labelers[b_ind]
                                denseArray = labeler._denseArray[smallkey]
                                result[bigkey]= denseArray
                            except:
                                print "Exception in OpBlockedSparseLabelArray.execute, probably due to simultaneous calls to setInSlot() and execute()"
                                print "labeler =", labeler
                                print "denseArray =", denseArray
                                print "result =", result
                                raise
    
                elif slot.name == "nonzeroValues":
                    nzvalues = set()
                    for l in self._labelers.values():
                        nzvalues |= set(l._sparseNZ.values())
                    result[0] = numpy.array(list(nzvalues))
    
                elif slot.name == "nonzeroCoordinates":
                    print "not supported yet"
                    #result[0] = numpy.array(self._sparseNZ.keys())
                elif slot.name == "nonzeroBlocks":
                    #we only return all non-zero blocks, no keys
                    slicelist = []
                    for b_ind in self._labelers.keys():
                        offset = self._blockShape*self._flatBlockIndices[b_ind]
                        bigstart = offset
                        bigstop = numpy.minimum(offset + self._blockShape, self._cacheShape)
                        bigkey = roiToSlice(bigstart, bigstop)
                        slicelist.append(bigkey)
    
                    result[0] = slicelist
                elif slot.name == "maxLabel":
                    result[0] = self._maxLabel
    
                self.lock.release()
                return result

        def setInSlot(self, slot, key, value):
            with Tracer(self.traceLogger):
                time1 = time.time()

                logger.info("OpBlockedSparseLabelArray")
                start, stop = sliceToRoi(key, self._cacheShape)
    
                blockStart = (1.0 * start / self._blockShape).floor()
                blockStop = (1.0 * stop / self._blockShape).ceil()
                blockStop = numpy.where(stop == self._cacheShape, self._dirtyShape, blockStop)
                blockKey = roiToSlice(blockStart,blockStop)
                innerBlocks = self._blockNumbers[blockKey]
                for b_ind in innerBlocks.ravel():
    
                    offset = self._blockShape*self._flatBlockIndices[b_ind]
                    bigstart = numpy.maximum(offset, start)
                    bigstop = numpy.minimum(offset + self._blockShape, stop)
                    smallstart = bigstart-offset
                    smallstop = bigstop - offset
                    bigkey = roiToSlice(bigstart-start, bigstop-start)
                    smallkey = roiToSlice(smallstart, smallstop)
                    smallvalues = value[tuple(bigkey)]
                    if (smallvalues != 0 ).any():
                        if not b_ind in self._labelers:
                            self._labelers[b_ind]=OpSparseLabelArray(self)
                            # Don't connect deletelabel; it is set manually (here and also above)
                            self._labelers[b_ind].inputs["deleteLabel"].setValue(self.inputs["deleteLabel"].value)
                            self._labelers[b_ind].inputs["shape"].setValue(self._blockShape)
                            self._labelers[b_ind].inputs["eraser"].connect(self.inputs["eraser"])

                            # remember old max labele, i.e. 0 since we just created
                            self._oldMaxLabels[b_ind] = 0
                            # add the 0 to the histogram
                            self._maxLabelHistogram[0] += 1
                            
                            def max_label_changed(b_ind, slot, *args):
                                self.lock.acquire()

                                newmax = slot.value

                                # make sure histogram is large enough
                                if newmax > self._maxLabelHistogram.shape[0] -1:
                                    self._maxLabelHistogram.resize((newmax+1,))

                                # update histogram
                                oldmax = self._oldMaxLabels[b_ind]
                                self._maxLabelHistogram[oldmax] -= 1
                                self._maxLabelHistogram[newmax] += 1
                                self._oldMaxLabels[b_ind] = newmax
                                
                                # check wether self._maxlabel needs to be updated (up and down)
                                maxdirty = False
                                if newmax > self._maxLabel:
                                    assert self._maxLabelHistogram[newmax] == 1
                                    self._maxLabel = newmax
                                elif self._maxLabelHistogram[oldmax] == 0:
                                    self._maxLabel = numpy.max(numpy.nonzero(self._maxLabelHistogram)[0])

                                self.lock.release()
                                
                                self.maxLabel.setValue(self._maxLabel)


                             
                            self._labelers[b_ind].inputs["maxLabel"].notifyDirty(partial(max_label_changed, b_ind))
                            
                        self._labelers[b_ind].inputs["Input"][smallkey] = smallvalues
                
                time2 = time.time()
                logger.info("OpBlockedSparseLabelArray: setInSlot writing took %fs" % (time2-time1,))
                # Set our max label output dirty

                self.Output.setDirty(key)

                time3 = time.time()
                logger.info("OpBlockedSparseLabelArray: setInSlot setDirty took %fs" % (time3-time2,))
                logger.info("OpBlockedSparseLabelArray: setInSlot total took %fs" % (time3-time1,))

        def notifyDirty(self, slot, key):
            with Tracer(self.traceLogger):
                if slot == self.inputs["Input"]:
                    self.Output.setDirty(key)

class OpBlockedArrayCache(Operator):
    name = "OpBlockedArrayCache"
    description = ""

    inputSlots = [InputSlot("Input"),InputSlot("innerBlockShape"), InputSlot("outerBlockShape"), InputSlot("fixAtCurrent")]
    outputSlots = [OutputSlot("Output")]

    loggerName = __name__ + ".OpBlockedArrayCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
        with Tracer(self.traceLogger):
            super(OpBlockedArrayCache, self).__init__( *args, **kwargs )
            self._configured = False
            self.source = OpArrayPiper(self)
            self.source.inputs["Input"].connect(self.inputs["Input"])
            self._fixed = False
            self._fixed_dirty_blocks = set()
            self._lock = Lock()
            self._innerBlockShape = None
            self._outerBlockShape = None
            self._blockShape = None
            self._fixed_all_dirty = False  # this is a shortcut for storing wehter all subblocks are dirty

    def setupOutputs(self):
        with Tracer(self.traceLogger):
            self._fixed = self.inputs["fixAtCurrent"].value
    
            inputSlot = self.inputs["Input"]
            shape = inputSlot.meta.shape
            if (    shape != self.Output.meta.shape
                 or self._outerBlockShape != self.outerBlockShape.value
                 or self._innerBlockShape != self.innerBlockShape.value ):
                self._configured = False
                
            if min(shape) == 0:
                # FIXME: This is evil, but there's no convenient way around it.
                # We don't want our output to be flagged as 'ready'
                # The only way to do that is to temporarily connect it to an unready operator
                opTmp = OpArrayPiper(graph=self.graph)
                opTmp.Output.connect( self.Output )
                self._configured = False
                return
            else:
                if self.Output.partner is not None:
                    self.Output.disconnect()
    
            if not self._configured:
                self.Output.meta.assignFrom(inputSlot.meta)
                with self._lock:
                    self._innerBlockShape = self.innerBlockShape.value
                    self._outerBlockShape = self.outerBlockShape.value
                    if len(self._fixed_dirty_blocks) > 0:
                        self._fixed_dirty_blocks = set()
                        notifyOutputDirty = True # Notify dirty output after we're fully configured
                    else:
                        notifyOutputDirty = False
    
                    self.shape = self.Input.meta.shape
                    self._blockShape = self.inputs["outerBlockShape"].value
                    self._blockShape = tuple(numpy.minimum(self._blockShape, self.shape))
                    assert numpy.array(self._blockShape).min() > 0, "ERROR in OpBlockedArrayCache: invalid blockShape = {blockShape}".format(blockShape=self._blockShape)
                    self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
                    assert numpy.array(self._dirtyShape).min() > 0, "ERROR in OpBlockedArrayCache: invalid dirtyShape = {dirtyShape}".format(dirtyShape=self._dirtyShape)

                    self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)

                _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
                _blockNumbers.shape = self._dirtyShape

                _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
                _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)

                self._blockNumbers = _blockNumbers

                # allocate queryArray object
                self._flatBlockIndices =  _blockIndices[:]
                self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)

                self._opSub_list = {}
                self._cache_list = {}


                self._configured = True

                if notifyOutputDirty:
                    self.Output.setDirty(slice(None))

    def execute(self, slot, roi, result):
        with Tracer(self.traceLogger, msg='roi={}'.format(roi)):
            if not self._configured:
                # this happends when the operator is not yet fully configured due to fixAtCurrent == True
                result[:] = 0
                return
    
            #find the block key
            key = roi.toSlice()
            start, stop = roi.start, roi.stop
    
            blockStart = (start / self._blockShape)
            blockStop = (stop * 1.0 / self._blockShape).ceil()
            #blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
            blockKey = roiToSlice(blockStart,blockStop)
            innerBlocks = self._blockNumbers[blockKey]
    
            if lazyflow.verboseRequests:
                print "OpSparseArrayCache %r: request with key %r for %d inner Blocks " % (self,key, len(innerBlocks.ravel()))
    
    
            requests = []
            for b_ind in innerBlocks.flat:
                #which part of the original key does this block fill?
                offset = self._blockShape*self._flatBlockIndices[b_ind]
                bigstart = numpy.maximum(offset, start)
                bigstop = numpy.minimum(offset + self._blockShape, stop)
    
    
                smallstart = bigstart-offset
                smallstop = bigstop - offset
    
                diff = smallstop - smallstart
                smallkey = roiToSlice(smallstart, smallstop)
    
                bigkey = roiToSlice(bigstart-start, bigstop-start)

                with self._lock:    
                    if not self._fixed:
                        if not self._cache_list.has_key(b_ind):

                            self._opSub_list[b_ind] = generic.OpSubRegion(self)
                            self._opSub_list[b_ind].inputs["Input"].connect(self.inputs["Input"])#source.outputs["Output"])
                            tstart = self._blockShape*self._flatBlockIndices[b_ind]
                            tstop = numpy.minimum((self._flatBlockIndices[b_ind]+numpy.ones(self._flatBlockIndices[b_ind].shape, numpy.uint8))*self._blockShape, self.shape)
        
                            self._opSub_list[b_ind].inputs["Start"].setValue(tuple(tstart))
                            self._opSub_list[b_ind].inputs["Stop"].setValue(tuple(tstop))
        
                            self._cache_list[b_ind] = OpArrayCache(self)
                            self._cache_list[b_ind].inputs["Input"].connect(self._opSub_list[b_ind].outputs["Output"])
                            self._cache_list[b_ind].inputs["fixAtCurrent"].connect( self.fixAtCurrent )
                            self._cache_list[b_ind].inputs["blockShape"].setValue(self.inputs["innerBlockShape"].value)
                            # we dont register a callback for dirtyness, since we already forward the signal

                if self._cache_list.has_key(b_ind):
                    op = self._cache_list[b_ind]
                    #req = self._cache_list[b_ind].outputs["Output"][smallkey].writeInto(result[bigkey])
    
                    smallroi = SubRegion(op.outputs["Output"], start = smallstart , stop= smallstop)
                    op.execute(op.outputs["Output"],smallroi,result[bigkey])
    
                    ####op.getOutSlot(op.outputs["Output"],smallkey,result[bigkey])
                    #requests.append(req)
                else:
                    #When this block has never been in the cache and the current
                    #value is fixed (fixAtCurrent=True), return 0  values
                    #This prevents random noise appearing in such cases.
                    result[bigkey] = 0
                    with self._lock:
                        # Since a downstream operator has expressed an interest in this block,
                        #  mark it to be signaled as dirty when we become unfixed.
                        # Otherwise, downstream operators won't know when there's valid data in this block.
                        self._fixed_dirty_blocks.add(b_ind)
    
            for r in requests:
                r.wait()


    def notifyDirty(self, slot, key):
        with Tracer(self.traceLogger):
            if slot == self.inputs["Input"]:
                if not self._fixed:
                    self.outputs["Output"].setDirty(key)                    
                elif self._blockShape is not None:
                    # Find the block key
                    roi = SubRegion(slot, pslice=key)
                    start, stop = roi.start, roi.stop
            
                    blockStart = (start / self._blockShape)
                    blockStop = (stop * 1.0 / self._blockShape).ceil()
                    
                    with self._lock:
                        # check wether the dirty region encompasses the whole cache
                        if (blockStart == 0).all() and (blockStop == self._blockNumbers.shape).all():
                            self._fixed_all_dirty = True

                        # shortcut, if everything is dirty already, dont loop over the blocks
                        if self._fixed_all_dirty is False:
                            blockKey = roiToSlice(blockStart,blockStop)
                            innerBlocks = self._blockNumbers[blockKey]
                            for b_ind in innerBlocks.flat:
                                self._fixed_dirty_blocks.add(b_ind)            

            if slot == self.fixAtCurrent:
                self._fixed = self.fixAtCurrent.value
                if not self._fixed:
                    # We've become unfixed.
                    # Take the superset of all the blocks that became dirty in the meantime and notify our output
                    dirtystart, dirtystop = (None,None)
                    with self._lock:
                        if self._fixed_all_dirty is True:
                            dirtystop = self.Output.meta.shape
                            dirtystart = [0] * len(self.Output.meta.shape)
                        elif len(self._fixed_dirty_blocks) > 0:
                            dirtystart = self.Output.meta.shape
                            dirtystop = [0] * len(self.Output.meta.shape)
                            for b_ind in self._fixed_dirty_blocks:
                                offset = self._blockShape*self._flatBlockIndices[b_ind]
                                bigstart = offset
                                bigstop = numpy.minimum(offset + self._blockShape, self.Output.meta.shape)
                                
                                dirtystart = numpy.minimum(bigstart, dirtystart)
                                dirtystop = numpy.maximum(bigstop, dirtystop)
                            
                            self._fixed_dirty_blocks = set()
                        # reset all dirty state to false
                        self._fixed_all_dirty = False 

                    if dirtystart is not None:
                        self.Output.setDirty(dirtystart, dirtystop)

    def setInSlot(self,slot,key):
        pass




class OpSlicedBlockedArrayCache(Operator):
    name = "OpSlicedBlockedArrayCache"
    description = ""

    Input = InputSlot()

    inputSlots = [InputSlot("innerBlockShape"), InputSlot("outerBlockShape"), InputSlot("fixAtCurrent", value = False)]
    outputSlots = [OutputSlot("Output"), MultiOutputSlot("InnerOutputs")]

    loggerName = __name__ + ".OpSlicedBlockedArrayCache"
    logger = logging.getLogger(loggerName)
    traceLogger = logging.getLogger("TRACE." + loggerName)

    def __init__(self, *args, **kwargs):
        with Tracer(self.traceLogger):
            super(OpSlicedBlockedArrayCache, self).__init__(*args, **kwargs)
            self._innerOps = []

    def setupOutputs(self):
        self.shape = self.inputs["Input"].shape
        self._outerShapes = self.inputs["outerBlockShape"].value
        self._innerShapes = self.inputs["innerBlockShape"].value

        if len(self._innerShapes) != len(self._innerOps):
            for o in self._innerOps:
                o.disconnect()

            self._innerOps = []

            for i,innershape in enumerate(self._innerShapes):
                op = OpBlockedArrayCache(self)
                op.inputs["fixAtCurrent"].connect(self.inputs["fixAtCurrent"])
                op.inputs["Input"].connect(self.inputs["Input"])
                self._innerOps.append(op)
                
                # Forward dirty propagations only from one blocked cache to our Output
                if i == 0:
                    def handleDirty( slot, roi ):
                        self.Output.setDirty( roi.start, roi.stop )
                    op.Output.notifyDirty( handleDirty )

        for i,innershape in enumerate(self._innerShapes):
            op = self._innerOps[i]
            op.inputs["innerBlockShape"].setValue(innershape)
            op.inputs["outerBlockShape"].setValue(self._outerShapes[i])

        self.Output.meta.assignFrom(self.Input.meta)

        # We also provide direct access to each of our inner cache outputs.        
        self.InnerOutputs.resize( len(self._innerOps) )
        for i, slot in enumerate(self.InnerOutputs):
            slot.connect(self._innerOps[i].Output)

    def execute(self, slot, roi, result):
        assert slot == self.Output
        
        key = roi.toSlice()
        start,stop=sliceToRoi(key,self.shape)
        roishape=numpy.array(stop)-numpy.array(start)

        max_dist_squared=sys.maxint
        index=0

        for i,blockshape in enumerate(self._innerShapes):
            blockshape = numpy.array(blockshape)

            diff = roishape - blockshape
            diffsquared = diff * diff
            distance_squared = numpy.sum(diffsquared)
            if distance_squared < max_dist_squared:
                index = i
                max_dist_squared = distance_squared

        op = self._innerOps[index]
        op.outputs["Output"][key].writeInto(result).wait()

    def notifyDirty(self, slot, key):
        # Dirtiness is automatically forwarded from one of our inner operators to our output.
        pass







































