import vigra
import numpy
from lazyflow import operators
from lazyflow.graph import *
from numpy.testing import *
from connected_comp import OpThreshold, OpConnectedComponents

def testThreshold():
    #generate a dummy prob. map
    pred = numpy.zeros((10, 10, 4))
    pred[0:5, 0:5, 0] = 0.6
    pred[0:5, 5:, 1] = 0.6
    pred[5:, 0:5, 2] = 0.7
    pred[5:, 5:, 3] = 0.8
    
    g = Graph()
    opTh = OpThreshold(g)
    opTh.inputs["Input"].setValue(pred)
    opTh.inputs["Threshold"].setValue(0.55)
    
    opTh.inputs["Channel"].setValue(0)
    res = opTh.outputs["Output"][:].allocate().wait()
    desired = numpy.zeros((10, 10, 1))
    desired[0:5, 0:5, 0] = 1
    assert_array_equal(res, desired)
    
    opTh.inputs["Channel"].setValue(1)
    res = opTh.outputs["Output"][:].allocate().wait()
    desired = numpy.zeros((10, 10, 1))
    desired[0:5, 5:, 0] = 1
    assert_array_equal(res, desired)
    
    opTh.inputs["Threshold"].setValue(0.65)
    res = opTh.outputs["Output"][:].allocate().wait()
    assert_array_equal(res, numpy.zeros((10, 10, 1)))
    print "done!"
    
def testCC():
    
    pred = numpy.zeros((1, 10, 10, 10, 2), dtype = numpy.uint8)
    predva = vigra.VigraArray(pred, axistags = vigra.defaultAxistags(5))
    predva.axistags.swapaxes(0, 3)
    predva.axistags.swapaxes(1, 3)
    predva.axistags.swapaxes(2, 3)
    
    predva[0, 0:5, 0:5, 0, 0] = 1
    predva[0, 7:8, 7:8, 0, 0] = 1
    predva[0, 0:5, 0:5, 0, 1] = 1
    
    
    g = Graph()
    opCC = OpConnectedComponents(g)
    opCC.inputs["Input"].setValue(predva)
    opCC.inputs["Neighborhood"].setValue(26)
    opCC.inputs["Background"].setValue(0)
    
    res = opCC.outputs["Output"][:].allocate().wait()
    
    
    desired = numpy.zeros((1, 10, 10, 10, 2), dtype=numpy.uint8)
    desired[0, 0:5, 0:5, 0, 0] = 1
    desired[0, 7:8, 7:8, 0, 0] = 2
    desired[0, 0:5, 0:5, 0, 1] = 1
    assert_array_equal(res, desired)
    print "done!"
    
    
    
    #opCC.inputs["Background"].setValue(-1)
    #res = opCC.outputs["Output"][:].allocate().wait()
    #desired = numpy.ones((10, 10), dtype = numpy.uint8)
    #desired[:] = 2
    #desired[0:5, 0:5] = 1
    #desired[7:8, 7:8] = 3
    #assert_array_equal(res, desired)
    
    
if __name__ == "__main__":
    #testThreshold()
    testCC()