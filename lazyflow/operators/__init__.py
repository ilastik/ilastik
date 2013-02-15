import traceback, os,  sys
import logging
logger = logging.getLogger(__name__)

import lazyflow

from lazyflow.graph import Operator
from lazyflow.utility.helpers import itersubclasses

try:
    if modules != None:
        pass
except:
    modules = []
    import generic
    import vigraOperators
    import classifierOperators
    import valueProviders
    import operators
    
    ops = itersubclasses(Operator)
    logger.debug("Loading default Operators...")
    loaded = ""
    for i, o in enumerate(ops):
        loaded += o.__name__ + ' '
        globals()[o.__name__] = o
    loaded += os.linesep
    logger.debug(loaded)

    from opVigraWatershed import OpVigraWatershed
    from opVigraLabelVolume import OpVigraLabelVolume
    from opFilterLabels import OpFilterLabels
    from opColorizeLabels import OpColorizeLabels
    from opObjectFeatures import OpObjectFeatures
    from adaptors import Op5ifyer
    from opCompressedCache import OpCompressedCache
    from opLabelImage import OpLabelImage, OpCachedLabelImage

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
