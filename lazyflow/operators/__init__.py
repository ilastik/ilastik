import traceback, os,  sys

import lazyflow

from lazyflow.graph import Operator
from lazyflow.helpers import itersubclasses

try:
    if modules != None:
        pass
except:
    modules = []
    from obsolete import generic
    from obsolete import vigraOperators
    from obsolete import classifierOperators
    from obsolete import valueProviders
    from obsolete import operators

    ops = itersubclasses(Operator)
    print "Loading default Operators..."
    for i, o in enumerate(ops):
        sys.stdout.write(o.__name__)
        sys.stdout.write(" ")
        globals()[o.__name__] = o
    sys.stdout.write(os.linesep+os.linesep)

    ops = list(itersubclasses(Operator))
    '''
    dirs = lazyflow.graph.CONFIG.get("Operators","directories", lazyflow.graph.CONFIG_DIR + "operators")
    dirs = dirs.split(",")
    for d in dirs:
        print "Loading Operators from ", d,"..."
        d = os.path.expanduser(d.strip())
        sys.path.append(d)
        files = os.listdir(d)
        for f in files:
            if os.path.isfile(d + "/" + f) and f[-3:] == ".py":
                try:
                    print "  Processing file", f
                    module = __import__(f[:-2])
                except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    pass

        ops2 = list(itersubclasses(Operator))

        newOps = list(set(list(ops2)).difference(set(list(ops))))
        
        for o in newOps:
            print "    Adding", o.__name__
            globals()[o.__name__] = o
	'''
    sys.stdout.write(os.linesep)
