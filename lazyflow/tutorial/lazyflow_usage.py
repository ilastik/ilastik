#    To use the lazyflow graph you must import
#    the neccessary python modules

from lazyflow.graph import Graph
from lazyflow import operators

from imshow import imshow
import numpy, vigra


#    The first thing you want to do is instantiating a new
#    lazyflow processing graph
#
#    If you need you can specify the number of threads
#    and the maximal memory usage for caches (in bytes) that lazyflow
#    should use:
#        g = Graph(numThreads = 8, softMaxMem = 16*1024**3)
#    if you do not specify these values lazyflow will use
#     reasonable defaults, which we will use here:

g = Graph()



#    Next we add a simple image reader operator to the graph
#    to have some data to play with
#
#    All operators must receive as first argument
#    the graph to which they will belong

reader = operators.OpImageReader(g)

#    To configure the image reader operator we
#    must provide a filename.
#    Operators receive the inputs or arguments
#    via their input slots.
#    You can list the inputslots of operators in ipython
#    by looking at their "inputs" attribute, e.g.:
#
#        print reader.inputs
#
#    will show a list of the inputslots the operator supports,
#    the image reader has only one input slot called "Filename",
#    to set a value we just call

reader.inputs["Filename"].setValue("ostrich.jpg")

#    Different operators of the graph are connected by connecting
#    their respective inputs and outputs, to demonstrate this
#    we will add another operator that that just copies
#    its inputs to its outputs


noOp = operators.OpArrayPiper(g)

noOp.inputs["Input"].connect(reader.outputs["Image"])


#    To read the outputs of ouperators, i.e. the results
#    of their calculations you have to provide the region
#    of interest, i.e. if you want
#   to retrieve a subregion :

rw = noOp.outputs["Output"][50:150,50:150,0:3]

#    or if you prefer to retrieve the full result

rw = noOp.outputs["Output"][:]



#    contrary to what you might expect the result
#    of this operation is not a numpy array, but a so
#    so called GetItemWriterObject, which supports
#    specifiying where to store the results of your request.
#    To do this you have to call:
#
#        rw.writeInto(destination_area)
#
#   Where destination_area must be a numpy ndarray of
#   appropriate shape.
#
#   If you do not care where the results should be written
#   the GetItemWriterObject supports a convencience function
#   which allocates an numpy array of appropriate shape:
#
#        rw.allocate()
#
#   We will use this convenience function for now:


req = rw.allocate()


#    contrary to what you might expect the result
#    of this operation is still not an numpy array, but
#    this time a so called GetItemRequestObject.
#    This object encapsulates all neccessary information
#    and is just waiting to be executed.
#    It is up to you to decide wether you want to execute
#    the request immediately:
#
#       result = req.wait()
#
#    Which will run the request and return the result array
#    that rw.allocate() has allocated.
#    Or, you can schedule the request for background execution
#    and provide a function that should be called once
#    the request is finished:
#
#       result = req.notify(callback)
#
#    The callback function that you have to provide receives
#    as first argument the result array. (To learn more read
#    the documentation of the GetItemRequestObject)
#
#    we will use a mere sychronous request for now:


result = req.wait()

#   To visualize the result of our graph processing pipeline
#   we will use a small image viewer helper:


imshow(result)

#    finally, we allso want to make sure that the noOp, which
#    is in fact an OpArrayPiper, does not change the image of
#    the image reader .
#    While doing so we will introduce you to the
#    call chaining syntax you may use when retrieving results
#    of operator outputs:

result2 = reader.outputs["Image"][:].allocate().wait()


#    this combines all previous operations into
#    one line.

imshow(result2)



#    it should be noted that operators can freely
#    define the shape of their output, one exmple
#    of an operator that changes the size of the inputs
#    on the output side is the OpSubRegion operator
#    which selects a subwindow of its input

subwin = operators.OpSubRegion(g)
subwin.inputs["Input"].connect(reader.outputs["Image"])

#    next we define the subwindow which it should select:

subwin.inputs["Start"].setValue((100,100,0))
subwin.inputs["Stop"].setValue((200,200,3))


#    when displaying the result of this operator
#    your will observe that selecting the
#    complete results [:] will return a smaller portion of
#    the image:

result3 = subwin.outputs["Output"][:].allocate().wait()
imshow(result3)


#    you can inspect the shape of an output slot by
#    printing its shape property:

print "reader.outputs[\"Image\"].shape :", reader.outputs["Image"].shape
print "subwin.outputs[\"Output\"].shape :", subwin.outputs["Output"].shape


#    in addition output slots have some other useful properties as
#    .dtype and .axistags

print "reader.outputs[\"Image\"].shape :", reader.outputs["Image"].shape
print "reader.outputs[\"Image\"].dtype :", reader.outputs["Image"].dtype
print "reader.outputs[\"Image\"].axistags :", reader.outputs["Image"].axistags
