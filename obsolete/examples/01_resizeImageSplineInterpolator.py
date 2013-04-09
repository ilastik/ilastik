"""
This operator scales the data(e.g an image) of an Input Slot.
To make this operator work one has to connect the InputSlot("Input") with an
Output Slot of another operator, e.g. vimageReader and set a value for the
InputSlot("ScaleFactor"). When all Input Slots of an operator are connected or set,
the setupOutputs method is called implicit. Here one can do different
checkings and define the type, shape and axistags of the Output Slot of the operator.
The scaling is done in the execute method of the operator.
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
    name = "OpImageResizer"
    description = "Resizes an Image using Spline Interpolation "

    #create Input and Output Slots (objects) of the operator
    #the different InputSlots and OutputSlot are saved in the dictionaries
    #"inputs" and "output"
    inputSlots = [InputSlot("Input"), InputSlot("ScaleFactor")]
    outputSlots = [OutputSlot("Output")]

    #this method is called when all InputSlots,
    #are set or connected with an OutputSlot or a value is set.
    def setupOutputs(self):

        inputSlot = self.inputs["Input"]
        self.scaleFactor = self.inputs["ScaleFactor"].value
        shape =  self.inputs["Input"].meta.shape

        #define the type, shape and axistags of the Output-Slot
        self.outputs["Output"].meta.dtype = inputSlot.meta.dtype
        self.outputs["Output"].meta.shape = tuple(numpy.hstack(((numpy.array(shape))[:-1] * self.scaleFactor, (numpy.array(shape))[-1])))
        self.outputs["Output"].meta.axistags = copy.copy(inputSlot.meta.axistags)

        assert self.scaleFactor > 0, "OpImageResizer: input'ScaleFactor' must be positive number !"

    #this method does the scaling
    def execute(self, slot, subindex, roi, result):
        key = roiToSlice(roi.start,roi.stop)

        #get start and stop coordinates of the requested OutputSlot area
        start, stop = sliceToRoi(key, slot.meta.shape)

        #additional edge, necessary for the SplineInterpolation to work properly
        edge = 3

        #calculate reading start and stop coordinates(of InputSlot)
        rstart = numpy.maximum(start / self.scaleFactor - edge * self.scaleFactor, start-start )
        rstart[-1] = start[-1] # do not enlarge channel dimension
        rstop = numpy.minimum(stop / self.scaleFactor + edge * self.scaleFactor, self.inputs["Input"].meta.shape)
        rstop[-1] = stop[-1]# do not enlarge channel dimension
        #create reading key
        rkey = roiToSlice(rstart,rstop)

        #get the data of the InputSlot
        img = numpy.ndarray(rstop-rstart,dtype=self.dtype)
        img = self.inputs["Input"][rkey].meta.wait()

        #create result array
        tmp_result = numpy.ndarray(tuple(numpy.hstack(((rstop-rstart)[:-1] * self.scaleFactor, (rstop-rstart)[-1]))), dtype=numpy.float32)

        #apply SplineInterpolation
        res = vigra.sampling.resizeImageSplineInterpolation(image = img.astype(numpy.float32), out = tmp_result)

        #calculate correction for interpolated edge
        corr = numpy.maximum(numpy.minimum(start / self.scaleFactor - edge * self.scaleFactor, start-start ) , - edge * self.scaleFactor)

        #calculate SubKey for interpolated array without interpolated edge
        subStart = (edge*self.scaleFactor+corr)*self.scaleFactor
        subStart[-1] = start[-1]
        subStop = numpy.minimum(stop - start + subStart, res.shape)
        subStop[-1] = stop[-1]

        subKey = roiToSlice(subStart, subStop)

        #write rescaled image into result
        result[:] = res[subKey]


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
    vimageReader = OpImageReader(graph=g)
    #read an image
    vimageReader.inputs["Filename"].setValue("/net/gorgonzola/storage/cripp/lazyflow/tests/ostrich.jpg")

    #create Resizer-Operator with Graph-Objekt as argument
    resizer = OpImageResizer(graph=g)

    #set ScaleFactor
    resizer.inputs["ScaleFactor"].setValue(2)

    #connect Resizer-Input with Image Reader Output
    #because now all the InputSlot are set or connected,
    #the "setupOutputs" method is executed
    resizer.inputs["Input"].connect(vimageReader.outputs["Image"])

    #resizer.outputs["Output"][:]returns an "GetItemWriterObject" object.
    #its method "allocate" will be executed, this method call the "writeInto"
    #method which calls the "fireRequest" method of the, in this case,
    #"OutputSlot" object which calls another method in "OutputSlot and finally
    #the "execute" method of our operator.
    #The wait() function blocks other activities and waits till the results
    # of the requested Slot are calculated and stored in the result area.

    dest = resizer.outputs["Output"][17:99,10:99,:].wait()
    #dest = resizer.outputs["Output"][:].wait()
    #write Image
    vigra.impex.writeImage(dest,"/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/resize_result_2.jpg")
    #write resized image on disk
    g.finalize()
