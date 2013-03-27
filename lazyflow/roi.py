import numpy
from numpy.lib.stride_tricks import as_strided as ast
from math import ceil, floor
import collections

class TinyVector(list):
    __slots__ = []

    def copy(self):
        return TinyVector(self)

    def __add__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x + y ,self,other))
        else:
            return TinyVector(map(lambda x: x + other ,self))

    __radd__ = __add__

    def __iadd__(self, other):
        # Must explicitly override list.__iadd__
        # Others (e.g. isub, imul) can use default implementation.
        if isinstance(other, collections.Iterable):
            self =  TinyVector(map(lambda x,y: x + y ,self,other))
            return self
        else:
            self = TinyVector(map(lambda x: x + other ,self))
            return self

    def __sub__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x - y ,self,other))
        else:
            return TinyVector(map(lambda x: x - other ,self))

    def __rsub__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: y - x ,self,other))
        else:
            return TinyVector(map(lambda x: other - x ,self))

    def __mul__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x * y ,self,other))
        else:
            return TinyVector(map(lambda x: x * other ,self))

    __rmul__ = __mul__

    def __div__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x/y ,self,other))
        else:
            return TinyVector(map(lambda x: x/other,self))

    def __rdiv__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  y / x,self,other))
        else:
            return TinyVector(map(lambda x:  other / x ,self))

    def __mod__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x % y ,self,other))
        else:
            return TinyVector(map(lambda x: x % other,self))

    def __rmod__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: y % x ,self,other))
        else:
            return TinyVector(map(lambda x: other % x,self))

    def __floordiv__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x // y ,self,other))
        else:
            return TinyVector(map(lambda x: x // other,self))

    def __rfloordiv__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: y // x ,self,other))
        else:
            return TinyVector(map(lambda x: other // x,self))

    def __eq__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  x == y,self,other))
        else:
            return TinyVector(map(lambda x:  x == other ,self))

    def __ne__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  x != y,self,other))
        else:
            return TinyVector(map(lambda x:  x != other ,self))

    def __ge__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  x >= y,self,other))
        else:
            return TinyVector(map(lambda x:  x >= other ,self))

    def __le__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  x <= y,self,other))
        else:
            return TinyVector(map(lambda x:  x <= other ,self))

    def __gt__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  x > y,self,other))
        else:
            return TinyVector(map(lambda x:  x > other ,self))

    def __lt__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y:  x < y,self,other))
        else:
            return TinyVector(map(lambda x:  x < other ,self))

    def __and__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x & y ,self,other))
        else:
            return TinyVector(map(lambda x: x & other,self))

    __rand__ = __and__

    def __or__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x | y ,self,other))
        else:
            return TinyVector(map(lambda x: x | other,self))

    __ror__ = __or__

    def __xor__(self, other):
        if isinstance(other, collections.Iterable):
            return TinyVector(map(lambda x,y: x ^ y ,self,other))
        else:
            return TinyVector(map(lambda x: x ^ other,self))

    __rxor__ = __xor__
    
    def __neg__(self):
        return self * -1
    
    def __abs__(self):
        return TinyVector( abs(x) for x in self )

    def __pos__(self):
        return TinyVector(self)
    
    def __invert__(self):
        return TinyVector(~x for x in self)
    
    def ceil(self):
        return TinyVector(map(ceil ,self))
        #return numpy.ceil(numpy.array(self))

    def floor(self):
        return TinyVector(map(floor ,self))
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

def expandSlicing(s, shape):
    """
    Args:
        s: Anything that can be used as a numpy array index:
           - int
           - slice
           - Ellipsis (i.e. ...)
           - Some combo of the above as a tuple or list
        
        shape: The shape of the array that will be accessed
        
    Returns:
        A tuple of length N where N=len(shape)
        slice(None) is inserted in missing positions so as not to change the meaning of the slicing.
        e.g. if shape=(1,2,3,4,5):
            0 --> (0,:,:,:,:)
            (0:1) --> (0:1,:,:,:,:)
            : --> (:,:,:,:,:)
            ... --> (:,:,:,:,:)
            (0,0,...,4) --> (0,0,:,:,4)            
    """
    if type(s) == list:
        s = tuple(s)
    if type(s) != tuple:
        # Convert : to (:,), or 5 to (5,)
        s = (s,)

    # Compute number of axes missing from the slicing
    if len(shape) - len(s) < 0:
        assert s == (Ellipsis,) or s == (slice(None),), "Slicing must not have more elements than the shape, except for [:] and [...] slices"

    # Replace Ellipsis with (:,:,:)
    if Ellipsis in s:
        ei = s.index(Ellipsis) # Ellipsis Index
        s = s[0:ei] + (len(shape) - len(s) + 1)*(slice(None),) + s[ei+1:]

    # Append (:,) until we get the right length
    s += (len(shape) - len(s))*(slice(None),)
    
    # Special case: we allow [:] and [...] for empty shapes ()
    if shape == ():
        s = ()
    
    return s

sTrl1 =   lambda x: x if type(x) != slice else x.start if x.start != None else 0
sTrl2 =  lambda x,y: y if type(y) != slice else y.stop if y.stop != None else x
sTrl3 = lambda x,y: y + 1 if x == y else y
def sliceToRoi(s, shape, extendSingleton = True):
    """Args:
            slice: slice object (1D) or list of slice objects (N-D)
            shape: the shape of the array to be sliced
            extendSingleton: if True, convert int indexes to slices so the dimension of the slicing matches the dimension of the shape.
       Returns:
            ROI instance corresponding to slice
    """
    s = expandSlicing(s, shape)
    start = map(sTrl1, s)
    stop = map(sTrl2, shape,s)
    if extendSingleton:
        stop = map(sTrl3,start,stop)
    return TinyVector(start), TinyVector(stop)

def roiFromShape(shape):
    start = TinyVector([0] * len(shape))
    stop = TinyVector(shape)
    return ( start, stop )

def getIntersection( roiA, roiB, assertIntersect=True ):    
    start = numpy.maximum( roiA[0], roiB[0] )    
    stop = numpy.minimum( roiA[1], roiB[1] )

    if numpy.prod(stop - start) <= 0:
        if assertIntersect:
            assert numpy.prod(stop - start) > 0, "Rois do not intersect!"
        else:
            return None    
    return (start, stop)

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
    if isinstance( sigma, collections.Iterable ):
        sigma = TinyVector(sigma)
    if isinstance( start, collections.Iterable ):
        ret_type = type(start[0])
    else:
        ret_type = type(start)
    newStart = numpy.maximum(start - numpy.ceil(window * sigma), zeros).astype( ret_type )
    sa = numpy.array(shape)
    newStop = numpy.minimum(stop + numpy.ceil(window * sigma), sa).astype( ret_type )
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

def getIntersectingBlocks( blockshape, roi, asmatrix=False ):
    """
    Returns the start coordinate of each block that the given roi intersects.
    By default, returned as an array of shape (N,M) (N indexes with M coordinates each).
    If asmatrix=True, then the blocks are returned as an array of shape (D1,D2,D3,...DN,M)
    such that coordinates of spatially adjacent blocks are returned in adjacent entries of the array.

    For example:

    >>> block_starts = getIntersectingBlocks( (10, 20), [(15, 25),(23, 40)] )
    >>> block_starts.shape
    (2, 2)
    >>> print block_starts
    [[10 20]
     [20 20]]

    >>> block_starts = getIntersectingBlocks( (10, 20), [(15, 25),(23, 41)] )
    >>> block_starts.shape
    (4, 2)
    >>> print block_starts
    [[10 20]
     [10 40]
     [20 20]
     [20 40]]

    Now the same two examples, with asmatrix=True.  Note the shape of the result.
    
    >>> block_start_matrix = getIntersectingBlocks( (10, 20), [(15, 25),(23, 40)], asmatrix=True )
    >>> block_start_matrix.shape
    (2, 1, 2)
    >>> print block_start_matrix
    [[[10 20]]
    <BLANKLINE>
     [[20 20]]]

    >>> block_start_matrix = getIntersectingBlocks( (10, 20), [(15, 25),(23, 41)], asmatrix=True )
    >>> block_start_matrix.shape
    (2, 2, 2)
    >>> print block_start_matrix
    [[[10 20]
      [10 40]]
    <BLANKLINE>
     [[20 20]
      [20 40]]]
    """
    assert len(blockshape) == len(roi[0]) == len(roi[1]), "blockshape and roi are mismatched."
    roistart = TinyVector( roi[0] )
    roistop = TinyVector( roi[1] )
    blockshape = TinyVector( blockshape )
    
    block_index_map_start = roistart / blockshape
    block_index_map_stop = ( roistop + (blockshape - 1) ) / blockshape # Add (blockshape-1) first as a faster alternative to ceil() 
    block_index_map_shape = block_index_map_stop - block_index_map_start
    
    num_axes = len(blockshape)
    block_indices = numpy.indices( block_index_map_shape )
    block_indices = numpy.rollaxis( block_indices, 0, num_axes+1 )
    block_indices += block_index_map_start

    # Multiply by blockshape to get the list of start coordinates
    block_indices *= blockshape

    if asmatrix:
        return block_indices
    else:
        # Reshape into N*M matrix for easy iteration
        num_indexes = numpy.prod(block_indices.shape[0:-1])
        axiscount = block_indices.shape[-1]
        return numpy.reshape( block_indices, (num_indexes, axiscount) )

def getBlockBounds(dataset_shape, block_shape, block_start):
    """
    Given a block start coordinate and block shape, return a roi for 
    the whole block, clipped to fit within the given dataset shape.
    
    >>> getBlockBounds( [35,35,35], [10,10,10], [10,20,30] )
    (array([10, 20, 30]), array([20, 30, 35]))
    """
    assert (numpy.mod( block_start, block_shape ) == 0).all(), "Invalid block_start.  Must be a multiple of the block shape!"

    entire_dataset_roi = roiFromShape( dataset_shape )
    block_shape = TinyVector( block_shape )
    block_bounds = ( block_start, block_start + block_shape )
    
    # Clip to dataset bounds
    block_bounds = getIntersection( block_bounds, entire_dataset_roi )
    return block_bounds

if __name__ == "__main__":
    import doctest
    doctest.testmod()
