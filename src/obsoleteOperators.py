import numpy

from graph import Operator, InputSlot, OutputSlot
from roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque
import greenlet, threading
import vigra
from operators import OpArrayPiper

"""
distributed blocks
request really only the requested pixels
"""
def cachingBlockQuery(input, result, start, stop, shape, blockShape, dirtyIndices, dirtyArray, dirtyState, cache):
    dirtyStart = numpy.floor(1.0 * start / blockShape)
    dirtyStop = numpy.ceil(1.0 * stop / blockShape)
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
            
    blockInd =  dirtyIndices[dirtyKey]
    blockInd = blockInd.reshape(blockInd.size/blockInd.shape[-1],blockInd.shape[-1],)

    #start the queries for the parts
    queries = []
    for p in blockInd:
        acc = tuple(p)
        if dirtyArray[acc] != dirtyState:
            globStart = p * blockShape
            globStop = (p+1) * blockShape

            globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,stop)
                            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            
            view = cache[tuple(p)][roiToSlice(locStart, locStop)]
            #assert (locStop - locStart == globStop -globStart).all(), "%r, %r, %r, %r " % (locStart, locStop, globStart, globStop)
            v = input[roiToSlice(globStart,globStop),view]
            queries.append((v,view,globStart,globStop))
        else:
            globStart = p * blockShape
            globStop = (p+1) * blockShape
            
            globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,stop)
            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            
            result[roiToSlice(globStart-start,globStop-start)] = cache[tuple(p)][roiToSlice(locStart, locStop)]

    for q in queries:
        v, view,globStart, globStop = q
        v()
        resStart = globStart - start
        resStop = globStop - start
        result[roiToSlice(resStart,resStop)] = view[:]
        
    # update _dirtyArray
    dirtyStart = numpy.ceil(1.0 * start / blockShape)
    stop = numpy.where(stop == shape, stop + blockShape, stop)
    dirtyStop = numpy.floor(1.0 * stop / blockShape)
    
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
    dirtyArray[dirtyKey] = dirtyState

"""
distributed blocks
request complete blocks
"""
def cachingBlockQuery2(input, result, start, stop, shape, blockShape, dirtyIndices, dirtyArray, dirtyState, cache):
    dirtyStart = numpy.floor(1.0 * start / blockShape)
    dirtyStop = numpy.ceil(1.0 * stop / blockShape)
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
            
    blockInd =  dirtyIndices[dirtyKey]
    blockInd = blockInd.reshape(blockInd.size/blockInd.shape[-1],blockInd.shape[-1],)

    #start the queries for the parts
    queries = []
    for p in blockInd:
        acc = tuple(p)
        if dirtyArray[acc] != dirtyState:
            globStart = p * blockShape
            globStop = (p+1) * blockShape

            #globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,shape)
                            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            
            view = cache[tuple(p)][roiToSlice(locStart, locStop)]
            #assert (locStop - locStart == globStop -globStart).all(), "%r, %r, %r, %r " % (locStart, locStop, globStart, globStop)
            v = input[roiToSlice(globStart,globStop),view]
            queries.append((v,view,globStart,globStop, acc))
        else:
            globStart = p * blockShape
            globStop = (p+1) * blockShape
            
            globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,stop)
            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            
            result[roiToSlice(globStart-start,globStop-start)] = cache[tuple(p)][roiToSlice(locStart, locStop)]

    for q in queries:
        v, view,globStart, globStop, acc = q
        v()
        dirtyArray[acc] = dirtyState
        globStart = numpy.maximum(globStart,start)
        globStop = numpy.minimum(globStop,stop)
        resStart = globStart - start
        resStop = globStop - start
        locStart = numpy.mod(globStart, blockShape)
        locStop = numpy.mod(globStop - 1, blockShape) + 1
        result[roiToSlice(resStart,resStop)] = cache[acc][roiToSlice(locStart, locStop)]


"""
distributed blocks
request complete blocks + wait for in processing
"""
def cachingBlockQuery3(input, result, start, stop, shape, blockShape, dirtyIndices, dirtyArray, dirtyState, cache, queryQueue):
    dirtyStart = numpy.floor(1.0 * start / blockShape)
    dirtyStop = numpy.ceil(1.0 * stop / blockShape)
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
            
    blockInd =  dirtyIndices[dirtyKey]
    blockInd = blockInd.reshape(blockInd.size/blockInd.shape[-1],blockInd.shape[-1],)

    #start the queries for the parts
    queries = []
    inprocess = []
    
    for p in blockInd:
        acc = tuple(p)
        queryDeque = queryQueue[acc]
        queryDeque.lock.acquire()
            
        if queryDeque.queue is None and dirtyArray[acc] != dirtyState:
            queryDeque.queue = deque()
            queryDeque.lock.release()
            globStart = p * blockShape
            globStop = (p+1) * blockShape

            #globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,shape)
                            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            
            view = cache[tuple(p)][roiToSlice(locStart, locStop)]
            #assert (locStop - locStart == globStop -globStart).all(), "%r, %r, %r, %r " % (locStart, locStop, globStart, globStop)

            def customClosure():
                #dirtyArray[acc] = dirtyState
                #queryQueue[acc] = None
                pass
                        
            v = input[roiToSlice(globStart,globStop)].writeInto(view)
            queries.append((v,view,globStart,globStop, acc))
        else:
            queryDeque.lock.release()
            globStart = p * blockShape
            globStop = (p+1) * blockShape
            
            globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,stop)
            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            inprocess.append((p,acc,globStart,globStop,locStart,locStop))
            #result[roiToSlice(globStart-start,globStop-start)] = cache[tuple(p)][roiToSlice(locStart, locStop)]
        
    for q in queries:
        v, view,globStart, globStop, acc= q
        v()
        dirtyArray[acc] = dirtyState
        queryDeque = queryQueue[acc]
        globStart = numpy.maximum(globStart,start)
        globStop = numpy.minimum(globStop,stop)
        resStart = globStart - start
        resStop = globStop - start
        locStart = numpy.mod(globStart, blockShape)
        locStop = numpy.mod(globStop - 1, blockShape) + 1
        result[roiToSlice(resStart,resStop)] = cache[acc][roiToSlice(locStart, locStop)]
        queryDeque.lock.acquire()
        queue = queryDeque.queue
        for w in queue:
            #[None, gr,event,thread]
            w[3].pendingGreenlets.append(w)
        queryDeque.queue = None
        queryDeque.lock.release()

    while len(inprocess)>0:
        q = inprocess.pop()
        p,acc,globStart,globStop,locStart,locStop= q
        temp = numpy.ndarray((1,), dtype = object)
        temp[0] = greenlet.getcurrent()
        task = [None, temp, threading.Event(),threading.current_thread()]
        if dirtyArray[acc] != dirtyState:
            queryDeque = queryQueue[acc]
            queryDeque.lock.acquire()
            queue = queryDeque.queue
            if queue is not None:
                queue.append(task)
                queryDeque.lock.release()
                greenlet.getcurrent().parent.switch(None)
            else:
                queryDeque.lock.release()
        result[roiToSlice(globStart-start,globStop-start)] = cache[acc][roiToSlice(locStart, locStop)]
"""
shared memory
request dirty blocks
"""
def dirtyBoxesQuery(input, result, start, stop, shape, blockShape, dirtyIndices, dirtyArray, dirtyState, cache):
    dirtyStart = numpy.floor(1.0 * start / blockShape)
    dirtyStop = numpy.ceil(1.0 * stop / blockShape)
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
            
    blockInd =  dirtyIndices[dirtyKey]
    blockInd = blockInd.reshape(blockInd.size/blockInd.shape[-1],blockInd.shape[-1],)

    #start the queries for the parts
    queries = []
    for p in blockInd:
        acc = tuple(p)
        if dirtyArray[acc] != dirtyState:
            globStart = p * blockShape
            globStop = (p+1) * blockShape

            globStart = numpy.maximum(globStart,start)
            globStop = numpy.minimum(globStop,stop)
                            
            locStart = numpy.mod(globStart, blockShape)
            locStop = numpy.mod(globStop - 1, blockShape) + 1
            
            view = cache[roiToSlice(globStart, globStop)]
            assert (locStop - locStart == globStop -globStart).all(), "%r, %r, %r, %r " % (locStart, locStop, globStart, globStop)
            v = input[roiToSlice(globStart,globStop),view]
            queries.append((v,view,globStart,globStop))

    print "Number of queries:", len(queries)
    for q in queries:
        v, view,globStart, globStop = q
        v()

    result[:] = cache[roiToSlice(start,stop)]
        
    # update _dirtyArray
    dirtyStart = numpy.ceil(1.0 * start / blockShape)
    stop = numpy.where(stop == shape, stop + blockShape, stop)
    dirtyStop = numpy.floor(1.0 * stop / blockShape)
    
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
    dirtyArray[dirtyKey] = dirtyState


"""
shared memory
request dirty blocks bounding box
"""
def dirtyBoundingBoxQuery(input, result, start, stop, shape, blockShape, dirtyIndices, dirtyArray, dirtyState, cache):
    dirtyStart = numpy.floor(1.0 * start / blockShape)
    dirtyStop = numpy.ceil(1.0 * stop / blockShape)
    dirtyKey = roiToSlice(dirtyStart,dirtyStop)

    #calculate bounding box        
    dirtyInd = numpy.nonzero(numpy.where(dirtyArray[dirtyKey] != dirtyState, 1, 0))
    for i in xrange(len(dirtyStart)):
        
        dirtyStop[i] = dirtyStart[i] + numpy.max(dirtyInd[i])
        dirtyStart[i] += numpy.min(dirtyInd[i])

    
    globStart = dirtyStart * blockShape
    globStop = (1+dirtyStop) * blockShape
    
    globStop = numpy.minimum(numpy.array(shape), globStop)
    
    view = cache[roiToSlice(globStart, globStop)]
    
    print "3", view.shape, globStart, globStop, start, stop
    v = input[roiToSlice(globStart,globStop)].writeInto(view)
    v()
    
    resStart = globStart - start
    resStop = globStop - start
    
    result[:] = cache[roiToSlice(start, stop)]

    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
    dirtyArray[dirtyKey] = dirtyState




class OpArrayBlockCache(OpArrayPiper):

    def __init__(self, graph, blockShape = None, immediateAlloc = True):
        OpArrayPiper.__init__(self, graph)
        if blockShape == None:
            blockShape = 128
        self._blockShape = blockShape
        self._immediateAlloc = immediateAlloc

    def notifyConnect(self, inputSlot):
        OpArrayPiper.notifyConnect(self, inputSlot)
        self._cache = numpy.ndarray(self.shape, dtype = object)
        
        if type(self._blockShape) != tuple:
            self._blockShape = (self._blockShape,)*len(self.shape)
            
        self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
        # if the entry in _dirtyArray differs from _dirtyState
        # the entry is considered dirty
        self._queryQueue = numpy.ndarray(self._dirtyShape, dtype=object)
        self._dirtyArray = numpy.ones(self._dirtyShape, numpy.uint8)
        _dirtyIndices = numpy.dstack(numpy.nonzero(self._dirtyArray))
        _dirtyIndices.shape = self._dirtyArray.shape + (_dirtyIndices.shape[-1],)
         
        self._dirtyIndices = _dirtyIndices
        
        self._dirtyArray[:]= 1
        self._dirtyState = 2
        
        if self._immediateAlloc:
            blockInd =  self._dirtyIndices[:]
            blockInd = blockInd.reshape(blockInd.size/blockInd.shape[-1],blockInd.shape[-1],)
            self.allocateBlocks(blockInd)
            

    def setDirty(self, inputSlot=None):
        OpArrayPiper.setDirty(self, inputSlot=inputSlot)
        self._dirtyState += 1
    
    def allocateBlocks(self, blockIndices):
        for p in blockIndices:
            acc = tuple(p)
            if self._cache[acc] is None:
                self._cache[acc] = numpy.zeros(tuple(self._blockShape), dtype=self.dtype)
                self._queryQueue[acc] = BlockQueue()
    
    def getOutSlot(self,slot,key,result):
        start, stop = sliceToRoi(key, self.shape)
        
        cachingBlockQuery3(self.inputs["Input"], result, start, stop, self.shape, self._blockShape, self._dirtyIndices, self._dirtyArray, self._dirtyState, self._cache, self._queryQueue)
        #cachingBlockQuery2(self.inputs["Input"], result, start, stop, self.shape, self._blockShape, self._dirtyIndices, self._dirtyArray, self._dirtyState, self._cache)
        #cachingFullBlockQuery(self.graph, self.inputs["Input"], result, start, stop, self.shape, self._blockShape, self._dirtyIndices, self._dirtyArray, self._dirtyState, self._cache)
    

    
    
    
    
class OpArraySliceCache(OpArrayPiper):

    def __init__(self, graph, blockShape = None):
        OpArrayPiper.__init__(self, graph)
        if blockShape == None:
            blockShape = 64
        self._blockShape = blockShape

    def notifyConnect(self, inputSlot):
        OpArrayPiper.notifyConnect(self, inputSlot)
        
        if type(self._blockShape) != tuple:
            self._blockShape = (self._blockShape,)*len(self.shape)
        
        self._cache = numpy.ndarray(self.shape, dtype = self.dtype)
        self._views = []
        self._dirtyArrays = []
        self._blockShapes = []
        self._dirtyShapes = []
        self._dirtyIndices = []
        for i in xrange(len(self.shape)):
            bs = numpy.array(self._blockShape)
            bs[i] = 1
            #self._views.append(block_view(self._cache, tuple(bs)))
            ds = numpy.ceil(1.0 * numpy.array(self.shape) / bs)
            self._dirtyShapes.append(ds)
            self._blockShapes.append(bs)
            da = numpy.ones(ds, numpy.uint8)
            self._dirtyArrays.append(da)
            di = numpy.dstack(numpy.nonzero(da))
            di.shape = da.shape + (di.shape[-1],)
            self._dirtyIndices.append(di)
            
        self._dirtyState = 2
        

            
    def setDirty(self, inputSlot=None):
        OpArrayPiper.setDirty(self, inputSlot=inputSlot)
        self._dirtyState += 1

    def getOutSlot(self,slot,key,result):
        start, stop = sliceToRoi(key, self.shape)
        dim = (stop - start).argmin()
        print "SliceCache Request: ", start, stop, "--> dim ", dim, "shape: ", self._blockShapes[dim]
        dirtyStart = start / self._blockShapes[dim]
        dirtyStop = numpy.ceil(1.0 * stop / self._blockShapes[dim])
        
        if (self._dirtyArrays[dim][roiToSlice(dirtyStart, dirtyStop)] == self._dirtyState).all():
            print "SliceCache: serving from cache..."
            result[:] =  self._cache[roiToSlice(start, stop)]
        else:
            print "SliceCache: queriying graph..."
            dirtyBoxesQuery(self.inputs["Input"], result, start, stop, self.shape, self._blockShapes[dim], self._dirtyIndices[dim], self._dirtyArrays[dim], self._dirtyState, self._cache)



class OpArraySliceCacheBounding(OpArraySliceCache):
    def getOutSlot(self,slot,key,result):
        start, stop = sliceToRoi(key, self.shape)
        dim = (stop - start).argmin()
        print "SliceCache Request: ", start, stop, "--> dim ", dim, "shape: ", self._blockShapes[dim]
        dirtyStart = start / self._blockShapes[dim]
        dirtyStop = numpy.ceil(1.0 * stop / self._blockShapes[dim])
        
        if (self._dirtyArrays[dim][roiToSlice(dirtyStart, dirtyStop)] == self._dirtyState).all():
            print "SliceCache: serving from cache..."
            result[:] =  self._cache[roiToSlice(start, stop)]
        else:
            print "SliceCache: queriying graph..."
            dirtyBoundingBoxQuery(self.inputs["Input"], result, start, stop, self.shape, self._blockShapes[dim], self._dirtyIndices[dim], self._dirtyArrays[dim], self._dirtyState, self._cache)
      
