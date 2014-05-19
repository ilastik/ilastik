###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
import time
import gc
import random
import threading
from functools import partial
import numpy
import vigra
import lazyflow.graph
from lazyflow.operators.operators import OpArrayCache
from lazyflow.operator import Operator
from lazyflow.slot import InputSlot, OutputSlot
from lazyflow.operatorWrapper import OperatorWrapper
from matplotlib import pyplot


class OpA(Operator):
    input = InputSlot()
    output = OutputSlot()
    
    
    def __init__(self, parent = None):
        Operator.__init__(self, parent)
        self.countSetupOutputs = 0
    
    def setupOutputs(self):
        self.countSetupOutputs += 1
        self.output.meta.shape = self.input.meta.shape
        self.output.meta.dtype = self.input.meta.dtype
        
    
    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, slot, subindex, roi):
        pass


results = []
results_gc = []

    
gc.disable()

for slots in range(0,100):
    
    graph = lazyflow.graph.Graph()
    opaw = OperatorWrapper(OpArrayCache, graph = graph)
    opbw = OperatorWrapper(OpA, graph = graph)
    
    opbw.input.connect(opaw.Output)
    
    array = numpy.ndarray((10,20), dtype = numpy.float32)
        
    t1 = time.time()
    opaw.Input.resize(slots)
    for s in range(slots):
        opaw.Input[s].setValue(array)
    t2 = time.time()    
    
    print slots, t2-t1
    results.append(t2-t1)

    print slots, gc.get_count()    

    t1 = time.time()
    gc.collect()
    t2 = time.time()
    
    print "GC", slots, t2-t1
    results_gc.append(t2-t1)
    
pyplot.title("Garbage collection time")
pyplot.xlabel("Number of lanes")    
pyplot.plot(results_gc)
pyplot.show()

pyplot.title("Setup time")    
pyplot.xlabel("Number of lanes")    
pyplot.plot(results)
pyplot.show()
    