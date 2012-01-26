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


def runBenchmark(numThreads, cacheClass, shape, requests, repeatCount=200):    
    g = Graph(numThreads = numThreads)
    provider = OpArrayPiper(g)
    provider.inputs["Input"].setValue(numpy.zeros(shape,dtype = numpy.uint8))

    opa = OpA(g)
    opb = OpB(g)
    opc1 = cacheClass(g)
    opc1.inputs["blockShape"].setValue(5)
    opc2 = cacheClass(g)
    opc2.inputs["blockShape"].setValue(11)
    opfull = OpC(g)
    opc3 = cacheClass(g)
    opc3.inputs["blockShape"].setValue(7)
    opc4 = cacheClass(g)
    opc4.inputs["blockShape"].setValue(11)
    
    opPiper1 = OpArrayPiper(g)
    opPiper2 = OpArrayPiper(g)
    
    opa.inputs["Input"].connect(provider.outputs["Output"])
    opb.inputs["Input"].connect(opa.outputs["Output"])
    opc1.inputs["Input"].connect(opb.outputs["Output"])
    opc2.inputs["Input"].connect(opc1.outputs["Output"])
    opfull.inputs["Input"].connect(opc2.outputs["Output"])
    opc3.inputs["Input"].connect(opfull.outputs["Output"])
    opc4.inputs["Input"].connect(opc3.outputs["Output"])
    opPiper1.inputs["Input"].connect(opc4.outputs["Output"])
    opPiper2.inputs["Input"].connect(opPiper1.outputs["Output"])
    

    tg1 = time.time()
    
    for r in requests:
        if r == "setDirty":
            print "setting new data and dirty...."
            provider.inputs["Input"][:] = numpy.zeros(provider.inputs["Input"].shape,dtype = provider.inputs["Input"].dtype)
            continue
        key = roi.roiToSlice(numpy.array(r[0]), numpy.array(r[1]))
        t1 = time.time()
        for i in range(repeatCount):
            res1 = opPiper2.outputs["Output"][key].allocate().wait()
        t2 = time.time()
        print "%s request %r runtime:" % (cacheClass.__name__,key) , (t2-t1)/repeatCount
        assert (res1 == 1).all(), res1
    tg2 = time.time()
    g.finalize()
    print "%s Total runtime:" % cacheClass.__name__, tg2-tg1    

    gc.collect()


shape = (200,200,200)
requests = [[[30,30,30],[100,100,31]],
            [[0,0,0],[100,100,1]],
            [[50,50,50],[150,150,150]],
            [[50,50,50],[150,150,150]],
            [[0,0,0],[200,200,200]],
            [[0,0,0],[11,11,11]],
            "setDirty",
            [[0,0,0],[200,200,200]]
            ]
numThreads = 2
#runBenchmark(numThreads,OpArrayCache, shape, requests)


import cProfile
cProfile.run("runBenchmark(numThreads,OpArrayCache, shape, requests)", filename="benchmark.cprof")

import pstats
stats = pstats.Stats("benchmark.cprof")
print "##################################################################"
print "                  C U M U L A T I V E"
print "##################################################################"
stats.sort_stats("cumulative").print_stats(20) 
print "##################################################################"
print "                  T I M E"
print "##################################################################"

stats.sort_stats("time").print_stats(20) 