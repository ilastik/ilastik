"""
This operator shifts the data(e.g an image) of an Input Slot in all dimensions,
but his time, an additional InputSlot for the shifting is used.
To make this operator work all InputSlots ahve to be connected with an OutputSlot
of another operator, e.g. vimageReader or a value has to be set. When all InputSlots
are connected or set to a value the notifyConnectAll method is called implicit. 
Here one can do different checkings and define the type, shape and axistags of 
the Output Slot of the operator. The calculation, here the shifting, is done in 
the getOutSlot method of the operator. This method again is called in an 
implicit way (see below)
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




class OpArrayShifter3(Operator):
    name = "OpArrayShifter3"
    description = "simple shifting operator in n dimensions"
    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output". In this example we create an additional InputSlot
    #for the shifting
    inputSlots = [InputSlot("Input"), InputSlot("Shift")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        #the value of inputs["Shift"].value, (the value of InputSlot("Shift))
        #which can be set freely, is saved in the property self.shift 
        self.shift = self.inputs["Shift"].value
         #define the type, shape and axistags of the Output-Slot    
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._axistags = inputSlot.axistags
        
        #check if inputSlot("Shift") provides the appropriate type and dimension 
        assert isinstance(self.shift, tuple), "OpArrayShifter: input'Shift' must have type tuple !"
        assert len(self.shift) == len(inputSlot.shape), "OpArrayShifter: number of dimensions of 'Shift' and 'Input' differs ! Shift:%d, Input:%d" %(len(self.shift), len(inputSlot.shape))


            
    #this method calculates the shifting          
    def getOutSlot(self, slot, key, result):
        
        #make shape of the input known
        shape = self.inputs["Input"].shape        
        #get N-D coordinate out of slice
        rstart, rstop = sliceToRoi(key, shape)    
      
        #shift the reading scope 
        rstart -=  self.shift
        rstop  -=  self.shift
         
        #calculate wrinting scope
        wstart = - numpy.minimum(rstart,rstart-rstart)
        wstop  = result.shape + numpy.minimum(numpy.array(shape)-rstop, rstop-rstop)
           
        #shifted rstart/rstop has to be in the original range (not out of range)
        #for shifts in both directions
        rstart = numpy.minimum(rstart,numpy.array(shape))
        rstart = numpy.maximum(rstart, rstart - rstart)
        rstop  = numpy.minimum(rstop,numpy.array(shape))
        rstop = numpy.maximum(rstop, rstop-rstop)
        
        #create slice out of the reading start and stop coordinates                
        rkey = roiToSlice(rstart,rstop)
        
        #create slice out of the reading start and stop coordinates                
        wkey = roiToSlice(wstart,wstop)
        
        #prefill result array with 0's
        result[:] = 0
        #write the shifted scope to the output 
        req = self.inputs["Input"][rkey].writeInto(result[wkey])
        res = req()
        return res

    def notifyDirty(selfut,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype


#create new Graphobject
g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

#create Image Reader       
vimageReader = OpImageReader(g)
#read an image 
vimageReader.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/tests/ostrich.jpg")

#create Shifter_Operator with Graph-Objekt as argument
shifter = OpArrayShifter3(g)

#set shifting
shifter.inputs["Shift"].setValue((10,-12,2))

#connect Shifter-Input with Image Reader Output
#because the Operator has only one Input Slot in this example,
#the "notifyConnectAll" method is executed
shifter.inputs["Input"].connect(vimageReader.outputs["Image"])

#shifter.outputs["Output"][:]returns an "GetItemWriterObject" object.
#its method "allocate" will be executed, this method call the "writeInto"
#method which calls the "fireRequest" method of the, in this case, 
#"OutputSlot" object which calls another method in "OutputSlot and finally
#the "getOutSlot" method of our operator.
#The wait() function blocks other activities and waits till the results
# of the requested Slot are calculated and stored in the result area.
shifter.outputs["Output"][:].allocate().wait()

#create Image Writer
vimageWriter = OpImageWriter(g)
#set writing path
vimageWriter.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/shift_result.jpg")
#connect Writer-Input with Shifter Operator-Output
vimageWriter.inputs["Image"].connect(shifter.outputs["Output"])

#write shifted image on disk
g.finalize()