import vigra, numpy
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.helpers import generateRandomKeys
import glob,os
from unittest.case import TestCase
from shutil import rmtree
from lazyflow.operators.ioOperators import OpStackLoader

            

class testOpStackLoader(TestCase):
    
    def __init__(self,dim = (60,80,500,3), keys = 20, testdir = "./stackLoaderTest/"):
        
        self.dim = dim
        self.keys = keys
        self.testdir = testdir
                
    def createImages(self):
        
        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)
        self.block = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2],self.dim[3])*255
        self.block = self.block.astype('uint8')
        for i in range(self.dim[2]):
            vigra.impex.writeImage(self.block[:,:,i,:],self.testdir+"%04d.png" % (i))
     
    def stackAndTestFull(self,filetype = "png"):
        
        g = Graph()
        loader = OpStackLoader(g)
        loader.inputs["globstring"].setValue(self.testdir+"/*."+filetype)
        result = loader.outputs["stack"][:].allocate().wait()
        
        if  not (result == self.block).all():
            raise RuntimeError('test failed')

    
    def stackAndTestKey(self):
        
        g = Graph()
        loader = OpStackLoader(g)
        loader.inputs["globstring"].setValue(self.testdir+"*.png")
        
        for i in range(self.keys):
            key = generateRandomKeys(self.dim)
            result = loader.outputs["stack"][key].allocate().wait()
            if  not (result == self.block[key]).all():
                raise RuntimeError('test failed')
    
    
    def clear(self):
        
        if os.path.exists(self.testdir):
            rmtree(self.testdir)
        

tester = testOpStackLoader()
tester.createImages()
tester.stackAndTestKey()
tester.clear()
