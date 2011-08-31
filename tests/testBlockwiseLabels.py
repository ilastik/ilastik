from lazyflow.operators import OpSparseLabelArray, OpBlockedSparseLabelArray
from lazyflow.graph import Graph
import numpy
from numpy.testing import *


def randomKey(shape):
    
    ndim = len(shape)-1
    x1 = numpy.random.randint(0, shape[0])
    x2 = numpy.random.randint(0, shape[0])
    if x1==x2:
        x1 = x2-1 if x2!=0 else x2+1
    if ndim>1:
        y1 = numpy.random.randint(0, shape[1])
        y2 = numpy.random.randint(0, shape[1])
        if y1==y2:
            y1 = y2-1 if y2!=0 else y2+1
    if ndim>2:
        z1 = numpy.random.randint(0, shape[2])
        z2 = numpy.random.randint(0, shape[2])
        if z1==z2:
            z1 = z2-1 if z2!=0 else z2+1
    
    key = None
    if ndim==1:
        key = (slice(min(x1, x2), max(x1, x2)), slice(0, 1, None))
    if ndim==2:
        key = (slice(min(x1, x2), max(x1, x2)), slice(min(y1, y2), max(y1, y2)), slice(0, 1, None))
    if ndim==3:
        key = (slice(min(x1, x2), max(x1, x2)), slice(min(y1, y2), max(y1, y2)), slice(min(z1, z2), max(z1, z2)), slice(0, 1, None))

    return key

def test(shape, blockshape):

    g = Graph()
    opLabel = OpSparseLabelArray(g)
    opLabelBlocked = OpBlockedSparseLabelArray(g)
    
    opLabel.inputs["shape"].setValue(shape[:-1] + (1,))
    opLabelBlocked.inputs["shape"].setValue(shape[:-1] + (1,))
    
    opLabelBlocked.inputs["blockShape"].setValue(blockshape)
    
    opLabel.inputs["eraser"].setValue(100)
    opLabelBlocked.inputs["eraser"].setValue(100)        
    
    niter = 10
    
    for i in range(niter):

        
        value = numpy.random.randint(0, 10)
        key = randomKey(shape)
        print i, key
        opLabel.setInSlot(opLabel.inputs["Input"], key, value)
        opLabelBlocked.setInSlot(opLabelBlocked.inputs["Input"], key, value)
        out = opLabel.outputs["Output"][:].allocate().wait()
        #print "first done"
        outblocked = opLabelBlocked.outputs["Output"][:].allocate().wait()
        #print "second done"
        assert_array_equal(out, outblocked)
        #print out
        #print outblocked
    
    print "done!"


if __name__=="__main__":
    shape = (50, 50, 50, 1)
    blockshape = (10, 10, 2, 1)
    test(shape, blockshape)
    