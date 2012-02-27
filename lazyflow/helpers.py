import os,numpy
from lazyflow.config import CONFIG


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

def generateRandomKeys(shape):
    """
    for a given shape of any dimension this method returns a list of slicings 
    which is bounded by the shape
    """
    
    dim = len(shape)
    tmp = numpy.zeros((len(shape),2))
    while len([x for x in tmp if x[0]!=x[1]]) < dim:
        tmp = numpy.random.rand(dim,2)
        for i in range(dim):
                tmp[i,:] *= shape[i]
                tmp[i,:] = numpy.sort(numpy.round(tmp[i,:]))
    key = [slice(int(x[0]),int(x[1]),None) for x in tmp]
    return key

def generateRandomRoi(shape):
    """
    for a given shape of any dimension this method returns a roi which is 
    bounded by the shape
    """
    roi = [[0,0]]
    while len([x for x in roi if not abs(x[0]-x[1])<=1]) < len(shape):
        roi = [sorted([numpy.random.randint(dim),numpy.random.randint(dim)]) for dim in shape]
    roi = [[x[0] for x in roi],[x[1] for x in roi]]
    return roi
