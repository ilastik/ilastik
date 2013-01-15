import os,numpy,itertools,copy
from lazyflow.config import CONFIG
from lazyflow.roi import TinyVector, roiToSlice

def warn_deprecated( msg ):
    warn = True
    if CONFIG.has_option("verbosity", "deprecation_warnings"):
        warn = CONFIG.getboolean("verbosity", "deprecation_warnings")
    if warn:
        import inspect
        import os.path
        fi = inspect.getframeinfo(inspect.currentframe().f_back)
        print "DEPRECATION WARNING: in", os.path.basename(fi.filename), "line", fi.lineno, ":", msg

# deprecation warning decorator
def deprecated( fn ):
    def warner(*args, **kwargs):
        warn_deprecated( fn.__name__ )
        return fn(*args, **kwargs)
    return warner

def itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.

    >>> list(itersubclasses(int)) == [bool]
    True
    >>> class A(object): pass
    >>> class B(A): pass
    >>> class C(A): pass
    >>> class D(B,C): pass
    >>> class E(D): pass
    >>>
    >>> for cls in itersubclasses(A):
    ...     print(cls.__name__)
    B
    D
    E
    C
    >>> # get ALL (new-style) classes currently defined
    >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
    ['type', ...'tuple', ...]
    """

    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None: _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError: # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


#detectCPUS function is shamelessly copied from the intertubes
def detectCPUs():
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else: # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
        if ncpus > 0:
            return ncpus
    return 1 # Default

def generateRandomKeys(maxShape,minShape = 0,minWidth = 0):
    """
    for a given shape of any dimension this method returns a list of slicings
    which is bounded by maxShape and minShape and has the minimum Width minWidth
    in all dimensions
    """
    if not minShape:
        minShape = tuple(numpy.zeros_like(list(maxShape)))
    assert len(maxShape) == len(minShape),'Dimensions of Shape do not match!'
    maxDim = len(maxShape)
    tmp = numpy.zeros((maxDim,2))
    while len([x for x in tmp if not x[1]-x[0] <= minWidth]) < maxDim:
        tmp = numpy.random.rand(maxDim,2)
        for i in range(maxDim):
            tmp[i,:] *= (maxShape[i]-minShape[i])
            tmp[i,:] += minShape[i]
            tmp[i,:] = numpy.sort(numpy.round(tmp[i,:]))
    key = [slice(int(x[0]),int(x[1]),None) for x in tmp]
    return key

def generateRandomRoi(maxShape,minShape = 0,minWidth = 0):
    """
    for a given shape of any dimension this method returns a roi which is
    bounded by maxShape and minShape and has the minimum Width in minWidth
    in all dimensions
    """
    if not minShape:
        minShape = tuple(numpy.zeros_like(maxShape))
    assert len(maxShape) == len(minShape),'Dimensions of Shape do not match!'
    roi = [[0,0]]
    while len([x for x in roi if not abs(x[0]-x[1]) < minWidth]) < len(maxShape):
        roi = [sorted([numpy.random.randint(minDim,maxDim),numpy.random.randint(minDim,maxDim)]) for minDim,maxDim in zip(minShape,maxShape)]
    roi = [TinyVector([x[0] for x in roi]),TinyVector([x[1] for x in roi])]
    return roi



class newIterator:
    def __init__(self,roi,srcGrid,trgtGrid,timeIndex = None,channelIndex = None):
        #cast list due to TinyVector being strange
        self.roi = (list(roi.start),list(roi.stop))
        self.srcGrid = srcGrid
        self.trgtGrid = trgtGrid
        self.cIndex = channelIndex
        if timeIndex is not None:
            self.hardBind = [timeIndex]
        else:
            self.hardBind = []
            

    def nextStop(self,start,grid,roi):
        mult = [b/l for b,l in zip(start,grid)]
        gridStop = [(m+1)*l for m,l in zip(mult,grid)]
        roiStop = roi[1]
        nextStop = [min(a,b) for a,b in zip(gridStop,roiStop)] 
        if reduce(lambda x,y: x or y, map(lambda x,y: True if x==y else False,roiStop,start),False):
            return None
        else:
            return nextStop
        
    def nextStarts(self,point,grid,roi):
        nextPoint = self.nextStop(point,grid,roi)
        nextStarts = []
        if nextPoint:
            for j in range(len(nextPoint)):
                p = copy.copy(point)
                p[j] = nextPoint[j]
                nextStarts.append(p)
            nextStarts.append(nextPoint)
        return nextStarts
    
    def getSubRois(self,point,grid,roi):
        starts = [point]
        visited = []
        subRois = []
        while len(starts):
            start = starts.pop()
            visited.append(start)
            nextStop = self.nextStop(start,grid,roi)
            if nextStop:
                subRois.append((start,nextStop))
            for s in self.nextStarts(start,grid,roi):
                if not s in visited:
                    starts.append(s)
        return subRois
    
    def getMask(self,subRoi,grid):
        start0 = subRoi[0]
        stop0 = subRoi[1]
        cIndex = self.cIndex
        start1 = [start0[i]%grid[i] if i == cIndex else 0 for i in range(len(start0))]
        stop1 = [stop0[i]-start0[i] if i != cIndex else stop0[i]%grid[i] if stop0[i]%grid[i] != 0 else grid[i] for i in range(len(stop0))]
        for i in self.hardBind:
            start1.pop(i)
            stop1.pop(i)
        return (start1,stop1)

    def mapRoiToSource(self,subRoi,srcGrid=None,trgtGrid=None):
        start = subRoi[0]
        stop = subRoi[1]
        if srcGrid is None:
            srcGrid = self.srcGrid
        if trgtGrid is None:
            trgtGrid = self.trgtGrid
        start = [start[i]/trgtGrid[i]*srcGrid[i] for i in range(len(start))]
        stop = [start[i]+srcGrid[i] for i in range(len(stop))]
        return (start,stop)
    
    def translateRoi(self,subRoi,point):
        start = subRoi[0]
        stop = subRoi[1]
        start = [start[i] - point[i] for i in range(len(start))]
        stop = [stop[i] - point[i] for i in range(len(start))]
        return (start,stop)
    
    def toSlice(self,roi,hardBind=False):
        start = roi[0]
        stop = roi[1]
        rTsl1 = lambda x,y:slice(x.__int__(),y.__int__())
        if self.hardBind and hardBind:
            res = []
            zipL = zip(start,stop)
            for i in range(len(zipL)):
                if (zipL[i][1] == zipL[i][0] + 1 or zipL[i][1] == zipL[i][0]) and i in self.hardBind:
                    res.append(int(zipL[i][0]))
                else:
                    res.append(slice(int(zipL[i][0]),int(zipL[i][1])))
            return tuple(res)
        else:
            return tuple(map(rTsl1,start,stop))
    
    def __iter__(self):
        trgtRois = self.getSubRois(self.roi[0], self.trgtGrid, self.roi)
        srcRoi = self.mapRoiToSource(self.roi)
        retRoi = [(self.translateRoi(self.mapRoiToSource(roi),srcRoi[0]),\
                 self.translateRoi(roi,self.roi[0]),self.getMask(roi,self.trgtGrid))\
                for roi in trgtRois]
        retSlice = [(self.toSlice(src,True),self.toSlice(trgt,True),self.toSlice(mask)) \
                    for src,trgt,mask in retRoi]
        return retSlice.__iter__()
 
if __name__ == "__main__":
    
    class roi:
        def __init__(self,start,stop):
            self.start = start
            self.stop = stop
    r = roi([16, 22, 35, 8],[34, 36, 36, 22])
    nIt = newIterator(r,[1,26,13,1],[1,40,40,1],channelIndex=3,timeIndex=0)
    for i,j,k in nIt:
        pass
