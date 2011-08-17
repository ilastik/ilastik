import numpy, vigra
from numpy.lib.stride_tricks import as_strided as ast
from math import ceil, floor

class TinyVector(list):
    __slots__ = []
    def __init__(self, data=None):
        list.__init__(self, data)
    
    def copy(self):
        return TinyVector(self)
    
    def __add__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y: x + y ,self,other))
        else:
            return TinyVector(map(lambda x: x + other ,self))

    def __iadd__(self, other):
        if hasattr(other, "__iter__"):
            self =  TinyVector(map(lambda x,y: x + y ,self,other))
            return self
        else:
            self = TinyVector(map(lambda x: x + other ,self))
            return self
            
    def __sub__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y: x - y ,self,other))
        else:
            return TinyVector(map(lambda x: x - other ,self))

    def __rsub__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y: y - x ,self,other))
        else:
            return TinyVector(map(lambda x: other - x ,self))
            
    def __mul__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y: x * y ,self,other))
        else:
            return TinyVector(map(lambda x: x * other ,self))

    def __div__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y: x / y ,self,other))
        else:
            return TinyVector(map(lambda x: x / other ,self))

    def __rdiv__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  y / x,self,other))
        else:
            return TinyVector(map(lambda x:  other / x ,self))

    def __eq__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  x == y,self,other))
        else:
            return TinyVector(map(lambda x:  x == other ,self))

    def __ne__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  x != y,self,other))
        else:
            return TinyVector(map(lambda x:  x != other ,self))

    def __ge__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  x >= y,self,other))
        else:
            return TinyVector(map(lambda x:  x >= other ,self))

    def __le__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  x <= y,self,other))
        else:
            return TinyVector(map(lambda x:  x <= other ,self))

    def __gt__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  x > y,self,other))
        else:
            return TinyVector(map(lambda x:  x > other ,self))

    def __lt__(self, other):
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y:  x < y,self,other))
        else:
            return TinyVector(map(lambda x:  x < other ,self))
            
    def ceil(self):
        return TinyVector(map(lambda x:  ceil(x) ,self))
        #return numpy.ceil(numpy.array(self))

    def floor(self):
        return TinyVector(map(lambda x:  floor(x) ,self))
        #return numpy.floor(numpy.array(self))
            
    def all(self):
        answer = True
        for e in self:
            if not e:
                answer = False
                break
        return answer
                      
    def any(self):
        answer = False
        for e in self:
            if e:
                answer = True
                break
        return answer                      
                      
TinyVector.__radd__ = TinyVector.__add__
TinyVector.__rmul__ = TinyVector.__mul__   


            
def sliceToRoi(s, shape=None, extendSingleton = True):
    """Args:
            slice: slice object (1D) or list of slice objects (N-D)
       Returns:
            ROI instance corresponding to slice
    """
    start = [0]*len(shape)
    stop = list(shape)
    try:
        for k in xrange(len(s)):
            try:
                if s[k].start is not None:
                    start[k] = s[k].start
                if s[k].stop is not None:
                    stop[k] = s[k].stop
            except:
                start[k] = s[k]
                stop[k] = s[k]
    except:
        try:
            if s.start is not None:
                start[0] = s.start
            if s.stop is not None:
                stop[0] = s.stop
        except:
            start[0] = s
            stop[0] = s
    if extendSingleton:
        stop = map(lambda x,y: y + 1 if x == y else y,start,stop)
    return TinyVector(start), TinyVector(stop)

#this method uses numpy arrays and is slower then the new one
def sliceToRoiOld(s, shape=None, extendSingleton = True):
    """Args:
            slice: slice object (1D) or list of slice objects (N-D)
       Returns:
            ROI instance corresponding to slice
    """
    start = numpy.zeros((len(shape),), dtype=numpy.int32)
    stop = numpy.array(shape)

    try:
        for k in xrange(len(s)):
            try:
                if s[k].start is not None:
                    start[k] = s[k].start
                if s[k].stop is not None:
                    stop[k] = s[k].stop
            except:
                start[k] = s[k]
                stop[k] = s[k]
    except:
        try:
            if s.start is not None:
                start[0] = s.start
            if s.stop is not None:
                stop[0] = s.stop
        except:
            start[0] = s
            stop[0] = s
    if extendSingleton and (stop - start == 0).any():
        temp = 1 - numpy.minimum(start - start + 1, stop - start)
        stop += temp
    return start, stop 


def roiToSlice(start, stop, hardBind=False):
    """Args:
            start (N-D coordinate): inclusive start
            stop  (N-D coordinate): exclusive stop
       Returns:
            list of slice objects describing the [start,stop) range,
            so that numpy.ndarray.__getitem__(roiToSlice(start,stop)) can be used.
    """
           
    if hardBind:
        res = []
        for sta, stp in zip(start,stop):
            if stp == sta + 1 or stp == sta:
                res.append(sta)
            else:
                res.append(slice(sta,stp))
        return tuple(res)
    else:
        return tuple(map(lambda x:slice(x[0],x[1]),zip(start,stop)))



def extendSlice(start, stop, shape, sigma):
    zeros = start - start
    newStart = numpy.maximum(start - numpy.ceil(3.5 * sigma), zeros)
    sa = numpy.array(shape)
    newStop = numpy.minimum(stop + numpy.ceil(3.5 * sigma), sa)
    return newStart, newStop


def block_view(A, block= (3, 3)):
    """Provide a 2D block view to 2D array. No error checking made.
    Therefore meaningful (as implemented) only for blocks strictly
    compatible with the shape of A."""
    # simple shape and strides computations may seem at first strange
    # unless one is able to recognize the 'tuple additions' involved ;-)
    shape= (A.shape[0]/ block[0], A.shape[1]/ block[1])+ block
    strides= (block[0]* A.strides[0], block[1]* A.strides[1])+ A.strides
    return ast(A, shape= shape, strides= strides)

