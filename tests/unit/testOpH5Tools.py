from lazyflow.operators.ioOperators import OpH5Writer
from lazyflow.graph import Graph
import numpy
import os
import unittest
import h5py

class TestOpH5Writer(unittest.TestCase):
    
    def setUp(self,dimension = (5,20,20,20,5),testdirectory = './opWriterTest/',filename = 'writeTestFile.h5',hdf5path = 'volume/data'):
        
        self.dim = dimension
        self.testdir = testdirectory
        self.createTestVolume()
        self.filename = filename
        self.hdf5path = hdf5path
        
        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)

        g = Graph()
        self.writer = OpH5Writer(g)
        self.writer.inputs["filename"].setValue(self.testdir+self.filename)
        self.writer.inputs["hdf5Path"].setValue(self.hdf5path)
        self.writer.inputs["roi"].setValue(self.generateRoi())
        self.writer.inputs["dataType"].setValue('uint8')
        self.writer.inputs["blockShape"].setValue(5)
        self.writer.inputs["normalize"].setValue([-5,-17])

    def roiToShape(self,myRoi):
        return tuple([a-b for a,b in zip(myRoi[1],myRoi[0])])
        
    def createTestVolume(self,datatype='uint8'):
        
        self.volume = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2],self.dim[3],self.dim[4])*255
        self.volume = self.volume.astype(datatype)
    
    def generateRoi(self):
        shape = self.volume.shape
        k=[[0,0]]
        while len([x for x in k if not abs(x[0]-x[1])<=1]) < len(shape):
            k = [sorted([numpy.random.randint(dim),numpy.random.randint(dim)]) for dim in shape]
        k = [[x[0] for x in k],[x[1] for x in k]]
        return k
    
    def test_writeToFileBlockshapes(self):
        
        self.writer.inputs["input"].setValue(self.volume)
        for blockshape in [numpy.int(i*max(self.volume.shape)) for i in [0.1,0.2,0.5,1,1.5,2]]:
            self.writer.inputs["blockShape"].setValue(blockshape)
            self.writer.outputs["WriteImage"][:].allocate().wait()
        

    def test_writeToFileDataType(self):
        self.writer.inputs["input"].setValue(self.volume)
        for dataType in ['uint8','uint16','float64']:
            self.writer.inputs["dataType"].setValue(dataType)
            self.writer.outputs["WriteImage"][:].allocate().wait()
            f = h5py.File(self.testdir+self.filename,'r')
            assert f[self.hdf5path].dtype == dataType
            f.close()
            
            
    def test_writeToFileRoi(self):
        self.writer.inputs["input"].setValue(self.volume)
        for i in range(20):
            testRoi = self.generateRoi()
            self.writer.inputs["roi"].setValue(testRoi)
            self.writer.outputs["WriteImage"][:].allocate().wait()
            f = h5py.File(self.testdir+self.filename,'r')
            assert(self.roiToShape(testRoi)==f[self.hdf5path].shape)
            f.close()