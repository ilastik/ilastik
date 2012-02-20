from lazyflow.operators import OpH5Writer
from lazyflow.graph import Graph
import numpy
import os

class OpH5WriterTest():
    
    def __init__(self,dimension = (5,20,20,20,5),testdirectory = './opWriterTest/',filename = 'writeTestFile.h5',hdf5path = 'volume/data',):
        
        self.dim = dimension
        self.testdir = testdirectory
        
        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)

        g = Graph()
        self.writer = OpH5Writer(g)
        self.writer.inputs["Filename"].setValue(self.testdir+filename)
        self.writer.inputs["hdf5Path"].setValue(hdf5path)


    def createTestVolume(self,datatype='uint8'):
        
        self.volume = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2],self.dim[3],self.dim[4])*255
        self.volume = self.volume.astype(datatype)
    
    def writeToFile(self,blockshape = 5):
        
        self.writer.inputs["Image"].setValue(self.volume)
        self.writer.inputs["blockShape"].setValue(blockshape)
        print self.writer.outputs["WriteImage"][:].allocate().wait()
        
if __name__ == "__main__":
    
    testclass = OpH5WriterTest()    
    testclass.createTestVolume()
    testclass.writeToFile()