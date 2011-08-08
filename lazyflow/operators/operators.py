import numpy

from lazyflow.graph import Operators, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view
from Queue import Empty
from collections import deque
from lazyflow.h5dumprestore import stringToClass
import greenlet, threading
import vigra
import copy
from threading import current_thread

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
        res = req()
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
        res = req()
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
        
        splitDim = numpy.argmax(diff)
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
        


class OpArrayCache(OpArrayPiper):
    name = "ArrayCache"
    description = "numpy.ndarray caching class"
    category = "misc"
    
    inputSlots = [InputSlot("Input"), InputSlot("blockShape")]
    outputSlots = [OutputSlot("Output")]    
    
    def __init__(self, graph, blockShape = None, immediateAlloc = True):
        OpArrayPiper.__init__(self, graph)
        if blockShape == None:
            blockShape = 64
        self._origBlockShape = blockShape
        self._blockShape = None
        self._dirtyShape = None
        self._blockState = None
        self._dirtyState = None
        self._cache = None
        self._immediateAlloc = immediateAlloc
        self._lock = threading.Lock()
        
    def notifyConnect(self, slot):
        if self.inputs["blockShape"].connected():
            self._origBlockShape = self.inputs["blockShape"].value
        if self.inputs["Input"].connected():
            inputSlot = self.inputs["Input"]
            OpArrayPiper.notifyConnectAll(self)
            self._cache = numpy.ndarray(self.shape, dtype = self.dtype)
            
            if type(self._origBlockShape) != tuple:
                self._blockShape = (self._origBlockShape,)*len(self.shape)
            else:
                self._blockShape = self._origBlockShape
                
            self._blockShape = numpy.minimum(self._blockShape, self.shape)
    
            self._dirtyShape = numpy.ceil(1.0 * numpy.array(self.shape) / numpy.array(self._blockShape))
            
            print "Reconfigured OpArrayCache with ", self.shape, self._blockShape, self._dirtyShape, self._origBlockShape
    
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
            

    def notifyDirty(self, slot, key):
        #print "OpArrayCache : DIRTY", key
        start, stop = sliceToRoi(key, self.shape)
        
        self._lock.acquire()
        blockStart = numpy.floor(1.0 * start / self._blockShape)
        blockStop = numpy.ceil(1.0 * stop / self._blockShape)
        blockKey = roiToSlice(blockStart,blockStop)
        self._blockState[blockKey] = 1
        #FIXEM: we should recalculate results for which others are waiting and notify them...
        self._lock.release()
        
        self.outputs["Output"].setDirty(key)
        
    def getOutSlot(self,slot,key,result):
        start, stop = sliceToRoi(key, self.shape)
        
        
        self._lock.acquire()
        blockStart = numpy.floor(1.0 * start / self._blockShape)
        blockStop = numpy.ceil(1.0 * stop / self._blockShape)
        blockKey = roiToSlice(blockStart,blockStop)
                
        inProcessQueries = numpy.unique(numpy.extract(self._blockState[blockKey] == 0, self._blockQuery[blockKey]))         
        
        cond = (self._blockState[blockKey] == 1)
        tileWeights = numpy.where(cond, 1, 128**3)       
        trueDirtyIndices = numpy.nonzero(numpy.where(cond, 1,0))
                    
        tileWeights = tileWeights.astype(numpy.uint32)
        #print "calling drtile...", tileWeights.dtype
        tileArray = drtile.test_DRTILE(tileWeights, 128**3).swapaxes(0,1)
                
        #print "finished calling drtile."
        dirtyRois = []
        half = tileArray.shape[0]/2
        dirtyRequests = []
#        print "Original Key %r, split into %d requests" % (key, tileArray.shape[1])
#        print self._blockState[blockKey][trueDirtyIndices]
#        print "Ranges:"
#        print "TileArray:", tileArray

        bq = BlockQueue()
        bq.queue = deque()
                
        for i in range(tileArray.shape[1]):

            #drStart2 = (tileArray[half-1::-1,i] + blockStart)
            #drStop2 = (tileArray[half*2:half-1:-1,i] + blockStart)
            drStart2 = tileArray[:half,i] + blockStart
            drStop2 = tileArray[half:,i] + blockStart
            drStart = drStart2*self._blockShape
            drStop = drStop2*self._blockShape

            drStop = numpy.minimum(drStop, self.shape)
            drStart = numpy.minimum(drStart, self.shape)
            
            key2 = roiToSlice(drStart2,drStop2)

            key = roiToSlice(drStart,drStop)
            dirtyRois.append([drStart,drStop])
            #print drStart2, drStop2, blockStart, self._blockShape
            #print "Request %d: %r" %(i,key)

            dirtyRequests.append((key,drStart,drStop))   

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
            
#        # indicate the inprocessing state, by setting array to 0        
        self._blockState[blockKey] = numpy.where(cond, 0, self._blockState[blockKey])
        self._blockQuery[blockKey] = numpy.where(cond, bq, self._blockQuery[blockKey])               
        self._lock.release()
        
        
        requests = []
        #fire off requests
        for r in dirtyRequests:
            key, reqStart, reqStop = r
            #req = self.inputs["Input"][key].writeInto(self._cache[key])
            req = self.inputs["Input"][key].allocate() #this is safer for cancelled requests
            requests.append((req, key))
            
        #wait for all requests to finish
        for req,key in requests:
            res = req.wait()
            self._cache[key] = res            
            
        # indicate the finished inprocess state        
        self._lock.acquire()
        self._blockState[blockKey] = numpy.where(cond, 2, self._blockState[blockKey])
        self._blockQuery[blockKey] = numpy.where(cond, None, self._blockQuery[blockKey])                       
        self._lock.release()

        
        #notify eventual waiters
        bq.lock.acquire()
        for w in bq.queue:
            w[1].finishedRequests.append(FakeGetItemRequestObject(w[0]))
            w[1].signalWorkAvailable()
        bq.queue = None
        bq.lock.release()
        

        #wait for all in process queries
        for q in inProcessQueries:
            q.lock.acquire()
            if q.queue is not None:
                gr = greenlet.getcurrent()
                task = [gr,threading.current_thread()]
                q.queue.append(task)
                q.lock.release()
                greenlet.getcurrent().parent.switch(None)
            else:
                q.lock.release()
                pass
        
        # finally, store results in result area
        #print "Oparraycache debug",result.shape,self._cache[roiToSlice(start, stop)].shape
        result[:] = self._cache[roiToSlice(start, stop)]
        
        
        
    def setInSlot(self, slot, key, value):
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
            start = start.astype(numpy.int32)
            stop = stop.astype(numpy.int32)
            
            tempKey = roiToSlice(start-start, stop-start, hardBind = True)
            
            stop += numpy.where(stop-start == 0,1,0)
            key = roiToSlice(start,stop)
    
            updateShape = tuple(stop-start)
    
            update = self._denseArray[key].copy()
    
            update[tempKey] = value
            
            startRavel = numpy.ravel_multi_index(start,shape)
            
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
