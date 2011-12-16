#!/usr/bin/env python
#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)
import numpy
import argparse
import sys
import os.path as path
import h5py
import numpy as np
import volumina.api as vol
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators import OpBlockedArrayCache, OpArrayPiper, OpArrayCache

class OpH5StackReader5d( Operator ):
    name = "H5StackReader5d"
    description = "represent stack of h5 files as 5d array"
       
    inputSlots = [InputSlot('h5fns'), InputSlot('dataset')]
    outputSlots = [OutputSlot("array5d")]
    
    def notifyConnectAll(self):
        h5fns = self.inputs["h5fns"].value
        dataset_name = self.inputs["dataset"].value
        timesteps = len(h5fns)
        # probe one file
        shape3d = (1024,1024,1024)
        dtype = numpy.uint8
        self.inputs["h5fns"].shape = shape3d
        shape = (timesteps,) + shape3d + (1,) 
            
        self.outputs["array5d"]._dtype = dtype
        self.outputs["array5d"]._shape = shape
        # self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

    def getOutSlot(self, slot, key, result):
        fns = self.inputs["h5fns"].value
        assert key[-1] == slice(0,1,None)
        temporal = key[0]
        dataset_name = self.inputs["dataset"].value
        start = temporal.start if temporal.start else 0
        stop = temporal.stop if temporal.stop else len(fns)
        step = temporal.step if temporal.step else 1
        assert(step == 1)
        result[:] = np.random.randint(1, 255, result.shape)



if __name__=='__main__':

    graph = Graph()

    stack_reader = OpH5StackReader5d(graph)

    stack_reader.inputs["h5fns"].setValue("pups")
    stack_reader.inputs["dataset"].setValue("hamster" )

    array = OpArrayPiper(graph)

    fiver = vol.Op5ifyer(graph)
    fiver.inputs['Input'].connect(array.outputs["Output"])

    cache = OpBlockedArrayCache(graph)
    #cache = OpArrayCache(graph)
    outerShape = 256
    innerShape = 129
    cache.inputs['outerBlockShape'].setValue((1,outerShape, outerShape, outerShape,1))
    cache.inputs['innerBlockShape'].setValue((1,innerShape, innerShape, innerShape,1))
    #cache.inputs['blockShape'].setValue((1,64,64,64,1))
    cache.inputs['fixAtCurrent'].setValue(False)
    cache.inputs["Input"].connect(stack_reader.outputs['array5d'])

    
    cache.outputs["Output"][0,:,:,500,0].allocate().wait()

    import itertools, time



    requestSize = 128
    xCount = cache.outputs["Output"].shape[1] / requestSize
    yCount = cache.outputs["Output"].shape[2] / requestSize


    t1 = time.time()
    c = itertools.count()
    def notif(dest):
      v = c.next()
      if v == xCount*yCount-1:
        t2 = time.time()
        print "ASYNC TIME", (t2-t1)*1e3, "ms"
    


    xShape = cache.outputs["Output"].shape[1]
    yShape = cache.outputs["Output"].shape[2]

    requests = []
    for x in range(xCount):
      for y in range(yCount):
        r = cache.outputs["Output"][0,x*requestSize:min((x+1)*requestSize,xShape),y*requestSize:min((y+1)*requestSize,yShape),500,0].allocate()
        r.notify(notif)
        requests.append(r)


    for r in requests:
      r.wait()
    
    t1 = time.time()
    for x in range(xCount):
      for y in range(yCount):
        #r = cache.outputs["Output"][0,x*requestSize:min((x+1)*requestSize,xShape),y*requestSize:min((y+1)*requestSize,yShape),500,0].allocate()
        #r.wait()
        cache.getOutSlot(cache.outputs["Output"],(slice(0,1,None),slice(x*requestSize,min((x+1)*requestSize,xShape),None),slice(y*requestSize,min(yShape,(y+1)*requestSize),None),slice(500,501,None),slice(0,1,None)),numpy.ndarray((1,128,128,1,1),numpy.uint8))

    t2 = time.time()

    print "SYNC TIME", (t2-t1)*1e3, "ms"
    


