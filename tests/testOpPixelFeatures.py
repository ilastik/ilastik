import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *
from lazyflow import operators
import numpy
import sys,signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


def test_OpPixelFeatures__T1():
    
    print "________________________________"
    print "__TEST: test_OpPixelFeatures__T1__"
    print "_____________"
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    OpG = operators.OpPixelFeatures(g)
    
    inputImage = vigra.impex.readImage("ostrich.jpg")
    
    OpG.inputs["Input"].setValue(inputImage)
    OpG.inputs["Scales"].setValue([1,20,30,40])

    aMatrix = numpy.array([[0,1,0,1],[0,0,0,0],[0,1,0,0],[0,1,0,0]])

    OpG.inputs["Matrix"].setValue(aMatrix)


    dest1 = OpG.outputs["Output"][:,:,0:3].allocate().wait()
    dest2= OpG.outputs["Output"][:,:,3:6].allocate().wait()
    dest3 = OpG.outputs["Output"][:,:,6:9].allocate().wait()
 
    vigra.impex.writeImage(dest1,"F2_T1_resultOpT1G1.jpg") 
    vigra.impex.writeImage(dest2,"F2_T1_resultOpT1G2.jpg") 
    vigra.impex.writeImage(dest3,"F2_T1_resultOpT1G3.jpg")
    
    print "Shape 1"
    print OpG.outputs["Output"].shape
    print "_________"
    
    shape1 = OpG.outputs["Output"].shape 
  
    OpG.inputs["Matrix"].setValue(numpy.array([[1,1,0,0],[0,1,1,0],[1,0,1,0],[1,0,0,1]]))   
   
    import gc
    del dest1
    del dest2
    del dest3
    gc.collect()  

    dest1 = OpG.outputs["Output"][:,:,0:3].allocate().wait()
    dest2= OpG.outputs["Output"][:,:,3:6].allocate().wait()
    dest3 = OpG.outputs["Output"][:,:,6:9].allocate().wait()
    
    vigra.impex.writeImage(dest1,"F2_T1_resultOpT2G1.jpg") 
    vigra.impex.writeImage(dest2,"F2_T1_resultOpT2G2.jpg") 
    vigra.impex.writeImage(dest3,"F2_T1_resultOpT2G3.jpg")
    
    print "Shape 2"
    print OpG.outputs["Output"].shape    
    print "_________"


    OpG.inputs["Matrix"].setValue(aMatrix)
    
    
    del dest1
    del dest2
    del dest3
    gc.collect()    

    dest1 = OpG.outputs["Output"][:,:,0:3].allocate().wait()
    dest2=  OpG.outputs["Output"][:,:,3:6].allocate().wait()
    dest3 = OpG.outputs["Output"][:,:,6:9].allocate().wait()

    vigra.impex.writeImage(dest1,"F2_T1_resultOpT3G1.jpg") 
    vigra.impex.writeImage(dest2,"F2_T1_resultOpT3G2.jpg") 
    vigra.impex.writeImage(dest3,"F2_T1_resultOpT3G3.jpg")
    
    print "Shape 3"
    print OpG.outputs["Output"].shape    
    print "_________"    
    
    
    shape3 = OpG.outputs["Output"].shape     
    
    if shape3 != shape1:
        print "ERROR!!!!!!"

    print "______________________"

    g.finalize()
    
    
def test_OpPixelFeatures__T2():
    
    print "________________________________"
    print "__TEST: test_OpPixelFeatures__T2__"
    print "_____________"    
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    

    OpG = operators.OpPixelFeatures(g)
    
    inputImage = vigra.impex.readImage("ostrich.jpg")

    OpG.inputs["Input"].setValue(numpy.random.rand(60,60,60,10,10).astype(numpy.float32))
    OpG.inputs["Matrix"].setValue(numpy.array([[1,1,0,0],[0,1,0,0],[0,1,0,0],[1,0,0,1]]))
    OpG.inputs["Scales"].setValue([1,.20,0.30,0.40])
    
    print OpG.outputs["Output"].shape
    
    dest1 = OpG.outputs["Output"][:,:,0,0,0:3].allocate().wait()
    dest2= OpG.outputs["Output"][:,:,0,0,3:6].allocate().wait()
    dest3 = OpG.outputs["Output"][:,:,0,0,6:9].allocate().wait()
    
    print "HERE"
    print dest1.shape
    print dest2.shape
    print dest3.shape
    
    dest1=numpy.squeeze(dest1)
    dest2=numpy.squeeze(dest2)
    dest3=numpy.squeeze(dest3)
    
    
    vigra.impex.writeImage(dest1,"F2_T2_resultOpG1.jpg") 
    vigra.impex.writeImage(dest2,"F2_T2_resultOpG2.jpg") 
    vigra.impex.writeImage(dest3,"F2_T2_resultOpG3.jpg") 
    
    print "______________________"    
    
    g.finalize()


test_OpPixelFeatures__T1()
test_OpPixelFeatures__T2()