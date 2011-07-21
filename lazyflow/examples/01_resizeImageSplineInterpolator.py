"""
This operator scales the data(e.g an image) of an Input Slot. 
To make this operator work one has to connect the InputSlot("Input") with an 
Output Slot of another operator, e.g. vimageReader and set a value for the 
InputSlot("ScaleFactor"). When all Input Slots of an operator are connected or set,
the notifyConnectAll method is called implicit. Here one can do different
checkings and define the type, shape and axistags of the Output Slot of the operator.
The scaling is done in the getOutSlot method of the operator.
This method again is called in an implicit way (see below)
"""


import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *



class OpImageResizer(Operator):
    name = "ResizeImageSplineInterpolation"
    description = "Resizes an Image using Spline Interpolation "
 
    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input"), InputSlot("ScaleFactor")]
    outputSlots = [OutputSlot("Output")]    
    
    #this method is called when all InputSlots, 
    #are set or connected with an OutputSlot or a value is set.
    def notifyConnectAll(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        
        self.scaleFactor = self.inputs["ScaleFactor"].value        
      
        shape =  self.inputs["Input"].shape
        
        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = tuple(numpy.hstack(((numpy.array(shape))[:-1] * self.scaleFactor, (numpy.array(shape))[-1])))
        self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

        assert self.scaleFactor > 0, "OpImageResizer: input'ScaleFactor' must be positive number !"

    #this method does the scaling
    def getOutSlot(self, slot, key, result):
        
        #get start and stop coordinates of the requested OutputSlot area
        start, stop = sliceToRoi(key, self.shape) 
        
        #calculate reading start and stop coordinates(of InputSlot)
        rstart = numpy.hstack((start[:-1] / self.scaleFactor, start[-1]))
        rstop = numpy.hstack((stop[:-1] / self.scaleFactor, stop[-1]))
        #create reading key        
        rkey = roiToSlice(rstart,rstop)
        
        #get the data of the InputSlot
        img = numpy.ndarray(rstop-rstart,dtype=self.dtype)
        img = self.inputs["Input"][rkey].allocate().wait()
        
        img = vigra.Image(img) 
        
        res = vigra.Image(result)        
    
        #for the scaling a vigra function is used        
        vigra.sampling.resizeImageSplineInterpolation(image = img, out = res)
        
        #write rescaled image into result
        result[:] = res
        

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype

#create new Graphobject
g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

#create ImageReader-Operator      
vimageReader = OpImageReader(g)
#read an image 
vimageReader.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/tests/ostrich.jpg")

#create Resizer-Operator with Graph-Objekt as argument
resizer = OpImageResizer(g)

#set ScaleFactor
resizer.inputs["ScaleFactor"].setValue(0.25)

#connect Resizer-Input with Image Reader Output
#because now all the InputSlot are set or connected,
#the "notifyConnectAll" method is executed
resizer.inputs["Input"].connect(vimageReader.outputs["Image"])

#resizer.outputs["Output"][:]returns an "GetItemWriterObject" object.
#its method "allocate" will be executed, this method call the "writeInto"
#method which calls the "fireRequest" method of the, in this case, 
#"OutputSlot" object which calls another method in "OutputSlot and finally
#the "getOutSlot" method of our operator.
#The wait() function blocks other activities and waits till the results
# of the requested Slot are calculated and stored in the result area.
resizer.outputs["Output"][25:75,20:80,:].allocate().wait()

#create Image Writer
vimageWriter = OpImageWriter(g)
#set writing path
vimageWriter.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/resize_result.jpg")
#connect Writer-Input with Resizer Operator-Output
vimageWriter.inputs["Image"].connect(resizer.outputs["Output"])

#write resized image on disk
g.finalize()