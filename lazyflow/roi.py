import numpy, vigra
from numpy.lib.stride_tricks import as_strided as ast

def sliceToRoi(s, shape=None):
    """Args:
            slice: slice object (1D) or list of slice objects (N-D)
       Returns:
            ROI instance corresponding to slice
    """
    assert type(s) == list or type(s) == slice or type(s) == tuple or type(s) == int
    
    if not isinstance(s, (list,tuple)):
        #special case for the [:] getall access
        if s == slice(None,None,None):
            s2 = []
            for i in range(len(shape)):
                s2.append(s)    
            s = s2 
        else:
            s = [s]
    s = list(s)    
    for i,k in enumerate(s):
        if type(k) is not slice:
            s[i] = slice(k,k+1,None)
        else:
            if k.stop is None:
                if shape is not None:
                    s[i] = slice(0,shape[i],None)
                else:
                    s[i] = slice(0,-1,None)
            elif k.start == k.stop:
                s[i] = slice(k.start,k.start+1,None)
                    
    start = numpy.array([k.start for k in s])
    stop = numpy.array([k.stop for k in s])
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
            if stp == sta + 1:
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

