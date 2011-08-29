import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *




class OpFlipArrayShifter(Operator):
    name = "OpFlipArrayShifter"
    description = "simple shifting operator in two dimensions with flipping"
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
        assert isinstance(self.shift, tuple), "OpFlipArrayShifter: input'Shift' must have type tuple !"
        assert len(self.shift) == len(inputSlot.shape), "OpFlipArrayShifter: number of dimensions of 'Shift' and 'Input' differs ! Shift:%d, Input:%d" %(len(self.shift), len(inputSlot.shape))
        shifted_axes = 0
        for i in self.shift:
            if i != 0:
                shifted_axes += 1
        assert shifted_axes<3, "Maximum two shfited axes!" 

            
    #this method calculates the shifting          
    def getOutSlot(self, slot, key, result):
        
        shape = self.inputs["Input"].shape   
        
        
        shifted_axes = 0
        for i in self.shift:
            if i != 0:
                shifted_axes += 1
        
        rstart, rstop = sliceToRoi(key, shape)
        ostart, ostop = sliceToRoi(key, shape)
 
        rstart -= self.shift
        rstop  -= self.shift      

        wstart = - numpy.minimum(rstart,rstart-rstart)
        wstop  = result.shape + numpy.minimum(numpy.array(shape)-rstop, rstop-rstop)        

        rstart = numpy.minimum(rstart,numpy.array(shape))
        rstart = numpy.maximum(rstart, rstart - rstart)
        rstop  = numpy.minimum(rstop,numpy.array(shape))
        rstop = numpy.maximum(rstop, rstop-rstop)

        result[:] = 0
        
        #dfrstart/dfrstop: start/stop reading coordinates of double flipped part
        dfrstart = rstart.copy()
        dfrstop  = rstop.copy()  
        #dfwstart/dfwstop: start/stop writing coordinates of double flipped part
        dfwstart = wstart.copy()
        dfwstop  = wstop.copy()
        
        for i in range(len(shape)):
           #frstart, frstop: start/stop reading coordinates of flipped part 
           frstart = rstart.copy()
           frstop = rstop.copy()
          
           if self.shift[i] < 0:
               frstart[i] = numpy.minimum(numpy.array(shape)[i] + self.shift[i] -(ostop[i]- numpy.array(shape)[i]),numpy.array(shape)[i] )
               frstop[i] = numpy.array(shape)[i] 
           elif self.shift[i] > 0:
               frstart[i] = rstart[i] 
               frstop[i] = numpy.maximum(frstart[i] + self.shift[i] - ostart[i], frstart[i])
           else:
               frstart[i] = rstart[i]
               frstop[i] = rstop[i]
               
             
           dfrstart[i] = frstart[i]
           dfrstop[i] = frstop[i]
           
           frkey = roiToSlice(frstart,frstop)
           
           flip = self.inputs["Input"][frkey].allocate().wait()
           flip = flip.swapaxes(0,i)[::-1].swapaxes(0,i)

           if self.shift[i] < 0:
               #fwstart, fwstop: start/stop writing coordinates of flipped part
               fwstart=wstart.copy()
               fwstop = wstop.copy()
               fwstart[i] = wstop[i] 
               fwstop[i] = numpy.array(result.shape)[i]  
               fwkey = roiToSlice(fwstart,fwstop)
               result[fwkey] = flip
               dfwstart[i] = fwstart[i]
               dfwstop[i]  = fwstop[i]
        
           elif self.shift[i] >0 :
               fwstart=wstart.copy()
               fwstop = wstop.copy()
               fwstart[i] = 0 
               fwstop[i] = wstart[i]
               fwkey = roiToSlice(fwstart,fwstop)
               result[fwkey] = flip
               dfwstart[i] = fwstart[i]
               dfwstop[i]  = fwstop[i] 
           else:
               dfwstart[i] = wstart[i]
               dfwstop[i]  = wstop[i] 
    
        if shifted_axes == 2:  
            
            dfrkey = roiToSlice(dfrstart,dfrstop)
            dflip = self.inputs["Input"][dfrkey].allocate().wait()
            for ax, sh in enumerate(self.shift):
                if sh !=0:
                    dflip = dflip.swapaxes(0,ax)[::-1].swapaxes(0,ax)
                    
            dfwkey = roiToSlice(dfwstart,dfwstop)
            result[dfwkey] = dflip
                                      
        rkey = roiToSlice(rstart,rstop)
               
        wkey = roiToSlice(wstart,wstop)
        
        res = self.inputs["Input"][rkey].allocate().wait()
        result[wkey] = res[:]
 

    def notifyDirty(selfut,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype

if __name__ == "__main__":
    #create new Graphobject
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    
    #create Image Reader       
    vimageReader = OpImageReader(g)
    #read an image 
    vimageReader.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/tests/ostrich.jpg")
    
    #create Shifter_Operator with Graph-Objekt as argument
    shifter = OpFlipArrayShifter(g)
    
    #set shifting
    shifter.inputs["Shift"].setValue((-200,200,0))
    
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
    res= shifter.outputs["Output"][30:300,120:340,0:3].allocate().wait()
    #write shifted image on disk
    vigra.impex.writeImage(res,"/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/shift_result.jpg") 
    
    g.finalize()