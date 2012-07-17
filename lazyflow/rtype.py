from roi import sliceToRoi, roiToSlice
import vigra,numpy,copy
from lazyflow.roi import TinyVector

class Roi(object):
    def __init__(self, slot):
        self.slot = slot
        pass
    pass

class SubRegion(Roi):
    def __init__(self, slot, start = None, stop = None, pslice = None):
        super(SubRegion,self).__init__(slot)
        if pslice != None or start is not None and stop is None and pslice is None:
            if pslice is None:
                pslice = start
            assert self.slot.meta.shape is not None
            self.start, self.stop = sliceToRoi(pslice,self.slot.meta.shape)
        elif start is None and pslice is None:
            self.start, self.stop = sliceToRoi(slice(None,None,None),self.slot.meta.shape)
        else:
            self.start = TinyVector(start)
            self.stop = TinyVector(stop)
        self.axistags = None
        self.dim = len(self.start)

    def __str__( self ):
        return "".join(("Subregion: start '", str(self.start), "' stop '", str(self.stop), "'"))

    def setAxistags(self,axistags):
        assert type(axistags) == vigra.vigranumpycore.AxisTags
        self.axistags = copy.copy(axistags)
    
    def setInputShape(self,inputShape):
        assert type(inputShape) == tuple
        self.inputShape = inputShape
        
    def expandByShape(self,shape):
        """
        extend a roi by a given in shape
        """
        #TODO: Warn if bounds are exceeded
        retRoi = copy.copy(self)
        if type(shape == int):
            tmp = shape
            shape = numpy.zeros(self.dim).astype(int)
            shape[:] = tmp
            shape[self.axistags.channelIndex] = 0
        tmpStart = [x-s for x,s in zip(self.start,shape)]
        tmpStop = [x+s for x,s in zip(self.stop,shape)]
        retRoi.start = TinyVector([max(t,i) for t,i in zip(tmpStart,numpy.zeros_like(self.inputShape))])
        retRoi.stop = TinyVector([min(t,i) for t,i in zip(tmpStop,self.inputShape)])
        return retRoi

    def popAxis(self,axis):
        retRoi = copy.copy(self)
        for a in list(axis):
            if a in self.axistags.__repr__():
                popKey = self.axistags.index(a)
                retRoi.start.pop(popKey)
                retRoi.stop.pop(popKey)
        return retRoi
        
    def centerIn(self,shape):
        retRoi = copy.copy(self)
        difference = [int(((shape-(stop-start))/2.0)) for (shape,start),stop in zip(zip(shape,self.start),self.stop)]  
        dimension = [int(stop-start) for start,stop in zip(self.start,self.stop)]
        retRoi.start = TinyVector(difference)
        retRoi.stop = TinyVector([diff+dim for diff,dim in zip(difference,dimension)])
        return retRoi
    
    def setStartToZero(self):
        retRoi = copy.copy(self)
        start = [0]*len(self.start)
        stop = [end-begin for begin,end in zip(self.start,self.stop)]
        retRoi.start = TinyVector(start)
        retRoi.stop = TinyVector(stop)
        return retRoi
    
    def maskWithShape(self,shape):
        retRoi = copy.copy(self)
        start = [a for a,b in zip(retRoi.start,list(shape))]
        stop = [b for a,b in zip(retRoi.stop,list(shape))]
        retRoi.start = start
        retRoi.stop = stop
        return retRoi

    def toSlice(self, hardBind = False):
        return roiToSlice(self.start,self.stop, hardBind)
