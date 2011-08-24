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

def Test1():
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    
    OpG = operators.OpPixelFeatures(g)
    
    inputImage = vigra.impex.readImage("../../tests/ostrich.jpg")
    
    #OpG.inputs["Input"].setValue(inputImage)
    OpG.inputs["Input"].setValue(numpy.random.rand(200,200,200).astype(numpy.float32))
    OpG.inputs["Matrix"].setValue([[1,1,0,0],[0,1,0,0],[0,1,0,0],[1,0,0,1]])
    OpG.inputs["Scales"].setValue([1,20,0.30,0.40])
    
    print OpG.outputs["Output"].shape
    
    dest1 = OpG.outputs["Output"][:,:,0:3].allocate().wait()
    dest2= OpG.outputs["Output"][:,:,3:6].allocate().wait()
    dest3 = OpG.outputs["Output"][:,:,6:9].allocate().wait()
    
    vigra.impex.writeImage(dest1,"resultOpG1.jpg") 
    vigra.impex.writeImage(dest2,"resultOpG2.jpg") 
    vigra.impex.writeImage(dest3,"resultOpG3.jpg") 
    
    
    
    #write shifted image on disk
    g.finalize()


def Test2():
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    
    OpG = operators.OpPixelFeatures(g)
    
    inputImage = vigra.impex.readImage("../../tests/ostrich.jpg")
    
    #OpG.inputs["Input"].setValue(inputImage)
    OpG.inputs["Input"].setValue(numpy.random.rand(60,60,60,10).astype(numpy.float32))
    OpG.inputs["Matrix"].setValue([[1,1,0,0],[0,1,0,0],[0,1,0,0],[1,0,0,1]])
    OpG.inputs["Scales"].setValue([1,.20,0.30,0.40])
    
    print OpG.outputs["Output"].shape
    
    dest1 = OpG.outputs["Output"][:,:,0,0:3].allocate().wait()
    dest2= OpG.outputs["Output"][:,:,0,3:6].allocate().wait()
    dest3 = OpG.outputs["Output"][:,:,0,6:9].allocate().wait()
    
    print "HERE"
    print dest1.shape
    print dest2.shape
    print dest3.shape
    
    dest1=numpy.squeeze(dest1)
    dest2=numpy.squeeze(dest2)
    dest3=numpy.squeeze(dest3)
    
    
    vigra.impex.writeImage(dest1,"resultOpG1.jpg") 
    vigra.impex.writeImage(dest2,"resultOpG2.jpg") 
    vigra.impex.writeImage(dest3,"resultOpG3.jpg") 
    
    
    
    #write shifted image on disk
    g.finalize()

def Test3():
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    
    OpG = operators.OpPixelFeatures(g)
    
    inputImage = vigra.impex.readImage("../../tests/ostrich.jpg")
    
    #OpG.inputs["Input"].setValue(inputImage)
    OpG.inputs["Input"].setValue(numpy.random.rand(60,60,60,10,1).astype(numpy.float32))
    OpG.inputs["Matrix"].setValue([[1,1,0,0],[0,1,0,0],[0,1,0,0],[1,0,0,1]])
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
    
    
    vigra.impex.writeImage(dest1,"resultOpG1.jpg") 
    vigra.impex.writeImage(dest2,"resultOpG2.jpg") 
    vigra.impex.writeImage(dest3,"resultOpG3.jpg") 
    
    
    
    #write shifted image on disk
    g.finalize()

def Test4():
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    
    OpG = operators.OpPixelFeatures(g)
    
    inputImage = vigra.impex.readImage("../../tests/ostrich.jpg")
    
    #OpG.inputs["Input"].setValue(inputImage)
    OpG.inputs["Input"].setValue(numpy.random.rand(60,60,60,10,10).astype(numpy.float32))
    OpG.inputs["Matrix"].setValue([[1,1,0,0],[0,1,0,0],[0,1,0,0],[1,0,0,1]])
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
    
    
    vigra.impex.writeImage(dest1,"resultOpG1.jpg") 
    vigra.impex.writeImage(dest2,"resultOpG2.jpg") 
    vigra.impex.writeImage(dest3,"resultOpG3.jpg") 
    
    
    
    #write shifted image on disk
    g.finalize()

Test1()
Test2()
Test3()
Test4()