"""
This operator returns a subregion of the Input Slot.
To make this operator work one has to connect the InputSlot("Input") with an
OutputSlot of another operator, e.g. vimageReader and set values for the
InputSlots("region_start") and ("region_stop"). When all InputSlots of an
operator are connected or set, the "notifyConnectAll" method is called implicit.
Here one can do different checkings (e.g. verfying that the element-wise values of
region_stop are greater than region_start) and define the type, shape and axistags
of the Output Slot of the operator.
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
        res = req.wait()
        return res

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)

    @property
    def shape(self):
        return self.outputs["Output"]._shape

    @property
    def dtype(self):
        return self.outputs["Output"]._dtype

if __name__=="__main__":
    #create new Graphobject
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

    #create ImageReader-Operator
    vimageReader = OpImageReader(g)
    #read an image
    vimageReader.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/tests/ostrich.jpg")

    #create Subregion_Operator with Graph-Objekt as argument
    subregion = OpSubregion(g)

    #connect Subregion-Input with Image Reader Output
    subregion.inputs["Input"].connect(vimageReader.outputs["Image"])
    #set values for the InputSlots, after this, the "notifyConnectAll" method is executed
    #because now all the InputSlot are set or connected
    subregion.inputs["region_start"].setValue((100,100,0))
    subregion.inputs["region_stop"].setValue((300,300,3))

    #subregion.outputs["Output"][:]returns an "GetItemWriterObject" object.
    #its method "allocate" will be executed, this method call the "writeInto"
    #method which calls the "fireRequest" method of the, in this case,
    #"OutputSlot" object which calls another method in "OutputSlot and finally
    #the "getOutSlot" method of our operator.
    #The wait() function blocks other activities and waits till the results
    # of the requested Slot are calculated and stored in the result area.
    subregion.outputs["Output"][:].allocate().wait()

    #create Image Writer
    vimageWriter = OpImageWriter(g)
    #set writing path
    vimageWriter.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/subregion_result.jpg")
    #connect Writer-Input with Subregion Operator-Output
    vimageWriter.inputs["Image"].connect(subregion.outputs["Output"])

    #write image on disk
    g.finalize()
