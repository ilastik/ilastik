import numpy, copy
import cPickle as pickle
import collections

from lazyflow.roi import TinyVector, sliceToRoi, roiToSlice
from lazyflow.utility import slicingtools

class RoiMeta(type):
    """
    Roi metaclass.  This mechanism automatically registers all roi 
    subclasses for string serialization via Roi._registerSubclass.
    """
    def __new__(cls, name, bases, classDict):
        cls = super(RoiMeta, cls).__new__(cls, name, bases, classDict)
        # Don't register the Roi baseclass itself.
        if bases[0] != object > 1:
            Roi._registerSubclass(cls)
        return cls

class Roi(object):
    __metaclass__ = RoiMeta

    def __init__(self, slot):
        self.slot = slot
        pass
    pass

    all_subclasses = set()

    @classmethod
    def _registerSubclass(cls, roiType):
        Roi.all_subclasses.add(roiType)

    @staticmethod
    def _toString(roi):
        """
        Convert roi into a string that can be converted back into a roi via _fromString().
        The default implementation uses pickle.
        Subclasses may override this and _fromString for more human-friendly string representations.
        """
        return pickle.dumps(roi)
    
    @staticmethod
    def _fromString(s):
        """
        Convert string 's' into a roi.
        The default implementation uses pickle.
        Subclasses may override this and _toString for more human-friendly string representations.
        """
        return pickle.loads(s)

    @staticmethod
    def dumps(roi):
        return roi.__class__.__name__ + ":" + roi.__class__._toString(roi)

    @staticmethod
    def loads(s):
        for cls in Roi.all_subclasses:
            if s.startswith(cls.__name__):
                return cls._fromString( s[len(cls.__name__)+1:] )
        assert False, "Class name within '{}' does not refer to any Roi subclasses.".format(s)

class Everything(Roi):
    '''Fallback Roi for Slots that can't operate on subsets of their input data.'''
    pass

class List(Roi):
    def __init__(self, slot, iterable=(), pslice=None):
        super(List, self).__init__(slot)
        self._l = list(iterable)
        if pslice is not None:
            print "pslice not none, but we are in a list!", pslice
            self._l = [pslice]
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

    @staticmethod
    def _toString(roi):
        assert isinstance(roi, SubRegion)
        assert roi.slot is None, "Can't stringify SubRegions with no slot"
        return "SubRegion(None, {}, {})".format(roi.start, roi.stop)

    @staticmethod
    def _fromString(s):
        return eval(s)

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
        if dim is not None:
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
        

    def expandByShape(self,shape,cIndex,tIndex):
        """
        extend a roi by a given in shape
        """
        #TODO: Warn if bounds are exceeded
        cStart = self.start[cIndex]
        cStop = self.stop[cIndex]
        if tIndex is not None:
            tStart = self.start[tIndex]
            tStop = self.stop[tIndex]
        if isinstance(shape, collections.Iterable):
            #add a dummy number for the channel dimension
            shape = shape+(1,)
        else:
            tmp = shape
            shape = numpy.zeros(self.dim).astype(int)
            shape[:] = tmp
        
        tmpStart = [int(x-s) for x,s in zip(self.start,shape)]
        tmpStop = [int(x+s) for x,s in zip(self.stop,shape)]
        start = [int(max(t,i)) for t,i in zip(tmpStart,numpy.zeros_like(self.inputShape))]   
        stop = [int(min(t,i)) for t,i in zip(tmpStop,self.inputShape)]
        start[cIndex] = cStart
        stop[cIndex] = cStop
        if tIndex is not None:
            start[tIndex] = tStart
            stop[tIndex] = tStop
        self.start = TinyVector(start)
        self.stop = TinyVector(stop)
        return self
        
    def adjustRoi(self,halo,cIndex=None):
        if type(halo) != list:
            halo = [halo]*len(self.start)
        notAtStartEgde = map(lambda x,y: True if x<y else False,halo,self.start)
        for i in range(len(notAtStartEgde)):
            if notAtStartEgde[i]:
                self.stop[i] = int(self.stop[i]-self.start[i]+halo[i])
                self.start[i] = int(halo[i])
        return self

    def adjustChannel(self,cPerC,cIndex,channelRes):
        if cPerC != 1 and channelRes == 1:
            start = [self.start[i]/cPerC if i == cIndex else self.start[i] for i in range(len(self.start))]
            stop = [self.stop[i]/cPerC+1 if i==cIndex else self.stop[i] for i in range(len(self.stop))]
            self.start = TinyVector(start)
            self.stop = TinyVector(stop)
        elif channelRes > 1:
            start = [0 if i == cIndex else self.start[i] for i in range(len(self.start))]
            stop = [channelRes if i==cIndex else self.stop[i] for i in range(len(self.stop))]
            self.start = TinyVector(start)
            self.stop = TinyVector(stop)
        return self

    def toSlice(self, hardBind = False):
        return roiToSlice(self.start,self.stop, hardBind)
