# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

import traceback, os,  sys
import logging
logger = logging.getLogger(__name__)

import lazyflow

from lazyflow.graph import Operator
from lazyflow.utility.helpers import itersubclasses

# necessary because we used a factory
from vigraOperators import Op1ToMulti, Op5ToMulti, Op50ToMulti

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
    from opLabelImage import OpLabelImage
    from opCachedLabelImage import OpCachedLabelImage
    from opInterpMissingData import OpInterpMissingData
    from opCrosshairMarkers import OpCrosshairMarkers
    from opMaskedWatershed import OpMaskedWatershed
    from opSelectLabel import OpSelectLabel
    from opMaskedSelect import OpMaskedSelect
    from opReorderAxes import OpReorderAxes

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
    #sys.stdout.write(os.linesep)
