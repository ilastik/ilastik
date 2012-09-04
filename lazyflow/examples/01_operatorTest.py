import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *


#from lazyflow import operators

from OperatorCollection import *

import random
random.seed()
import pylab
z = 0



def arraySplitter(op,img,start,stop, requests, callback, sync):
    """
    op  - Operator, already connected
    img - empty output array
    start/stop - arrays with start/stop coordinates of img
    """

    global z

    dim = len(stop)

    #difference of start and stop
    diff = []
    for i in range(dim):
        diff.append(stop[i]-start[i])

    ld = diff.index(max(diff))

    #size of array
    size = 1
    for i in diff:
        size *= i

    #random maximum size
    bsize = random.randint(100,40000)

    #if size is small, operator is applied to partial array
    if size < bsize:
        for i in range(dim):
            start[i] = int(start[i]+0.5)
            stop[i] = int(stop[i]+0.5)

        #fire request
        req = op.outputs["Output"][roiToSlice(start,stop)].writeInto(img[roiToSlice(start,stop)])
        if sync:
            requests.append(req)
            res = req.wait()
            callback(res, start, stop)
        else:
            req.notify(callback, start = start, stop = stop)
            requests.append(req)
        return

    #split array up into p parts
    p =  random.randint(2,20)
    step = diff[ld]/float(p)
    start[ld] -= step
    for i in range(p):
        start[ld] += step
        stop[ld] = start[ld] + step
        arraySplitter(op,img,start[:],stop[:], requests, callback, sync)


imageCounter = 0

def operatorTest(operator_name, sync = False, cache = False):

    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

    #set up operators
    if operator_name == "OpArrayShifter1":
        op = OpArrayShifter1(g)
    elif operator_name == "OpImageResizer":
        op = OpImageResizer(g)
        op.inputs["ScaleFactor"].setValue(2)
    elif operator_name == "OpSubregion":
        op = OpSubregion(g)
        op.inputs["region_start"].setValue((100,100,0))
        op.inputs["region_stop"].setValue((300,300,3))
    elif operator_name == "OpSwapAxes":
        op = OpSwapAxes(g)
        op.inputs["Axis1"].setValue(0)
        op.inputs["Axis2"].setValue(1)
    elif operator_name == "OpArrayShifter2":
        op = OpArrayShifter2(g)
    elif operator_name == "OpArrayShifter3":
        op = OpArrayShifter3(g)
        op.inputs["Shift"].setValue((10,-12,0))
    else:
        print "Operatorname nicht bekannt!"

    def notify(result, start, stop):
        tempKey = roiToSlice(start, stop)
        imgP[tempKey] = result
        global imageCounter

        vigra.impex.writeImage(imgP,"./tt/result_%09d.jpg" % imageCounter )
        imageCounter +=1


    inputImage = vigra.impex.readImage("./tests/ostrich.jpg")
    op.inputs["Input"].setValue(inputImage)

    if cache:
        tempOp = operators.OpArrayCache(g)
        tempOp.inputs["Input"].connect(op.outputs["Output"])

        op = tempOp

    #fragmented image
    img1 = numpy.zeros(op.outputs["Output"].meta.shape , numpy.float32)

    start = []
    stop = []
    for i in range(img1.ndim):
        start.append(0)
        stop.append(numpy.array(img1.shape)[i])

    requests = []
    imgP = numpy.zeros(op.outputs["Output"].meta.shape , numpy.float32)

    arraySplitter(op,img1,start[:],stop[:], requests, notify, sync = sync)

    print "Length of requests", len(requests)
    for r in requests:
        r.wait()

    #full image
    img2 = op.outputs["Output"][:].allocate().wait()


    if (img2 == img1).all():
        print "_______________"
        print "Op works correctly"
        print "_______________"
    else:
        print "_______________"
        print "Op doesn't work correctly"
        print "_______________"

    vigra.impex.writeImage(img1,"./tt/result_fullImage.jpg")
    vigra.impex.writeImage(img2,"./tt/result_fragmentedImage.jpg" )


    g.finalize()

if __name__=="__main__":
    operatorTest("OpSwapAxes", sync = False, cache = False)
