import numpy

from graph import Operator, InputSlot, OutputSlot
from roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque

class OpArrayPiper(Operator):
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnect(self, inputSlot):
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._axistags = inputSlot.axistags

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype        

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




#"""
#distributed blocks
#request all touched blocks in full
#"""
#def cachingFullBlockQuery(graph, input, result, start, stop, shape, blockShape, dirtyIndices, dirtyArray, dirtyState, cache):
#    dirtyStart = numpy.floor(1.0 * start / blockShape)
#    dirtyStop = numpy.ceil(1.0 * stop / blockShape)
#    dirtyKey = roiToSlice(dirtyStart,dirtyStop)
#            
#    blockInd =  dirtyIndices[dirtyKey]
#    blockInd = blockInd.reshape(blockInd.size/blockInd.shape[-1],blockInd.shape[-1],)
#
#    #start the queries for the parts
#    queries = []
#    inWorkQueries =  deque()
#    print "in the beginning", len(inWorkQueries)
#    for p in blockInd:
#        acc = tuple(p)
#        dirtyness = dirtyArray[acc]
#        if  dirtyness!= dirtyState and dirtyness != 0:
#            #indicate the work in progress
#            print "working on", input.operator.name, p, dirtyness            
#            globStart = p * blockShape
#            globStop = (p+1) * blockShape
#
#            #globStart = numpy.maximum(globStart,start)
#            globStop = numpy.minimum(globStop,numpy.array(shape))
#                            
#            locStart = numpy.mod(globStart, blockShape)
#            locStop = numpy.mod(globStop - 1, blockShape) + 1
#            
#            view = cache[acc][roiToSlice(locStart, locStop)]
#            #assert (locStop - locStart == globStop -globStart).all(), "%r, %r, %r, %r " % (locStart, locStop, globStart, globStop)
#            
#            queries.append((view,globStart,globStop,p))
#        elif dirtyness == dirtyState:
#            globStart = p * blockShape
#            globStop = (p+1) * blockShape
#            
#            globStart = numpy.maximum(globStart,start)
#            globStop = numpy.minimum(globStop,stop)
#            
#            locStart = numpy.mod(globStart, blockShape)
#            locStop = numpy.mod(globStop - 1, blockShape) + 1
#            
#            result[roiToSlice(globStart-start,globStop-start)] = cache[acc][roiToSlice(locStart, locStop)]
#        elif dirtyness == 0: #e.g. the block is in work
#            print "already in work?", input.operator.name, p, dirtyness
#            globStart = p * blockShape
#            globStop = (p+1) * blockShape
#            
#            #globStart = numpy.maximum(globStart,start)
#            globStop = numpy.minimum(globStop,numpy.array(shape))
#            
#            inWorkQueries.append((globStart,globStop,p))
#
#            
#    tasks = graph.tasks
#    while len(inWorkQueries) > 0:
#        q = inWorkQueries.popleft()
#        
#        globStart, globStop,p = q
#
#        globStart = numpy.maximum(globStart,start)
#        globStop = numpy.minimum(globStop,stop)
#        
#        locStart = numpy.mod(globStart, blockShape)
#        locStop = numpy.mod(globStop - 1, blockShape) + 1
#
#        acc = tuple(p)
#        while dirtyArray[acc] != dirtyState:
#            try:
#                task = tasks.get(False)
#            except Empty:
#                # task queue empty, e.g. our
#                # result is being calculated by some worker
#                # -> just wait for the result after loop
#                break
#            #            try:
#            # doe something useful while waiting for result, e.g.
#            # calculate an store result of some task
#            task[0](task[1]) 
#            # set event, thus indicating result is ready
#            task[3].set()
#        if dirtyArray[acc] == dirtyState:
#            "yeah, finished one",p
#            result[roiToSlice(globStart - start, globStop - start)] = cache[acc][roiToSlice(locStart, locStop)]
#        else:
#            print "Tasks: ", tasks.qsize(), "len(inWorkQueries)",len(inWorkQueries)
#            inWorkQueries.append(q)
#
#    queries2 = []
#    for q in queries:
#        view, globStart, globStop,p = q
#        dirtyArray[tuple(p)] = 0
#        v = input[roiToSlice(globStart,globStop),view]
#        queries2.append((v,view, globStart, globStop,p))
#    for q in queries2:
#        v, view, globStart, globStop,p = q
#        v()
#        dirtyArray[tuple(p)] = dirtyState
#        
#        globStart = numpy.maximum(globStart,start)
#        globStop = numpy.minimum(globStop,stop)
#        
#        locStart = numpy.mod(globStart, blockShape)
#        locStop = numpy.mod(globStop - 1, blockShape) + 1
#        
#        resStart = globStart - start
#        resStop = globStop - start
#                
#        result[roiToSlice(resStart,resStop)] = view[roiToSlice(locStart, locStop)]

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
    v = input[roiToSlice(globStart,globStop),view]
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
                    
    
    def getOutSlot(self,slot,key,result):
        start, stop = sliceToRoi(key, self.shape)
        
        cachingBlockQuery2(self.inputs["Input"], result, start, stop, self.shape, self._blockShape, self._dirtyIndices, self._dirtyArray, self._dirtyState, self._cache)
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
           
        