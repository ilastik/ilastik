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
    def __init__(self, source, sourceAxis, destination, destinationAxis, transform):
        
        self.source = source
        self.sourceAxis = sourceAxis
        self.dest = destination
        self.destAxis = destinationAxis
        self.transform = transform
        self.sourceTransform = [None] * len(self.source.shape)
        self.destTransform = [None] * len(self.dest.shape)
        self.axisDict = {}
        self.revAxisDict = {}
        
        #check for the neccessary interface
        if not hasattr(self.source, 'shape'):
            raise RuntimeError('Source has no \'shape\' attribute')
        if not hasattr(self.dest, 'shape'):
            raise RuntimeError('Destination has no \'shape\' attribute')
        
        #ONLY the source needs axistags right now
        if not hasattr(self.source, 'axistags'):
            raise RuntimeError('Source has no \'axistags\' attribute')
        if not hasattr(self.source, '__getslice__'):
            raise RuntimeError('Source has no \'__getslice__\' attribute')
        if not hasattr(self.dest, '__getslice__'):
            raise RuntimeError('Destination has no \'__getslice__\' attribute')
        if not isinstance(self.sourceAxis, str):
            raise RuntimeError('SourceAxis must be a string')
        if not isinstance(self.destAxis, str):
            raise RuntimeError('DestinationAxis must be a string')
        
        #TODO: check for proper transformational iteration conditions:
        
        # check and parse the AxisStrings
        self.axisStringParser()
        #split and sort the sourceAxis and the destAxis
        self.createAxisDicts()
        # parse transforms
        self.transformParser()
        # expand the transforms for easy handling
        self.expandTransforms()
        #Setup the Axis,Dest iterspace
        self.setupIterSpace()
        
    def expandTransforms(self):
        
        #care, confusing code
        for i in range(len(self.source.shape)):
            if self.revAxisDict[i] in self.sourceAxis:
                self.destTransform[i] = self.transform[0][self.sourceAxis.index(self.revAxisDict[i])]
            else:
                self.destTransform[i] = 1
        
        for i in range(len(self.dest.shape)):
            if self.revAxisDict[i] in self.destAxis:
                self.sourceTransform[i] = self.transform[1][self.destAxis.index(self.revAxisDict[i])]
            else:
                self.sourceTransform[i] = 1
        
    def createAxisDicts(self):
        
        for i in range(len(self.source.axistags)):
            self.axisDict[self.source.axistags[i].key] = i
        self.revAxisDict = dict((v, k) for k, v in self.axisDict.iteritems())
        
    def __iter__(self):
        return self.iterSpace.__iter__()
    
    def transformParser(self):
        if len(self.transform[0]) == 0:
            self.transform[0] = (1,) * len(self.source.shape)
        if len(self.transform[1]) == 0:
            self.transform[1] = (1,) * len(self.source.shape)
        if type(self.transform[1]) == dict:
            tmp = [1]*len(self.dest.shape)
            for s in list('txyzc'):
                if s in self.transform[1].keys():
                    tmp[self.axisDict[s]] = self.transform[1][s]
            self.transform[1] = tuple(tmp) 

    def axisStringParser(self):
        self.sourceAxis = list(self.sourceAxis)
        self.destAxis = list(self.destAxis)
        if list('spatial') == self.sourceAxis:
            self.sourceAxis = []
            for tag in self.source.axistags:
                if tag.isSpatial():
                    self.sourceAxis.append(tag.key)
        if list('spatialc') == self.sourceAxis:
            self.sourceAxis = []
            for tag in self.source.axistags:
                if tag.isSpatial():
                    self.sourceAxis.append(tag.key)
            self.sourceAxis.append('c')
        if list('spatial') == self.destAxis:
            self.destAxis = []
            for tag in self.source.axistags:
                if tag.isSpatial():
                    self.destAxis.append(tag.key)
        if list('spatialc') == self.destAxis:
            self.destAxis = []
            for tag in self.source.axistags:
                if tag.isSpatial():
                    self.destAxis.append(tag.key)
            self.destAxis.append('c')

        allowedAxisKeys = set(['t', 'x', 'y', 'z', 'c'])
        if len(allowedAxisKeys.intersection(set(self.sourceAxis))) < len(self.sourceAxis):
            raise RuntimeError('There are non-allowed AxisKeys present in Source')
        if len(allowedAxisKeys.intersection(set(self.destAxis))) < len(self.destAxis):
            raise RuntimeError('There are non-allowed AxisKeys present in Destination')
        #check for proper dimensional iteration conditions:
        
        if len(self.destAxis) != len(self.sourceAxis):
            raise RuntimeError('Source and Target iteration dimensions are not equal')
        if len(self.destAxis) > len(self.dest.shape):
            print len(self.destAxis), len(self.dest.shape)
        if len(self.sourceAxis) > len(self.source.shape):
            raise RuntimeError('source iteration dimension is greater then source dimension')

        #TODO:check Consistency of transforms
        
    def setupIterSpace(self):
        
        def getSlicing(shape, string, transform = None):
            slicing = []
            mask = []
            for i in range(len(shape)):
                if self.revAxisDict[i] in [s for s in list('txyzc') if s not in string]:
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
            
        self.iterSpace = zip(getSlicing(self.source.shape, self.sourceAxis,self.transform[0]),\
                             getSlicing(self.dest.shape, self.destAxis,self.transform[1]))

