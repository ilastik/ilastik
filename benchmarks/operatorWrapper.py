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


class TimeIt(object):
    def __init__(self):
        self.t1 = 0
        self.t2 = 0
        
    def __enter__(self):
        self.t1 = time.time()
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.t2 = time.time()
        
    def time(self):
        return self.t2 - self.t1

results = []
results_gc = []

    
gc.disable()

for slots in range(0,100):
    
    graph = lazyflow.graph.Graph()
    opaw = OperatorWrapper(OpArrayCache, graph = graph)
    opbw = OperatorWrapper(OpA, graph = graph)
    
    opbw.input.connect(opaw.Output)
    
    array = numpy.ndarray((10,20), dtype = numpy.float32)
        
    time_resize = TimeIt()
    with time_resize:
        opaw.Input.resize(slots)
        for s in range(slots):
            opaw.Input[s].setValue(array)
    
    
    time_addlane = TimeIt()
    with time_addlane:
        for num_slots in range(1,slots):
            opaw.Input.resize(num_slots)
            opaw.Input[num_slots-1].setValue(array)
       
    
    results.append(time_resize.time())

    time_gc = TimeIt()
    with time_gc:
        gc.collect()
        
    print "slots: %d, time_resize=%2.2f, time_addlane=%2.2f, time_gc=%2.2f" % (slots, time_resize.time(), time_addlane.time(), time_gc.time())
    results_gc.append(time_gc.time())
    
pyplot.title("Garbage collection time")
pyplot.xlabel("Number of lanes")    
pyplot.plot(results_gc)
pyplot.show()

pyplot.title("Setup time")    
pyplot.xlabel("Number of lanes")    
pyplot.plot(results)
pyplot.show()
    