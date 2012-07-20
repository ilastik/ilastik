import os,numpy,itertools
from lazyflow.config import CONFIG
from lazyflow.roi import TinyVector

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


class AxisIterator:
    """
    An Iterator Class that iterates over slices of a source and a destination
    array. sourceAxis and destinationAxis specify the volume which is iterated
    over. Transform specifies the ratio between the source and destinaton slices.  
    """
    def __init__(self, source, sourceAxis, destination, destinationAxis, transform,destinationTags=None):
        self.source = source
        self.dest = destination
        self.sourceAxisDict,self.revSourceAxisDict = self.createAxisDicts(source)
        #this distinction is JUST for lazyflow
        if hasattr(destination,'meta.axistags') or hasattr(destination,'axistags'):
            self.destAxisDict,self.revDestAxisDict = self.createAxisDicts(destination) 
        else:
            self.destAxisDict,self.revDestAxisDict = self.sourceAxisDict,self.revSourceAxisDict
        self.sourceAxis = self.axisStringParser(sourceAxis)
        self.destAxis = self.axisStringParser(destinationAxis)
        self.transform = [self.transformParser(transform[0],self.sourceAxisDict),\
                          self.transformParser(transform[1],self.destAxisDict)]
        self.setupIterSpace()

    def transformParser(self,transform,axisDict):
        if len(transform) == 0:
            transform = (1,) * len(axisDict)  
        if type(transform) == dict:
            tmp = [1]*len(self.dest.shape)
            for s in list('txyzc'):
                if s in transform.keys():
                    tmp[axisDict[s]] = transform[s]
            transform = tuple(tmp)
        return transform
        
    def createAxisDicts(self,array):
        axisDict = dict((array.axistags[i].key,i) for i in range(len(array.axistags)))
        revAxisDict = dict((v, k) for k, v in axisDict.iteritems())
        return axisDict,revAxisDict    
        
    def axisStringParser(self,axis=None):
        axis = list(axis)
        if list('spatial') == axis:
            axis = []
            for tag in self.source.axistags:
                if tag.isSpatial():
                    axis.append(tag.key)
        if list('spatialc') == axis:
            axis = []
            for tag in self.source.axistags:
                if tag.isSpatial():
                    axis.append(tag.key)
            axis.append('c')
        return axis
    
    def __iter__(self):
        return self.iterSpace.__iter__()

    def setupIterSpace(self):
        def getSlicing(shape, string,revAxDic, transform = None):
            slicing = []
            mask = []
            for i in range(len(shape)):
                if revAxDic[i] in [s for s in list('txyzc') if s not in string]:
                    mask.append(range(0, shape[i],transform[i]))
                else:
                    mask.append(None)
            iterL = [m for m in mask if m is not None]
            iterS = itertools.product(*iterL)
            for s in iterS:
                sl = []
                c = 0
                for i in range(len(shape)):
                    if mask[i] is not None:
                        if transform[i] != 1:
                            sl.append(slice(s[c], s[c] + transform[i], None))
                        else:
                            sl.append(s[c])
                        c += 1
                    else:
                        sl.append(slice(0, None, None))
                slicing.append(sl)
            return slicing
        
        self.iterSpace = zip(getSlicing(self.source.shape, self.sourceAxis,self.revSourceAxisDict,self.transform[0]),\
                             getSlicing(self.dest.shape, self.destAxis,self.revDestAxisDict,self.transform[1]))