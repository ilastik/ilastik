import numpy, vigra
from numpy.lib.stride_tricks import as_strided as ast
from math import ceil, floor

class TinyVector(list):
    __slots__ = []
    
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
        rdiv = numpy.divide
        if hasattr(other, "__iter__"):
            return TinyVector(map(lambda x,y: rdiv(y,x) ,self,other))
        else:
            return TinyVector(map(lambda x: rdiv(x),self))

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
    
    def _asint(self):
        return TinyVector(map(lambda x:  x.__int__() ,self))
    
    def insert(self,index, value):
        l = list(self)
        l.insert(index,value)
        return TinyVector(l)
    
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



sTrl1 =   lambda x: x if type(x) != slice else x.start if x.start != None else 0 
sTrl2 =  lambda x,y: y if type(y) != slice else y.stop if y.stop != None else x
sTrl3 = lambda x,y: y + 1 if x == y else y
def sliceToRoi(s, shape=None, extendSingleton = True):
    """Args:
            slice: slice object (1D) or list of slice objects (N-D)
       Returns:
            ROI instance corresponding to slice
    """
    if type(s) == tuple or type(s) == list:
      assert len(s) == len(shape)
      start = map(sTrl1, s)
      stop = map(sTrl2, shape,s)
    else: #this handles the [:] case
      start = [0]*len(shape)
      stop = shape
    if extendSingleton:
        stop = map(sTrl3,start,stop)
    return TinyVector(start), TinyVector(stop)


rTsl1 = lambda x,y:slice(x.__int__(),y.__int__())
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
                res.append(int(sta))
            else:
                res.append(slice(int(sta),int(stp)))
        return tuple(res)
    else:
        return tuple(map(rTsl1,start,stop))



def extendSlice(start, stop, shape, sigma, window = 3.5):
    zeros = start - start
    if hasattr(sigma, "__iter__"):
      sigma = TinyVector(sigma)
    newStart = numpy.maximum(start - numpy.ceil(window * sigma), zeros)
    sa = numpy.array(shape)
    newStop = numpy.minimum(stop + numpy.ceil(window * sigma), sa)
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

