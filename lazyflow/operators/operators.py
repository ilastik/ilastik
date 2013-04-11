#third-party dependencies
import psutil
if psutil.__version__ < '0.6':
    raise RuntimeError("lazyflow requires psutil 0.6.  Please upgrade your version of psutil (e.g. easy_install -U psutil)")
try:
    import blist
except:
    err =  "##############################################################"
    err += "#                                                            #"
    err += "#           please install blist (easy_install blist)        #"
    err += "#                                                            #"
    err += "##############################################################"
    raise RuntimeError(err)
try:
    from  lazyflow.drtile import drtile
except Exception, e:
    raise RuntimeError("Error importing drtile, please use cmake to compile lazyflow.drtile !\n" + str(e))

#lazyflow
import lazyflow
from lazyflow.rtype import SubRegion
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view, TinyVector, getBlockBounds
from lazyflow import request
from lazyflow.utility import Tracer

from lazyflow.operators.arrayCacheMemoryMgr import ArrayCacheMemoryMgr

#various cache operators
from lazyflow.operators.opArrayCache import OpArrayCache
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.opSparseLabelArray import OpSparseLabelArray
from lazyflow.operators.opBlockedSparseLabelArray import OpBlockedSparseLabelArray
from lazyflow.operators.opSlicedBlockedArrayCache import OpSlicedBlockedArrayCache


# create global Memory Manager instance
if not hasattr(ArrayCacheMemoryMgr, "instance"):
    mgr = ArrayCacheMemoryMgr() 
    setattr(ArrayCacheMemoryMgr, "instance" ,mgr)
    mgr.start()







































