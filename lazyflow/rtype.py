from roi import sliceToRoi, roiToSlice
import vigra,numpy,copy
from lazyflow.roi import TinyVector
from lazyflow import slicingtools

class Roi(object):
    def __init__(self, slot):
        self.slot = slot
        pass
    pass



class Everything(Roi):
    '''Fallback Roi for Slots that can't operate on subsets of their input data.'''
    pass


class List(Roi):
    def __init__(self, slot, iterable=()):
        super(List, self).__init__(slot)
        self._l = list(iterable)
    def __iter__( self ):
        return iter(self._l)
    def __len__( self ):
        return len(self._l)
    def __str__( self ):
        return str(self._l)


    
class SubRegion(Roi):
    def __init__(self, slot, start = None, stop = None, pslice = None):
        super(SubRegion,self).__init__(slot)
        if pslice != None or start is not None and stop is None and pslice is None:
            if pslice is None:
                pslice = start
            shape = self.slot.meta.shape
            if shape is None:
                # Okay to use a shapeless slot if the key is bounded
                # AND if the key has the correct length
                assert slicingtools.is_bounded(pslice)
                # Supply a dummy shape
                shape = [0] * len(pslice)
            self.start, self.stop = sliceToRoi(pslice,shape)
        elif start is None and pslice is None:
            self.start, self.stop = sliceToRoi(slice(None,None,None),self.slot.meta.shape)
        else:
            self.start = TinyVector(start)
            self.stop = TinyVector(stop)
        self.dim = len(self.start)

    def __str__( self ):
        return "".join(("Subregion: start '", str(self.start), "' stop '", str(self.stop), "'"))

    def setInputShape(self,inputShape):
        assert type(inputShape) == tuple
        self.inputShape = inputShape

    def copy(self):
        return copy.copy(self)

    def popDim(self, dim):
        """
        remove the i'th dimension from the SubRegion
        works inplace !
        """
        self.start.pop(dim)
        self.stop.pop(dim)
        return self

    def setDim(self, dim , start, stop):
        """
        change the subarray at dim, to begin at start
        and to end at stop
        """
        self.start[dim] = start
        self.stop[dim] = stop
        return self

    def insertDim(self, dim, start, stop, at):
        """
        insert a new dimension before dim.
        set start to start, stop to stop
        and the axistags to at
        """
        self.start.insert(0,start)
        self.stop.insert(0,stop)
        return self
        

    def expandByShape(self,shape):
        """
        extend a roi by a given in shape
        """
        #TODO: Warn if bounds are exceeded
        if type(shape == int):
            tmp = shape
            shape = numpy.zeros(self.dim).astype(int)
            shape[:] = tmp
        tmpStart = [x-s for x,s in zip(self.start,shape)]
        tmpStop = [x+s for x,s in zip(self.stop,shape)]
        self.start = TinyVector([max(t,i) for t,i in zip(tmpStart,numpy.zeros_like(self.inputShape))])
        self.stop = TinyVector([min(t,i) for t,i in zip(tmpStop,self.inputShape)])
        return self

        
    def centerIn(self,shape):
        difference = [int(((shape-(stop-start))/2.0)) for (shape,start),stop in zip(zip(shape,self.start),self.stop)]  
        dimension = [int(stop-start) for start,stop in zip(self.start,self.stop)]
        self.start = TinyVector(difference)
        self.stop = TinyVector([diff+dim for diff,dim in zip(difference,dimension)])
        return self
    
    def setStartToZero(self):
        start = [0]*len(self.start)
        stop = [end-begin for begin,end in zip(self.start,self.stop)]
        self.start = TinyVector(start)
        self.stop = TinyVector(stop)
        return self
    
    def maskWithShape(self,shape):
        start = [a for a,b in zip(self.start,list(shape))]
        stop = [b for a,b in zip(self.stop,list(shape))]
        self.start = start
        self.stop = stop
        return self

    def toSlice(self, hardBind = False):
        return roiToSlice(self.start,self.stop, hardBind)
