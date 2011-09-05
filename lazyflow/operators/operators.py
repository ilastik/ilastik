import numpy

from lazyflow.graph import Operators, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view, TinyVector
from Queue import Empty
from collections import deque
from lazyflow.h5dumprestore import stringToClass
import greenlet, threading
import vigra
import copy
import gc
import weakref
from threading import current_thread, Lock
import generic
from lazyflow.graph import OperatorGroup

try:
    import blist
    has_blist = True
except:
    has_blist = False
    print "##############################################################"
    print "#                                                            #"
    print "#           please install blist (easy_install blist)        #"
    print "#           otherwise OpSparseLabelArray will be missing     #"
    print "#                                                            #"
    print "##############################################################"
    
class OpArrayPiper(Operator):
    name = "ArrayPiper"
    description = "simple piping operator"
       
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

    def getOutSlot(self, slot, key, result):
        req = self.inputs["Input"][key].writeInto(result)
        res = req.wait()
        return res

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype



class OpMultiArrayPiper(Operator):
    name = "MultiArrayPiper"
    description = "simple piping operator"
    
    inputSlots = [MultiInputSlot("MultiInput")]
    outputSlots = [MultiOutputSlot("MultiOutput")]
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["MultiInput"]
        #print "OpMultiArrayPiper notifyConnect"
        self.outputs["MultiOutput"].resize(len(inputSlot)) #clearAllSlots()
        for i,islot in enumerate(self.inputs["MultiInput"]):
            oslot = self.outputs["MultiOutput"][i]
            if islot.partner is not None:
                oslot._dtype = islot.dtype
                oslot._shape = islot.shape
                oslot._axistags = islot.axistags
    
    def notifySubConnect(self, slots, indexes):
        #print "OpMultiArrayPiper notifySubConnect"
        self.notifyConnectAll()

    def notifySubSlotRemove(self, slots, indexes):
        self.outputs["MultiOutput"].pop(indexes[0])
    
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
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["MultiInput"]
        #print "OpMultiArrayPiper notifyConnect", inputSlot
        self.outputs["MultiOutput"].resize(len(inputSlot)) #clearAllSlots()
        for i,mislot in enumerate(self.inputs["MultiInput"]):
            self.outputs["MultiOutput"][i].resize(len(mislot))
            for ii,islot in enumerate(mislot):
                oslot = self.outputs["MultiOutput"][i][ii]
                if islot.partner is not None:
                    oslot._dtype = islot.dtype
                    oslot._shape = islot.shape
                    oslot._axistags = islot.axistags
            
    def notifySubConnect(self, slots, indexes):
        #print "OpMultiArrayPiper notifySubConnect", slots, indexes
        self.notifyConnectAll()
        

    
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
    print "Error importing drtile, please use cmake to compile lazyflow.drtile !"
    import sys    
    sys.exit(1)

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
    
class OpArrayCache(OpArrayPiper):
    name = "ArrayCache"
    description = "numpy.ndarray caching class"
    category = "misc"
    
    inputSlots = [InputSlot("Input"), InputSlot("blockShape"), InputSlot("fixAtCurrent")]
    outputSlots = [OutputSlot("Output")]    
    
    def __init__(self, graph, register = True, blockShape = None, immediateAlloc = True):
        OpArrayPiper.__init__(self, graph, register = register)
        if blockShape == None:
            blockShape = 64
        self._origBlockShape = blockShape
        self._blockShape = None
        self._dirtyShape = None
        self._blockState = None
        self._dirtyState = None
        self._fixed = False
        self._cache = None
        self._lock = Lock()
        self._cacheLock = Lock()
        self._lazyAlloc = True
        self._cacheHits = 0
        self.graph._registerCache(self)
        
    def _memorySize(self):
        if self._cache is not None:
            return self._cache.nbytes        
        else:
            return 0

    def _freeMemory(self):
        self._cacheLock.acquire()
        freed  = self._memorySize() 
        if self._cache is not None: 
            fshape = self._cache.shape
            try:
                self._cache.resize((1,))
            except ValueError:
                freed = 0
                print "OpArrayCache: freeing failed due to view references"
            if freed > 0:
                print "OpArrayCache: freed cache of shape", fshape
                #gc.collect()
                #referrers = gc.get_referrers(self._cache)
                #for r in referrers:
                #    print "referrer: ", id(r), type(r)  
                del self._cache
                self._cache = None
        self._cacheLock.release()   
        return freed
        
    def _allocateManagementStructures(self):
        if type(self._origBlockShape) != tuple:
            self._blockShape = (self._origBlockShape,)*len(self.shape)
        else:
            self._blockShape = self._origBlockShape
            
        self._blockShape = numpy.minimum(self._blockShape, self.shape)

        self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
        
        print "Configured OpArrayCache with ", self.shape, self._blockShape, self._dirtyShape, self._origBlockShape

        # if the entry in _dirtyArray differs from _dirtyState
        # the entry is considered dirty
        self._blockQuery = numpy.ndarray(self._dirtyShape, dtype=object)
        self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)

        _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
        _blockNumbers.shape = self._dirtyShape

        _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
        _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)

         
        self._blockNumbers = _blockNumbers
        self._blockIndices = _blockIndices
        
                            #TODO: introduce constants for readability
                            #0 is "in process"
        self._blockState[:]= 1 #this is the dirty state
        self._dirtyState = 2 #this is the clean state
        
        # allocate queryArray object
        self._flatBlockIndices =  self._blockIndices[:]
        self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)
#        for p in self._flatBlockIndices:
#            self._blockQuery[p] = BlockQueue()
                 
        
    def _allocateCache(self):
        self._cacheLock.acquire()
          
        if self._cache is None or (self._cache.shape != self.shape):
            mem = numpy.ndarray(self.shape, dtype = self.dtype)
            print "OpArrayCache: Allocating cache (size: %dbytes)" % mem.nbytes
            self.graph._notifyMemoryAllocation(self, mem.nbytes)
            if self._blockState is None:
                self._allocateManagementStructures()
            inputSlot = self.inputs["Input"]
            self.graph._notifyFreeMemory(self._memorySize())
            self._cache = mem
        self._cacheLock.release()
            
    def notifyConnect(self, slot):
        reconfigure = False
        if  self.inputs["fixAtCurrent"].connected():
            self._fixed =  self.inputs["fixAtCurrent"].value        
        if slot == self.inputs["blockShape"]:
            newBShape = self.inputs["blockShape"].value
            if self._origBlockShape != newBShape and self.inputs["Input"].connected():
                reconfigure = True
            self._origBlockShape = newBShape                
        if slot == self.inputs["Input"]:
            OpArrayPiper.notifyConnectAll(self)
            inputSlot = self.inputs["Input"]
            reconfigure = True
    
        if reconfigure and self.shape is not None:
            self._lock.acquire()
            self._allocateManagementStructures()
            if not self._lazyAlloc:
                self._allocateCache()
            self._lock.release()

            
            
    def notifyDirty(self, slot, key):
        if not self._fixed:
            #print
            #print "OpArrayCache : DIRTY", key
            #print
            start, stop = sliceToRoi(key, self.shape)
            
            self._lock.acquire()
            if self._cache is not None:        
                blockStart = numpy.floor(1.0 * start / self._blockShape)
                blockStop = numpy.ceil(1.0 * stop / self._blockShape)
                blockKey = roiToSlice(blockStart,blockStop)
                self._blockState[blockKey] = 1
                #FIXME: we should recalculate results for which others are waiting and notify them...
            self._lock.release()
            
            self.outputs["Output"].setDirty(key)
        
    def getOutSlot(self,slot,key,result):
        #return     
        self.graph._notifyMemoryHit()
        
        start, stop = sliceToRoi(key, self.shape)
        
        self._lock.acquire()

        ch = self._cacheHits
        ch += 1
        self._cacheHits = ch
        
        if self._cache is None:
            self._allocateCache()
        blockStart = (1.0 * start / self._blockShape).floor()
        blockStop = (1.0 * stop / self._blockShape).ceil()
        blockKey = roiToSlice(blockStart,blockStop)

        blockSet = self._blockState[blockKey]
        
        # this is a little optimization to shortcut
        # many lines of python code when all data is
        # is already in the cache:
        if (blockSet == 2).all():
            self._lock.release()
            result[:] = self._cache[roiToSlice(start, stop)]
            return
    
        inProcessQueries = numpy.unique(numpy.extract( blockSet == 0, self._blockQuery[blockKey]))         
        
        cond = (blockSet == 1)
        tileWeights = fastWhere(cond, 1, 128**3, numpy.uint32)       
        #tileWeights = numpy.where(cond, 1, 128**3)       
        trueDirtyIndices = numpy.nonzero(cond)

                    
        #tileWeights = tileWeights.astype(numpy.uint32)
        #print "calling drtile...", tileWeights.dtype
        tileArray = drtile.test_DRTILE(tileWeights, 128**3).swapaxes(0,1)
        
        #print "finished calling drtile."
        #print "shape of the dirty tile array:", tileArray.shape
        
        dirtyRois = []
        half = tileArray.shape[0]/2
        dirtyRequests = []
#        print "Original Key %r, split into %d requests" % (key, tileArray.shape[1])
#        print self._blockState[blockKey][trueDirtyIndices]
#        print "Ranges:"
#        print "TileArray:", tileArray


        for i in range(tileArray.shape[1]):

            #drStart2 = (tileArray[half-1::-1,i] + blockStart)
            #drStop2 = (tileArray[half*2:half-1:-1,i] + blockStart)
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
                #print drStart2, drStop2, blockStart, self._blockShape
                #print "Request %d: %r" %(i,key)
    
                req = self.inputs["Input"][key].writeInto(self._cache[key])
                
                dirtyRequests.append((req,key2, key3))   
    
                self._blockQuery[key2] = req
                
                #sanity check:
                if (self._blockState[key2] != 1).any():
                    print "original condition", cond                    
                    print "original tilearray", tileArray, tileArray.shape
                    print "original tileWeights", tileWeights, tileWeights.shape
                    print "sub condition", self._blockState[key2] == 1 
                    print "START, STOP", drStart2, drStop2
                    import h5py
                    f = h5py.File("test.h5", "w")
                    f.create_dataset("data",data = tileWeights)
                    print "%r \n %r \n %r\n %r\n %r \n%r" % (key2, blockKey,self._blockState[key2], self._blockState[blockKey][trueDirtyIndices],self._blockState[blockKey],tileWeights)
                    assert 1 == 2
            else:
                self._cache[key] = 0
#        # indicate the inprocessing state, by setting array to 0     
        if not self._fixed:   
            blockSet[:]  = fastWhere(cond, 0, blockSet, numpy.uint8)
        self._lock.release()
        
        def onCancel(cancelled, reqBlockKey, reqSubBlockKey):
            if not cancelled[0]:
                cancelled[0] = True
                self._lock.acquire()
                blockSet = fastWhere(cond, 1, blockSet, numpy.uint8)
                self._blockQuery[blockKey] = fastWhere(cond, None, self._blockQuery[blockKey], object)                       
                self._lock.release()            
            
        temp = [False]            
            
        #wait for all requests to finish
        for req, reqBlockKey, reqSubBlockKey in dirtyRequests:
            req.onCancel(onCancel, cancelled = temp, reqBlockKey = reqBlockKey, reqSubBlockKey = reqSubBlockKey)
            res = req.wait()

        # indicate the finished inprocess state
        if not self._fixed:        
            self._lock.acquire()
            blockSet[:] = fastWhere(cond, 2, blockSet, numpy.uint8)
            self._blockQuery[blockKey] = fastWhere(cond, None, self._blockQuery[blockKey], object)                       
            self._lock.release()


        #wait for all in process queries
        for req in inProcessQueries:
            req.wait()
        
        # finally, store results in result area
        #print "Oparraycache debug",result.shape,self._cache[roiToSlice(start, stop)].shape
        self._lock.acquire()        
        if self._cache is not None:
            result[:] = self._cache[roiToSlice(start, stop)]
        else:
            self.inputs["Input"][roiToSlice(start, stop)].writeInto(result).wait()
        self._lock.release()
        
    def setInSlot(self, slot, key, value):
        ch = self._cacheHits
        ch += 1
        self._cacheHits = ch
        #print "OpArrayCache : SetInSlot", key
        start, stop = sliceToRoi(key, self.shape)
        blockStart = numpy.ceil(1.0 * start / self._blockShape)
        blockStop = numpy.floor(1.0 * stop / self._blockShape)
        blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
        blockKey = roiToSlice(blockStart,blockStop)

        if (blockStop >= blockStart).all():
            start2 = blockStart * self._blockShape
            stop2 = blockStop * self._blockShape
            stop2 = numpy.minimum(stop2, self.shape)
            key2 = roiToSlice(start2,stop2)
            self._lock.acquire()
            if self._cache is None:
                self._allocateCache()
            self._cache[key2] = value[roiToSlice(start2-start,stop2-start)]
            self._blockState[blockKey] = self._dirtyState
            self._lock.release()
        
        #pass request on
        self.outputs["Output"][key] = value
        
        
        
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
                    "_allocateCache" : self._allocateCache,
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
                    "_allocateCache" : "_allocateCache",
                    "_cacheHits" : "_cacheHits",
                    "_fixed" : "_fixed"
                },patchBoard)    

        setattr(op, "_blockQuery", numpy.ndarray(op._dirtyShape, dtype = object))

        return op        


if has_blist:       
    class OpSparseLabelArray(Operator):
        name = "Sparse Label Array"
        description = "simple cache for sparse label arrays"
           
        inputSlots = [InputSlot("Input"), InputSlot("shape"), InputSlot("eraser"), InputSlot("deleteLabel")]
        outputSlots = [OutputSlot("Output"), OutputSlot("nonzeroValues"), OutputSlot("nonzeroCoordinates")]    
        
        def __init__(self, graph):
            Operator.__init__(self, graph)
            self.lock = threading.Lock()
            self._denseArray = None
            self._sparseNZ = None
            
        def notifyConnect(self, slot):
            if slot.name == "shape":
                shape = self.inputs["shape"].value
                self.outputs["Output"]._dtype = numpy.uint8
                self.outputs["Output"]._shape = shape
                self.outputs["Output"]._axistags = vigra.defaultAxistags(len(shape))
        
                self.outputs["nonzeroValues"]._dtype = object
                self.outputs["nonzeroValues"]._shape = (1,)
                self.outputs["nonzeroValues"]._axistags = vigra.defaultAxistags(1)
                
                self.outputs["nonzeroCoordinates"]._dtype = object
                self.outputs["nonzeroCoordinates"]._shape = (1,)
                self.outputs["nonzeroCoordinates"]._axistags = vigra.defaultAxistags(1)
    
                self._denseArray = numpy.zeros(shape, numpy.uint8)
                self._sparseNZ =  blist.sorteddict()  
                
            if slot.name == "deleteLabel":
                labelNr = slot.value
                if labelNr is not -1:
                    neutralElement = 0
                    slot.setValue(-1) #reset state of inputslot
                    self.lock.acquire()
    
                    #remove values to be deleted
                    updateNZ = numpy.nonzero(numpy.where(self._denseArray == labelNr,1,0))
                    if len(updateNZ)>0:
                        updateNZRavel = numpy.ravel_multi_index(updateNZ, self._denseArray.shape)
                        self._denseArray.ravel()[updateNZRavel] = neutralElement
                        for index in updateNZRavel:
                            self._sparseNZ.pop(index)
                    self._denseArray[:] = numpy.where(self._denseArray > labelNr, self._denseArray - 1, self._denseArray)
                    self.lock.release()
                    self.outputs["nonzeroValues"][0] = numpy.array(self._sparseNZ.values())
                    self.outputs["nonzeroCoordinates"][0] = numpy.array(self._sparseNZ.keys())
                    self.outputs["Output"][:] = self._denseArray #set output dirty
                    
                
        def getOutSlot(self, slot, key, result):
            self.lock.acquire()
            assert(self.inputs["eraser"].connected() == True and self.inputs["shape"].connected() == True), "OpDenseSparseArray:  One of the neccessary input slots is not connected: shape: %r, eraser: %r" % (self.inputs["eraser"].connected(), self.inputs["shape"].connected())
            if slot.name == "Output":
                result[:] = self._denseArray[key]
            elif slot.name == "nonzeroValues":
                result[0] = numpy.array(self._sparseNZ.values())
            elif slot.name == "nonzeroCoordinates":
                result[0] = numpy.array(self._sparseNZ.keys())
            self.lock.release()
            return result
    
        def setInSlot(self, slot, key, value):
            shape = self.inputs["shape"].value
            eraseLabel = self.inputs["eraser"].value
            neutralElement = 0
    
            self.lock.acquire()
            #fix slicing of single dimensions:            
            start, stop = sliceToRoi(key, shape, extendSingleton = False)
            start = start.floor()
            stop = stop.floor()
            
            tempKey = roiToSlice(start-start, stop-start, hardBind = True)
            
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
            
            self.lock.release()
            
            self.outputs["Output"].setDirty(key)
    
    class OpBlockedSparseLabelArray(OperatorGroup):
        name = "Blocked Sparse Label Array"
        description = "simple cache for sparse label arrays"
           
        inputSlots = [InputSlot("Input"), InputSlot("shape"), InputSlot("eraser"), InputSlot("deleteLabel"), InputSlot("blockShape")]
        outputSlots = [OutputSlot("Output"), OutputSlot("nonzeroValues"), OutputSlot("nonzeroCoordinates"), OutputSlot("nonzeroBlocks")]
        
        def __init__(self, graph):
            OperatorGroup.__init__(self, graph)
            self.lock = threading.Lock()
            
            self._sparseNZ = None
            self._labelers = {}
            self.shape = None
            
            
        def _createInnerOperators(self):
            #Inner operators are created on demand            
            pass
            
        def notifyConnect(self, slot):
            if slot.name == "shape":
                self.shape = self.inputs["shape"].value
                self.outputs["Output"]._dtype = numpy.uint8
                self.outputs["Output"]._shape = self.shape
                self.outputs["Output"]._axistags = vigra.defaultAxistags(len(self.shape))
        
                self.outputs["nonzeroValues"]._dtype = object
                self.outputs["nonzeroValues"]._shape = (1,)
                self.outputs["nonzeroValues"]._axistags = vigra.defaultAxistags(1)
                
                self.outputs["nonzeroCoordinates"]._dtype = object
                self.outputs["nonzeroCoordinates"]._shape = (1,)
                self.outputs["nonzeroCoordinates"]._axistags = vigra.defaultAxistags(1)

                self.outputs["nonzeroBlocks"]._dtype = object
                self.outputs["nonzeroBlocks"]._shape = (1,)
                self.outputs["nonzeroBlocks"]._axistags = vigra.defaultAxistags(1)
    
                #Filled on request
                self._sparseNZ =  blist.sorteddict()
                
            if slot.name == "blockShape":
                self._origBlockShape = self.inputs["blockShape"].value
                
                if type(self._origBlockShape) != tuple:
                    self._blockShape = (self._origBlockShape,)*len(self.shape)
                else:
                    self._blockShape = self._origBlockShape
                    
                self._blockShape = numpy.minimum(self._blockShape, self.shape)
        
                self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
                
                print "Reconfigured Sparse labels with ", self.shape, self._blockShape, self._dirtyShape, self._origBlockShape
                #FIXME: we don't really need this blockState thing
                self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)
                
                _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
                _blockNumbers.shape = self._dirtyShape
        
                _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))
                _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)
        
                 
                self._blockNumbers = _blockNumbers
                self._blockIndices = _blockIndices
                
                # allocate queryArray object
                self._flatBlockIndices =  self._blockIndices[:]
                self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)
            
                
            if slot.name == "deleteLabel":
                print "not there yet"
                return
                labelNr = slot.value
                if labelNr is not -1:
                    neutralElement = 0
                    slot.setValue(-1) #reset state of inputslot
                    self.lock.acquire()
    
                    #remove values to be deleted
                    updateNZ = numpy.nonzero(numpy.where(self._denseArray == labelNr,1,0))
                    if len(updateNZ)>0:
                        updateNZRavel = numpy.ravel_multi_index(updateNZ, self._denseArray.shape)
                        self._denseArray.ravel()[updateNZRavel] = neutralElement
                        for index in updateNZRavel:
                            self._sparseNZ.pop(index)
                    self._denseArray[:] = numpy.where(self._denseArray > labelNr, self._denseArray - 1, self._denseArray)
                    self.lock.release()
                    self.outputs["nonzeroValues"][0] = numpy.array(self._sparseNZ.values())
                    self.outputs["nonzeroCoordinates"][0] = numpy.array(self._sparseNZ.keys())
                    self.outputs["Output"][:] = self._denseArray #set output dirty
                    
        def getOutSlot(self, slot, key, result):
            self.lock.acquire()
            #print "AAAAAAAAAAAAAAAAAAAA, request ", key, "from blocked labels", len(self._labelers), "filled so far"
            assert(self.inputs["eraser"].connected() == True and self.inputs["shape"].connected() == True and self.inputs["blockShape"].connected()==True), \
            "OpDenseSparseArray:  One of the neccessary input slots is not connected: shape: %r, eraser: %r" % \
            (self.inputs["eraser"].connected(), self.inputs["shape"].connected())
            if slot.name == "Output":
                #result[:] = self._denseArray[key]
                #find the block key
                start, stop = sliceToRoi(key, self.shape)
                blockStart = (1.0 * start / self._blockShape).floor()
                blockStop = (1.0 * stop / self._blockShape).ceil()
                blockKey = roiToSlice(blockStart,blockStop)
                innerBlocks = self._blockNumbers[blockKey]
                for b_ind in innerBlocks.ravel():
                    
                    #which part of the original key does this block fill?
                    offset = self._blockShape*self._flatBlockIndices[b_ind]
                    bigstart = numpy.maximum(offset, start)
                    bigstop = numpy.minimum(offset + self._blockShape, stop)
                
                    smallstart = bigstart-offset
                    smallstop = bigstop - offset
                    
                    bigkey = roiToSlice(bigstart-start, bigstop-start)
                    smallkey = roiToSlice(smallstart, smallstop)
                    if not b_ind in self._labelers:
                        #print "returning zeros from block ", b_ind, "for key ", bigkey
                        result[bigkey]=0
                    else:
                        result[bigkey]=self._labelers[b_ind]._denseArray[smallkey]
            
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
                    #print "labeler exists!", b_ind
                    offset = self._blockShape*self._flatBlockIndices[b_ind]
                    bigstart = offset
                    bigstop = numpy.minimum(offset + self._blockShape, self.shape)                    
                    bigkey = roiToSlice(bigstart, bigstop)
                    slicelist.append(bigkey)
                
                
#                slicelist = []
#                print "requesting key", key
#                start, stop = sliceToRoi(key, self.shape)
#                blockStart = (1.0 * start / self._blockShape).floor()
#                blockStop = (1.0 * stop / self._blockShape).ceil()
#                blockKey = roiToSlice(blockStart,blockStop)
#                innerBlocks = self._blockNumbers[blockKey]
#                for b_ind in innerBlocks.ravel():
#                    print "b_ind", b_ind
#                    if b_ind in self._labelers:
#                        print "labeler exists", b_ind
#                        offset = self._blockShape*self._flatBlockIndices[b_ind]
#                        bigstart = numpy.maximum(offset, start)
#                        bigstop = numpy.minimum(offset + self._blockShape, stop)                    
#                        bigkey = roiToSlice(bigstart, bigstop)
#                        slicelist.append(bigkey)
                result[0] = slicelist
                
                
            self.lock.release()
            return result
            
        def setInSlot(self, slot, key, value):
            #print "setting inslot, key:", key, "value", value.shape
            start, stop = sliceToRoi(key, self.shape)
            
            #print "start, stop:", start, stop, "blockshape:", self._blockShape
            blockStart = (1.0 * start / self._blockShape).floor()
            blockStop = (1.0 * stop / self._blockShape).ceil()
            blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
            blockKey = roiToSlice(blockStart,blockStop)
            #print "blockStop:", blockStop
            #blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
            #print "blockStop2:", blockStop
            #blockKey = roiToSlice(blockStart,blockStop)
            
            #FIXME: this assumes, that key passes 0 at singleton dimensions
            #FIXME: like volumeeditor does.
            nonsingletons = [i for i in range(len(key)) if key[i]!=0]
            
        
            #print "good dimensions:", nonsingletons
            innerBlocks = self._blockNumbers[blockKey]
            #print "innerBlocks:"
            for b_ind in innerBlocks.ravel():

                offset = self._blockShape*self._flatBlockIndices[b_ind]
                #print "offset:", offset
                bigstart = numpy.maximum(offset, start)
                bigstop = numpy.minimum(offset + self._blockShape, stop)
                #print "bigstart:", bigstart, "bigstop:", bigstop
                smallstart = bigstart-offset
                smallstop = bigstop - offset
                #print "smallstart:", smallstart, "smallstop", smallstop
                bigkey = roiToSlice(bigstart-start, bigstop-start)
                smallkey = roiToSlice(smallstart, smallstop)
                shortbigkey = [bigkey[i] for i in nonsingletons]
                #print "smallkey", smallkey
                #print "bigkey", bigkey
                #print "shortbigkey", shortbigkey, "value", value.shape
                if not b_ind in self._labelers:
                    #print "allocating labeler for b_ind", b_ind
                    self._labelers[b_ind]=OpSparseLabelArray(self.graph)
                    self._labelers[b_ind].inputs["shape"].setValue(self._blockShape)
                    self._labelers[b_ind].inputs["eraser"].setValue(self.inputs["eraser"])
                    self._labelers[b_ind].inputs["deleteLabel"].setValue(self.inputs["deleteLabel"])
                    
                self._labelers[b_ind].inputs["Input"][smallkey] = value[tuple(bigkey)].squeeze()
            
            self.outputs["Output"].setDirty(key)
        
        def notifyDirty(self, slot, key):
            if slot == self.inputs["Input"]:
                self.outputs["Output"].setDirty(key)
        
            
        def getInnerInputs(self):
            inputs = {}
            return inputs
        
        def getInnerOutputs(self):
            outputs = {}
            return outputs
            
            
locking = threading.Lock()          
            
            
class OpBlockedArrayCache(OperatorGroup):
    name = "OpBlockedArrayCache"
    description = ""

    inputSlots = [InputSlot("Input"),InputSlot("innerBlockShape"), InputSlot("outerBlockShape"), InputSlot("fixAtCurrent")]
    outputSlots = [OutputSlot("Output")]    

    def _createInnerOperators(self):
        
        self.source = OpArrayPiper(self.graph)
        self.fixerSource = OpArrayPiper(self.graph)

    def notifyConnect(self, slot):
        if slot == self.inputs["fixAtCurrent"]:
            self._fixed = self.inputs["fixAtCurrent"].value  
        if self.inputs["Input"].connected() and self.inputs["fixAtCurrent"].connected() and self.inputs["innerBlockShape"].connected() and self.inputs["outerBlockShape"].connected():
            if slot != self.inputs["fixAtCurrent"] or not hasattr(self,"_blockState"):
                inputSlot = self.inputs["Input"]
                
                self.outputs["Output"]._dtype = inputSlot.dtype
                self.outputs["Output"]._shape = inputSlot.shape
                self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)
                
                self._fixed = self.inputs["fixAtCurrent"].value        
                
                self._blockShape = self.inputs["outerBlockShape"].value
                self.shape = self.inputs["Input"].shape
                
                self._blockShape = tuple(numpy.minimum(self._blockShape, self.shape))
                    
                assert numpy.array(self._blockShape).min != 0, "ERROR in OpBlockedArrayCache: invalid blockShape"
                    
                self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))        
                    
                self._blockState = numpy.ones(self._dirtyShape, numpy.uint8)        
                    
                _blockNumbers = numpy.dstack(numpy.nonzero(self._blockState.ravel()))
                _blockNumbers.shape = self._dirtyShape
                    
                _blockIndices = numpy.dstack(numpy.nonzero(self._blockState))  
                _blockIndices.shape = self._blockState.shape + (_blockIndices.shape[-1],)
                    
                self._blockNumbers = _blockNumbers
                self._blockIndices = _blockIndices
            
                # allocate queryArray object
                self._flatBlockIndices =  self._blockIndices[:]
                self._flatBlockIndices = self._flatBlockIndices.reshape(self._flatBlockIndices.size/self._flatBlockIndices.shape[-1],self._flatBlockIndices.shape[-1],)     
                    
                self._opSub_list = {}
                self._cache_list = {}
            
#        for b_num in self._blockNumbers.ravel():
#                
#            self._opSub_list.append(generic.OpSubRegion(self.graph))
#            self._opSub_list[b_num].inputs["Input"].connect(self.source.outputs["Output"])
#                    
#            start = self._blockShape*self._flatBlockIndices[b_num]
#            stop = numpy.minimum((self._flatBlockIndices[b_num]+numpy.ones(self._flatBlockIndices[b_num].shape, numpy.uint8))*self._blockShape, self.shape)                
#                    
#            self._opSub_list[b_num].inputs["Start"].setValue(tuple(start))
#            self._opSub_list[b_num].inputs["Stop"].setValue(tuple(stop))
#    
#            self._cache_list.append(OpArrayCache(self.graph))
#            self._cache_list[b_num].inputs["Input"].connect(self._opSub_list[b_num].outputs["Output"])
#            self._cache_list[b_num].inputs["fixAtCurrent"].setValue(self._fixed)
#            self._cache_list[b_num].inputs["blockShape"].setValue(self.inputs["innerBlockShape"].value)
           
    def getOutSlot(self, slot, key, result):

        #find the block key
        start, stop = sliceToRoi(key, self.shape)
        blockStart = numpy.floor(1.0 * start / self._blockShape)
        blockStop = numpy.ceil(1.0 * stop / self._blockShape)
        blockStop = numpy.where(stop == self.shape, self._dirtyShape, blockStop)
        blockKey = roiToSlice(blockStart,blockStop)
        innerBlocks = self._blockNumbers[blockKey]
        result[:] = 0
        
        for b_ind in innerBlocks.ravel():
                
            #which part of the original key does this block fill?
            offset = self._blockShape*self._flatBlockIndices[b_ind]
            bigstart = numpy.maximum(offset, start)
            bigstop = numpy.minimum(offset + self._blockShape, stop)
            

            
            smallstart = bigstart-offset
            smallstop = bigstop - offset
            
            diff = smallstop - smallstart
            minimum = numpy.min(diff)
            smallkey = roiToSlice(smallstart, smallstop)
                
            bigkey = roiToSlice(bigstart-start, bigstop-start)                  
            if not self._fixed:
                if not self._cache_list.has_key(b_ind):
                    self._opSub_list[b_ind] = generic.OpSubRegion(self.graph)
                    self._opSub_list[b_ind].inputs["Input"].connect(self.source.outputs["Output"])
                            
                    tstart = self._blockShape*self._flatBlockIndices[b_ind]
                    tstop = numpy.minimum((self._flatBlockIndices[b_ind]+numpy.ones(self._flatBlockIndices[b_ind].shape, numpy.uint8))*self._blockShape, self.shape)                
                            
                    self._opSub_list[b_ind].inputs["Start"].setValue(tuple(tstart))
                    self._opSub_list[b_ind].inputs["Stop"].setValue(tuple(tstop))
            
                    self._cache_list[b_ind] = OpArrayCache(self.graph)
                    self._cache_list[b_ind].inputs["Input"].connect(self._opSub_list[b_ind].outputs["Output"])
                    self._cache_list[b_ind].inputs["fixAtCurrent"].connect(self.fixerSource.outputs["Output"])
                    self._cache_list[b_ind].inputs["blockShape"].setValue(self.inputs["innerBlockShape"].value)
            
            if self._cache_list.has_key(b_ind):
                req = self._cache_list[b_ind].outputs["Output"][smallkey].writeInto(result[bigkey])
                res = req.wait()

        return result

    def notifyDirty(self, slot, key):
        if slot == self.inputs["Input"]:
            self.outputs["Output"].setDirty(key)
            
            
    def getInnerInputs(self):
        inputs = {}
        inputs["Input"] = self.source.inputs["Input"]
        inputs["fixAtCurrent"] = self.fixerSource.inputs["Input"]
        return inputs
        
    def getInnerOutputs(self):
        outputs = {}
        return outputs
        
                   
        
