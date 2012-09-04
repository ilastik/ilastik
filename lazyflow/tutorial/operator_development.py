#===============================================================================
# Operator base class documentation
#===============================================================================

import vigra, numpy, copy
from imshow import imshow
from lazyflow.roi import sliceToRoi, roiToSlice

if 1==2:
    class Operator(object):
        """
        The base class for all Operators.

        Operators consist of a class inheriting from this class
        and need to specify their inputs and outputs via
        thei inputSlot and outputSlot class properties.

        Each instance of an operator obtains individual
        copies of the inputSlots and outputSlots, which are
        available in the self.inputs and self.outputs instance
        properties.

        these instance properties can be used to connect
        the inputs and outputs of different operators.

        Example:
            operator1.inputs["InputA"].connect(operator2.outputs["OutputC"])


        Different examples for simple operators are provided
        in an example directory. plese read through the
        examples to learn how to implement your own operators...
        """

        #definition of inputs slots
        inputSlots  = []

        #definition of output slots -> operators instances
        outputSlots = []
        name = ""
        description = ""



        """
        This method is called when an output of another operator on which
        this operators dependds, i.e. to which it is connected gets invalid.
        The region of interest of the inputslot which is now dirty is specified
        in the key property, the input slot which got dirty is specified in the inputSlot
        property.

        This method must calculate what output ports and which subregions of them are
        invalidated by this, and must call the .setDirty(key) of the corresponding
        outputslots.
        """
        def notifyDirty(self, inputSlot, key):
            pass

        """
        This method corresponds to the notifyDirty method, but is used
        for multidimensional inputslots, which contain subslots.

        The slots argument is a list of slots in which the first
        element specifies the mainslot (i.e. the slot which is specified
        in the operator.). The next element specifies the sub slot, i.e. the
        child of the main slot, and so forth.

        The indexes argument is a list of the subslot indexes. As such it is
        of lenght n-1 where n is the length of the slots arugment list.
        It contains the indexes of all subslots realtive to their parent slot.

        The key argument specifies the region of interest.
        """
        def notifySubSlotDirty(self, slots, indexes, key):
            pass

        """
        This method is called opon connection of all inputslots of
        an operator.

        The operator should setup the output all outputslots accordingly.
        this includes setting their shape and axistags properties.
        """
        def setupOutputs(self):
            pass


        """
        This method corresponds to the notifyConnect method, but is used
        for multidimensional inputslots, which contain subslots.

        The slots argument is a list of slots in which the first
        element specifies the mainslot (i.e. the slot which is specified
        in the operator.). The next element specifies the sub slot, i.e. the
        child of the main slot, and so forth.

        The indexes argument is a list of the subslot indexes. As such it is
        of lenght n-1 where n is the length of the slots arugment list.
        It contains the indexes of all subslots realtive to their parent slot.

        The key argument specifies the region of interest.
        """
        def notifySubConnect(self, slots, indexes):
            pass


        """
        This method is called when a subslot of a multidimensional inputslot
        is removed.

        The slots argument is a list of slots in which the first
        element specifies the mainslot (i.e. the slot which is specified
        in the operator.). The next element specifies the sub slot, i.e. the
        child of the main slot, and so forth.

        The indexes argument is a list of the subslot indexes. As such it is
        of lenght n-1 where n is the length of the slots arugment list.
        It contains the indexes of all subslots realtive to their parent slot.

        The operator should recalculate the shapes of its output slots
        when neccessary.
        """
        def notifySubSlotRemove(self, slots, indexes):
            pass


        """
        This method of the operator is called when a connected operator
        or an outside user of the graph wants to retrieve the calculation results
        from the operator.

        The slot which is requested is specified in the slot arguemt,
        the region of interest is specified in the key property.
        The result area into which the calculation results MUST be written is
        specified in the result argument. "result" is an numpy.ndarray that
        has the same shape as the region of interest(key).

        The method must retrieve all required inputs that are neccessary to
        calculate the requested output area from its input slots,
        run the calculation and put the results into the provided result argument.
        """
        def getOutSlot(self, slot, key, result):
            pass


        """
        This method corresponds to the getOutSlot method, but is used
        for multidimensional inputslots, which contain subslots.

        The slots argument is a list of slots in which the first
        element specifies the mainslot (i.e. the slot which is specified
        in the operator.). The next element specifies the sub slot, i.e. the
        child of the main slot, and so forth.

        The indexes argument is a list of the subslot indexes. As such it is
        of lenght n-1 where n is the length of the slots arugment list.
        It contains the indexes of all subslots realtive to their parent slot.

        The key argument specifies the region of interest.
        """
        def getSubOutSlot(self, slots, indexes, key, result):
            return None


        """
        This method is called when an inputslot is disconnected.

        The slot argument specifies the inputslot that is affected.

        The operator should recalculate the shapes of its output slots
        when neccessary..
        """
        def notifyDisconnect(self, slot):
            pass


        """
        This method corresponds to the notifyDisconnect method, but is used
        for multidimensional inputslots, which contain subslots.

        The slots argument is a list of slots in which the first
        element specifies the mainslot (i.e. the slot which is specified
        in the operator.). The next element specifies the sub slot, i.e. the
        child of the main slot, and so forth.

        The indexes argument is a list of the subslot indexes. As such it is
        of lenght n-1 where n is the length of the slots arugment list.
        It contains the indexes of all subslots realtive to their parent slot.

        The key argument specifies the region of interest.
        """
        def notifySubDisconnect(self, slots, indexes):
            pass



#===============================================================================
# Implementing an Operator
#===============================================================================

# First whe import the neccessary lazyflow modules
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot



# next we define a class that inherits from the Operator base class
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
    def setupOutputs(self):
        #new name for the InputSlot("Input")
        inputSlot = self.inputs["Input"]
        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"].meta.dtype = inputSlot.meta.dtype
        self.outputs["Output"].meta.shape = inputSlot.meta.shape
        self.outputs["Output"].meta.axistags = copy.copy(inputSlot.meta.axistags)

    #this method calculates the shifting
    def getOutSlot(self, slot, key, result):

        #new name for the shape of the InputSlot
        shape =  self.inputs["Input"].meta.shape

        #get N-D coordinate out of slice
        rstart, rstop = sliceToRoi(key, shape)

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
        res = req.wait()
        return res

    def notifyDirty(self,slot,key):
        self.outputs["Output"].setDirty(key)


from lazyflow import operators

# create graph
g = Graph()
# construct image reader
reader = operators.OpImageReader(g)
reader.inputs["Filename"].setValue("ostrich.jpg")
# create Shifter_Operator with Graph-Objekt as argument
shifter = OpArrayShifter1(g)

# connect Shifter-Input with Image Reader Output
# because the Operator has only one Input Slot in this example,
# the "setupOutputs" method is executed
shifter.inputs["Input"].connect(reader.outputs["Image"])

# shifter.outputs["Output"][:]returns an "GetItemWriterObject" object.
# its method "allocate" will be executed, this method call the "writeInto"
# method which calls the "fireRequest" method of the, in this case,
# "OutputSlot" object which calls another method in "OutputSlot and finally
# the "getOutSlot" method of our operator.
# The wait() function blocks other activities and waits till the results
# of the requested Slot are calculated and stored in the result area.
result=shifter.outputs["Output"][:].allocate().wait()

# display the result
imshow(result)
