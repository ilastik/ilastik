from lazyflow.operators import OpSparseLabelArray, OpBlockedSparseLabelArray
from lazyflow.graph import Graph
from lazyflow.roi import *
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
        key = (slice(min(x1, x2), max(x1, x2)), 0)
    if ndim==2:
        key = (slice(min(x1, x2), min(x1, x2)+1), slice(min(y1, y2), max(y1, y2)), 0)
    if ndim==3:
        key = (slice(min(x1, x2), max(x1, x2)), slice(min(y1, y2), shape[1]), slice(min(z1, z2), shape[2]), 0)

    return key

#def randomBlockKey(shape, blockshape):


def test(shape, blockshape):

    g = Graph()
    opLabel = OpSparseLabelArray(g)
    opLabelBlocked = OpBlockedSparseLabelArray(g)
    
    opLabel.inputs["shape"].setValue(shape[:-1] + (1,))
    opLabelBlocked.inputs["shape"].setValue(shape[:-1] + (1,))
    
    opLabelBlocked.inputs["blockShape"].setValue(blockshape)
    
    opLabel.inputs["eraser"].setValue(100)
    opLabelBlocked.inputs["eraser"].setValue(100)        
    
    niter = 100

    for i in range(niter):
        
        value = numpy.random.randint(1, 10)
        key = randomKey(shape[:-1])
        #key = (slice(0, 1, None), slice(4, 39, None), 0)
        #key = (slice(25, 49, None), slice(19, 50, None), slice(37, 50, None), 0)
        start, stop = sliceToRoi(key, shape)
        diff = stop - start        
        valueshape = diff[:-1]
        valuearray = numpy.zeros(tuple(valueshape), dtype = numpy.uint8)
        valuearray[:] = value 
        print i, key, valuearray.shape
        
        opLabel.setInSlot(opLabel.inputs["Input"], key, valuearray)
        opLabelBlocked.setInSlot(opLabelBlocked.inputs["Input"], key, valuearray)
        out = opLabel.outputs["Output"][:].allocate().wait()
        #print "first done"
        outblocked = opLabelBlocked.outputs["Output"][:].allocate().wait()
        #print "second done"
        assert_array_equal(out, outblocked)
        #print out
        #print outblocked
    
    nz1 = opLabel.outputs["nonzeroValues"][0].allocate().wait()
    
    nz2 = opLabelBlocked.outputs["nonzeroValues"][0].allocate().wait()

    for nz in nz1[0]:
        assert nz in nz2[0], "%r value not in blocked set"%nz
    
    for nz in nz2[0]:
        assert nz in nz1[0], "%r value not in non-blocked array"%nz
    
    print "done!"

def veryRandomTest(shape, blockshape):
    g = Graph()
    opLabel = OpSparseLabelArray(g)
    opLabelBlocked = OpBlockedSparseLabelArray(g)
    
    opLabel.inputs["shape"].setValue(shape[:-1] + (1,))
    opLabelBlocked.inputs["shape"].setValue(shape[:-1] + (1,))
    
    opLabelBlocked.inputs["blockShape"].setValue(blockshape)
    
    opLabel.inputs["eraser"].setValue(100)
    opLabelBlocked.inputs["eraser"].setValue(100)
    niter = 100

    for i in range(niter):
        
        value = numpy.random.randint(1, 10)
        key = randomKey(shape)
        #key = (slice(1, 41, None), slice(27, 50, None), slice(12, 50, None), 0)
        #key = (slice(7, 20, None), slice(7, 50, None), slice(35, 50, None), 0)
        start, stop = sliceToRoi(key, shape)
        diff = stop - start        
        valueshape = diff[:-1]
        valuearray = numpy.zeros(tuple(valueshape), dtype = numpy.uint8)
        valuearray[:] = value 
        
        opLabel.setInSlot(opLabel.inputs["Input"], key, valuearray)
        opLabelBlocked.setInSlot(opLabelBlocked.inputs["Input"], key, valuearray)
        
        key2 = randomKey(shape)
        #key2 = (slice(37, 49, None), slice(38, 50, None), slice(28, 50, None), 0)
        #key2 = (slice(7, 21, None), slice(21, 50, None), slice(10, 50, None))
        print i, key, key2
        out = opLabel.outputs["Output"][key2].allocate().wait()
        #print "first done"
        outblocked = opLabelBlocked.outputs["Output"][key2].allocate().wait()
        #print "second done"
        assert_array_equal(out, outblocked)
        #print out
        #print outblocked
    
    
def testBlocks(shape, blockshape):
    g = Graph()    
    opLabelBlocked = OpBlockedSparseLabelArray(g)
    opLabelBlocked.inputs["shape"].setValue(shape[:-1] + (1,))
    
    opLabelBlocked.inputs["blockShape"].setValue(blockshape)
    opLabelBlocked.inputs["eraser"].setValue(100)
    
    key = (slice(5, 15, None), slice(0, 10, None), 3, 3)
    value = numpy.zeros((10, 10, 1, 1), dtype=numpy.uint8)
    value[:] = 33
    
    opLabelBlocked.setInSlot(opLabelBlocked.inputs["Input"], key, value)
    
    blocklist = opLabelBlocked.outputs["nonzeroBlocks"][:].allocate().wait()
    print blocklist
    
    offset = numpy.array(shape[:-1])/numpy.array(blockshape[:-1])
    #offset = 0.5*step
    
    print offset
    nsteps = min(offset)
    for i in range(nsteps-1):
        start = offset + i*numpy.array(blockshape[:-1])
        stop = offset+(i+1)*numpy.array(blockshape[:-1])
        print start, stop
        key = roiToSlice(start, stop)
        print key
        valueshape = stop-start
        value = numpy.zeros(tuple(valueshape)+(1,), dtype=numpy.uint8)
        value[:] = 33
        newkey = [x for x in key]
        newkey.append(0)
        opLabelBlocked.setInSlot(opLabelBlocked.inputs["Input"], newkey, value)
        blocklist = opLabelBlocked.outputs["nonzeroBlocks"][:].allocate().wait()
        print blocklist
    
    
    
if __name__=="__main__":
    shape = (50, 50, 50, 1)
    blockshape = (10, 10, 10, 1)
    #test(shape, blockshape)
    #veryRandomTest(shape, blockshape)
    testBlocks(shape, blockshape)
    
