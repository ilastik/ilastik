import vigra, numpy
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
import glob,os
from unittest.case import TestCase
from shutil import rmtree
from lazyflow.operators.vigraOperators import OpStackLoader


            

class testOpStackLoader(TestCase):
    
    def __init__(self,dim = (60,80,3,500), keys = 20, testdir = "./stackLoaderTest/"):
        
        self.dim = dim
        self.keys = keys
        self.testdir = testdir
                
    def createImages(self):
        
        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)
        self.block = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2],self.dim[3])*255
        self.block = self.block.astype('uint8')
        for i in range(self.dim[3]):
            vigra.impex.writeImage(self.block[:,:,:,i],self.testdir+"%04d.png" % (i))
     
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
            key = self.makeKey()
            result = loader.outputs["stack"][key].allocate().wait()
            if  not (result == self.block[key]).all():
                raise RuntimeError('test failed')
    
    def makeKey(self):
        
        tmp = numpy.zeros((4,2))
        
        while tmp[0,0] == tmp[0,1] or tmp[1,0] == tmp[1,1] or tmp[2,0] == tmp[2,1]\
        or tmp[3,0] == tmp[3,1]:
            
            tmp = numpy.random.rand(4,2)
            for i in range(4):
                tmp[i,:] *= self.dim[i]
                tmp[i,:] = numpy.sort(numpy.round(tmp[i,:]))
        
        key = []
        for i in range(4):
            key.append(slice(int(tmp[i,0]),int(tmp[i,1]),1))
        
        return key

    def clear(self):
        
        if os.path.exists(self.testdir):
            rmtree(self.testdir)
        

tester = testOpStackLoader()
tester.createImages()
tester.stackAndTestKey()
tester.clear()