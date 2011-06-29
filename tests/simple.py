import numpy, vigra
import time
from lazyflow.graph import *
import gc
from lazyflow import roi
import threading

from lazyflow.operators.operators import OpArrayCache, OpArrayPiper, OpMultiArrayPiper
from lazyflow.operators.obsoleteOperators import OpArrayBlockCache, OpArraySliceCache, OpArraySliceCacheBounding

__testing__ = False

from tests.mockOperators import OpA, OpB, OpC
from lazyflow.operators.valueProviders import ArrayProvider

def runBenchmark(numThreads, cacheClass, shape, requests):    
    g = Graph(numThreads = numThreads)
    provider = ArrayProvider( "Zeros", shape = shape, dtype=numpy.uint8)
    provider.setData(numpy.zeros(provider.shape,dtype = provider.dtype))
    opa = OpA(g)
    opb = OpB(g)
    opc1 = cacheClass(g,5)
    opc2 = cacheClass(g,11)
    opfull = OpC(g)
    opc3 = cacheClass(g,7)
    opc4 = cacheClass(g,11)
    opf = OpArrayCache(g)
    
    opa.inputs["Input"].connect(provider)
    opb.inputs["Input"].connect(opa.outputs["Output"])
    opc1.inputs["Input"].connect(opb.outputs["Output"])
    opc2.inputs["Input"].connect(opc1.outputs["Output"])
    opfull.inputs["Input"].connect(opc2.outputs["Output"])
    opc3.inputs["Input"].connect(opfull.outputs["Output"])
    opc4.inputs["Input"].connect(opc3.outputs["Output"])
    opf.inputs["Input"].connect(opc1.outputs["Output"])
    
    tg1 = time.time()
    
    for r in requests:
        if r == "setDirty":
            print "setting new data and dirty...."
            provider.setData(numpy.zeros(provider.shape,dtype = provider.dtype))
            continue
        key = roi.roiToSlice(numpy.array(r[0]), numpy.array(r[1]))
        t1 = time.time()
        res1 = opc4.outputs["Output"][key].allocate().wait()
        t2 = time.time()
        print "%s request %r runtime:" % (cacheClass.__name__,key) , t2-t1
        assert (res1 == 1).all(), res1
    tg2 = time.time()
    g.finalize()
    print "%s Total runtime:" % cacheClass.__name__, tg2-tg1    

    gc.collect()


shape = (200,200,200)
requests = [[[0,0,0],[100,100,1]],
            [[50,50,50],[150,150,150]],
            [[50,50,50],[150,150,150]],
            [[0,0,0],[200,200,200]],
            "setDirty",
            [[0,0,0],[200,200,200]]
            ]
numThreads = 2
#runBenchmark(numThreads,OpArrayBlockCache, shape, requests)
#runBenchmark(1,OpArrayBlockCache, shape, requests)
runBenchmark(numThreads,OpArrayCache, shape, requests)
