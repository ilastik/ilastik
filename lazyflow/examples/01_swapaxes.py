"""
This operator swaps two axes of the InputSlot.
To make this operator work one has to connect the InputSlot("Input") with an
OutputSlot of another operator, e.g. vimageReader and set values for the
InputSlots("Axis1") and ("Axis2"), defining the two axes to swap.
When all the InputSlots of the operator are connected or set, the
"setupOutputs" method is called implicit. Here one can do different checkings
and define the type, shape and axistags of the Output Slot of the operator.
"""


import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.roi import roiToSlice
from lazyflow.operators.operators import OpArrayPiper
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *



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
    def setupOutputs(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]

        axis1 = self.inputs["Axis1"].value
        axis2 = self.inputs["Axis2"].value

        #calculate the output shape
        output_shape = numpy.array(inputSlot.meta.shape)
        a = output_shape[axis1]
        output_shape[axis1] = output_shape[axis2]
        output_shape[axis2] = a

        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"].meta.dtype = inputSlot.meta.dtype
        self.outputs["Output"].meta.shape = output_shape
        self.outputs["Output"].meta.axistags = copy.copy(inputSlot.meta.axistags)

    #this method does the swapping
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)

        axis1 = self.inputs["Axis1"].value
        axis2 = self.inputs["Axis2"].value

        #get start and stop coordinates
        start, stop = sliceToRoi(key, slot.meta.shape)

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



    def propagateDirty(self, slot, subindex, roi):
        key = roi.toSlice()
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"].meta.shape

    @property
    def dtype(self):
        return self.outputs["Output"].meta.dtype

if __name__=="__main__":
    #create new Graphobject
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

    #create ImageReader-Operator
    vimageReader = OpImageReader(g)
    #read an image
    vimageReader.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/tests/ostrich.jpg")

    #create SwapAxes_Operator with Graph-Objekt as argument
    swapaxes = OpSwapAxes(g)

    #connect SwapAxes-Input with Image Reader Output
    swapaxes.inputs["Input"].connect(vimageReader.outputs["Image"])
    #set values for the InputSlots, after this, the "setupOutputs" method is executed
    #because now all the InputSlot are set or connected
    swapaxes.inputs["Axis1"].setValue(0)
    swapaxes.inputs["Axis2"].setValue(1)

    #swapaxes.outputs["Output"][:]returns an "GetItemWriterObject" object.
    #its method "allocate" will be executed, this method call the "writeInto"
    #method which calls the "fireRequest" method of the, in this case,
    #"OutputSlot" object which calls another method in "OutputSlot and finally
    #the "execute" method of our operator.
    #The wait() function blocks other activities and waits till the results
    # of the requested Slot are calculated and stored in the result area.
    swapaxes.outputs["Output"][:].allocate().wait()

    #create Image Writer
    vimageWriter = OpImageWriter(g)
    #set writing path
    vimageWriter.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/swapaxes_result.jpg")
    #connect Writer-Input with SwapAxes Operator-Output
    vimageWriter.inputs["Image"].connect(swapaxes.outputs["Output"])

    #write image on disk
    g.finalize()
