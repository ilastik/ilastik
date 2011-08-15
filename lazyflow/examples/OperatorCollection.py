import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *



class OpArrayShifter1(Operator):
    name = "OpArrayShifter1"
    description = "simple shifting operator"
    #change value for another shift
    shift = 50   
    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]    
    
    #this method is called when all InputSlot, in this example only one,
    #are connected with an OutputSlot or a value is set.
    def notifyConnectAll(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

    #this method calculates the shifting
    def getOutSlot(self, slot, key, result):
        
        #new name for the shape of the InputSlot
        shape =  self.inputs["Input"].shape     
        
        #get N-D coordinate out of slice
        ostart, ostop = sliceToRoi(key, shape)    
        #copy original array        
        rstart, rstop = ostart.copy(), ostop.copy()
      
        #shift the reading scope
        #change value '-2' for shifting another dimension
        rstart[-2] -=  self.shift
        rstop[-2]  -=  self.shift
        
        #calculate wrinting scope
        wstart = - numpy.minimum(rstart,rstart-rstart)
        wstop  = result.shape + numpy.minimum(numpy.array(shape)-rstop, rstop-rstop)
        
        #shifted rstart/rstop has to be in the original range (not out of range)
        #for shifts in both directions
        rstart = numpy.minimum(rstart,numpy.array(shape))
        rstart = numpy.maximum(rstart, rstart - rstart)
        rstop  = numpy.minimum(rstop,numpy.array(shape))
        rstop  = numpy.maximum(rstop, rstop-rstop)
        
        #create slice out of the reading start and stop coordinates                
        rkey = roiToSlice(rstart,rstop)       
        
        #create slice out of the reading start and stop coordinates                
        wkey = roiToSlice(wstart,wstop)
        
        #preallocate result array with 0's
        result[:] = 0
        
        #write the shifted scope to the output 
        #self.inputs["Input"][rkey] returns an "GetItemWriterObject" object
        #its method "writeInto" will be called, which will call the 
        #"fireRequest" method of the, in this case, the Input-Slot,
        #which will return an "GetItemRequestObject" object. While this
        #object will be creating the "putTask" method of the graph object 
        #will be called
        req = self.inputs["Input"][rkey].writeInto(result[wkey])
        res = req()
        return res

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype
        
        
        
class OpArrayShifter2(Operator):
    name = "OpArrayShifter2"
    description = "simple shifting operator in n dimensions"
    #change values for other shifts
    shift = ([50,60,0,0,0,9678,76])
    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input")]
    outputSlots = [OutputSlot("Output")]   
    
    def notifyConnectAll(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)        
 
        #calculating diffrence between input dimension and shift dimension
        diffShift = numpy.array(self.shift).size - numpy.array(self.shape).size
        if diffShift<0:
            #fill missing shift dimensions with zeros
            self.shift = numpy.hstack((self.shift,numpy.zeros(abs(diffShift))))
        elif diffShift>0:
            #cut the shift vector to the appropriate dimension
            self.shift = self.shift[0:numpy.array(self.shape).size]
            
    #this method calculates the shifting           
    def getOutSlot(self, slot, key, result):
        
        #make shape of the input known
        shape = self.inputs["Input"].shape
        #get N-D coordinate out of slice
        ostart, ostop = sliceToRoi(key, shape)    
        #copy original array        
        rstart, rstop = ostart.copy(), ostop.copy()
      
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
        #self.inputs["Input"][rkey] returns an "GetItemWriterObject" object
        #its method "writeInto" will be called, which will call the 
        #"fireRequest" method of the, in this case, the Input-Slot,
        #which will return an "GetItemRequestObject" object. While this
        #object will be creating the "putTask" method of the graph object 
        #will be called
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
        ostart, ostop = sliceToRoi(key, shape)    
        #copy original array        
        rstart, rstop = ostart.copy(), ostop.copy()
      
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
        

class OpImageResizer(Operator):
    name = "OpImageResizer"
    description = "Resizes an Image using Spline Interpolation "
 
    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input"), InputSlot("ScaleFactor")]
    outputSlots = [OutputSlot("Output")]    
    
    #this method is called when all InputSlots, 
    #are set or connected with an OutputSlot or a value is set.
    def notifyConnectAll(self):

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
        
        print "Start/Stop"
        print start
        print stop
        print "________"
        
        #additional edge, necessary for the SplineInterpolation to work properly
        edge = 3        
        
        #calculate reading start and stop coordinates(of InputSlot)
        rstart = numpy.maximum(start / self.scaleFactor - edge * self.scaleFactor, start-start )
        rstart[-1] = start[-1] # do not enlarge channel dimension
        rstop = numpy.minimum(stop / self.scaleFactor + edge * self.scaleFactor, self.inputs["Input"].shape)
        rstop[-1] = stop[-1]# do not enlarge channel dimension
        #create reading key        
        rkey = roiToSlice(rstart,rstop)
        
        #get the data of the InputSlot
        img = numpy.ndarray(rstop-rstart,dtype=self.dtype)
        img = self.inputs["Input"][rkey].allocate().wait()
         
        #create result array
        tmp_result = numpy.ndarray(tuple(numpy.hstack(((rstop-rstart)[:-1] * self.scaleFactor, (rstop-rstart)[-1]))), dtype=numpy.float32)
     
        #apply SplineInterpolation
        res = vigra.sampling.resizeImageSplineInterpolation(image = img.astype(numpy.float32), out = tmp_result)
              
        #calculate correction for interpolated edge
        corr = numpy.maximum(numpy.minimum(start / self.scaleFactor - edge * self.scaleFactor, start-start ) , - edge * self.scaleFactor)        
        print "corr", corr

        #calculate SubKey for interpolated array without interpolated edge
        subStart = (edge*self.scaleFactor+corr)*self.scaleFactor
        subStart[-1] = start[-1]
        subStop = numpy.minimum(stop - start + subStart, res.shape)
        subStop[-1] = stop[-1]
        
        subKey = roiToSlice(subStart, subStop)
        
        print "rstart/rstop"
        print "rstart", rstart
        print "rstop", rstop
        print "__________"
        print "Subkey", subKey
        print subStart
        print subStop
        print "________"
        print "result", result.shape
        print "res", res.shape
        print "res[subKey].shape", res[subKey].shape       
        
        #write rescaled image into result
        result[:] = res[subKey]
        

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype
        
        
class OpSwapAxes(Operator):
    name = "OpSwapAxes"
    description = "swaps the axes of two InputSlots"

    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input"),InputSlot("Axis1"), InputSlot("Axis2")]
    outputSlots = [OutputSlot("Output")]    
    
    #this method is called when all InputSlot, in this example three,
    #are connected with an OutputSlot or a value is set.
    def notifyConnectAll(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        
        axis1 = self.inputs["Axis1"].value
        axis2 = self.inputs["Axis2"].value
         
        #calculate the output shape 
        output_shape = numpy.array(inputSlot.shape)
        a = output_shape[axis1]
        output_shape[axis1] = output_shape[axis2]
        output_shape[axis2] = a    

        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = output_shape
        self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

    #this method does the swapping
    def getOutSlot(self, slot, key, result):
        
        axis1 = self.inputs["Axis1"].value
        axis2 = self.inputs["Axis2"].value        
        
        #get start and stop coordinates        
        start, stop = sliceToRoi(key, self.shape)
        
        #calculate new reading key
        a = start[axis1]
        start[axis1] = start[axis2]
        start[axis2] = a
        a = stop[axis1]
        stop[axis1] = stop[axis2]
        stop[axis2] = a
        skey = roiToSlice(start,stop)
        
        #get data of the Inputslot
        img = self.inputs["Input"][skey].allocate().wait()
         
        
        #write swapped image into result array
        result[:] = img.swapaxes(axis1, axis2)

        

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype
        
        
        
class OpSubregion(Operator):
    name = "OpSubregion"
    description = "simple subregion operator"

    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input"),InputSlot("region_start"), InputSlot("region_stop")]
    outputSlots = [OutputSlot("Output")]    
    
    #this method is called when all InputSlot, in this example three,
    #are connected with an OutputSlot or a value is set.
    def notifyConnectAll(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        
        start = numpy.array(self.inputs["region_start"].value)
        stop = numpy.array(self.inputs["region_stop"].value)
               
        assert (stop>=start).all()
        assert (stop <= numpy.array(self.inputs["Input"].shape )).all()
        assert (start >= start - start).all()

        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"]._dtype = inputSlot.dtype
        self.outputs["Output"]._shape = tuple(stop - start)
        self.outputs["Output"]._axistags = copy.copy(inputSlot.axistags)

    #this method calculates the shifting
    def getOutSlot(self, slot, key, result):

        #subregion start and stop        
        start = self.inputs["region_start"].value         
        stop = self.inputs["region_stop"].value
         
        #get start and stop coordinates
        ostart, ostop = sliceToRoi(key, self.shape)
        #calculate the new reading start and stop coordinates 
        rstart = start + ostart
        rstop  = start + ostop
        #create reading key
        rkey = roiToSlice(rstart,rstop)
        
        #write the subregion to the output 
        #self.inputs["Input"][key] returns an "GetItemWriterObject" object
        #its method "writeInto" will be called, which will call the 
        #"fireRequest" method of the, in this case, the Input-Slot,
        #which will return an "GetItemRequestObject" object. While this
        #object will be creating the "putTask" method of the graph object 
        #will be called
        req = self.inputs["Input"][rkey].writeInto(result)   
        res = req()
        return res

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape
    
    @property
    def dtype(self):
        return self.outputs["Output"]._dtype
