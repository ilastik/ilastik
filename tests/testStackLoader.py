#===============================================================================
# Operator base class documentation
#===============================================================================

import vigra, numpy, copy
from imshow import imshow
from lazyflow.roi import sliceToRoi, roiToSlice

#===============================================================================
# Implementing an Operator
#===============================================================================

# First whe import the neccessary lazyflow modules
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot


from lazyflow import operators
import glob,os

class OpStackLoader(Operator):
    name = "Image Reader"
    category = "Input"
    
    inputSlots = [InputSlot("Globstring", stype = "string")]
    outputSlots = [OutputSlot("Stack")]
    
    def notifyConnectAll(self):
        globString = self.inputs["Globstring"].value
        self.fileNameList = (glob.glob(globString))
        self.fileNameList.sort()

        if len(self.fileNameList) != 0:
            self.info = vigra.impex.ImageInfo(self.fileNameList[0])
            oslot = self.outputs["Stack"]
            
            #build 3D shape out of 2dShape and Filelist
            oslot._shape = (self.info.getShape()[0],self.info.getShape()[1],len(self.fileNameList))
            oslot._dtype = self.info.getDtype()
            oslot._axistags = self.info.getAxisTags()
            
        else:
            oslot = self.outputs["Image"]
            oslot._shape = None
            oslot._dtype = None
            oslot._axistags = None
            
    def getOutSlot(self, slot, key, result):
        
        fileList = []
        
        for i in range(len(self.fileNameList))[key[2]]:
            fileList.append(vigra.impex.readImage(self.fileNameList[i]))
        
        print key
        
        template = numpy.zeros((self.info.getShape()[0],self.info.getShape()[1],1))
        temp = template[key[0],key[1],:]
        
        for aFile in fileList:
            
            aFile3D = numpy.zeros_like(template)
            aFile3D[:,:,0] = aFile[:,:,0]
            temp = numpy.concatenate((temp,aFile3D[key[0],key[1],:]),2)
            
        result[:,:,:] = temp[:,:,1:]

class testOpStackLoader(object):
    
    def __init__(self,dim = (10,20,30), keys = 5, testdir = "./stackLoaderTest/"):
        
        self.dim = dim
        self.keys = keys
        self.testdir = testdir
        if not os.path.exists(self.testdir):
            print "creating directory '%s'" % (self.testdir)
            os.mkdir(self.testdir)
        
    def createImages(self):
        
        self.block = numpy.random.rand(self.dim[0],self.dim[1],self.dim[2])*255
        self.block = self.block.astype('uint8')
        for i in range(self.dim[2]):
            vigra.impex.writeImage(self.block[:,:,i],self.testdir+"%04d.png" % (i))
     
    def stackAndTestFull(self):
        
        g = Graph()
        loader = OpStackLoader(g)
        loader.inputs["Globstring"].setValue(self.testdir+"*.png")
        result = loader.outputs["Stack"][:].allocate().wait()
        
        if (result == self.block).all():
            print "The Sky is clear tonight"
    
    def stackAndTestKey(self):
        
        g = Graph()
        loader = OpStackLoader(g)
        loader.inputs["Globstring"].setValue(self.testdir+"*.png")
        
        for i in range(self.keys):
            key = self.makeKey()
            result = loader.outputs["Stack"][key].allocate().wait()
            if (result == self.block[key]).all():
                print "The Sky is clear tonight with key Nr. %d" % (i)
        
    
    def makeKey(self):
        
        tmp = numpy.random.rand(6)
        tmpslice1 =[numpy.round(tmp[0]*self.dim[0]),numpy.round(tmp[1]*self.dim[0])]
        tmpslice1.sort()
        tmpslice2 =[numpy.round(tmp[2]*self.dim[1]),numpy.round(tmp[3]*self.dim[1])]
        tmpslice2.sort()
        tmpslice3 =[numpy.round(tmp[4]*self.dim[2]),numpy.round(tmp[5]*self.dim[2])]
        tmpslice3.sort()
        slice1 = slice(int(tmpslice1[0]),int(tmpslice1[1]),1)
        slice2 = slice(int(tmpslice2[0]),int(tmpslice2[1]),1)
        slice3 = slice(int(tmpslice3[0]),int(tmpslice3[1]),1)
        key = (slice1,slice2,slice3)
        return key
    
    def clear(self):
        
        if os.path.exists(self.testdir):
            print "deleting directory '%s'" % (self.testdir)
            for aFile in os.listdir(self.testdir):
                try:
                    os.remove(self.testdir+aFile)
                except Exception, e:
                    print e
            os.removedirs(self.testdir) 

tester = testOpStackLoader(dim=(40,40,50),keys=10)
tester.createImages()
tester.stackAndTestKey()
tester.clear()
