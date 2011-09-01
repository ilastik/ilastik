import vigra
import threading
from lazyflow.graph import *
import copy

from lazyflow.operators.operators import OpArrayPiper 
from lazyflow.operators.vigraOperators import *
from lazyflow.operators.valueProviders import *
from lazyflow.operators.classifierOperators import *
from lazyflow.operators.generic import *

from lazyflow import operators
    
        
def test1():
             
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
    

    Op = operators.OpBlockedArrayCache(g)
    
    inputImage = vigra.impex.readImage("ostrich.jpg")

    opPiper = OpArrayPiper(g)
    opPiper.inputs["Input"].setValue(inputImage)
    
    Op.inputs["Input"].connect(opPiper.outputs["Output"])
    
    maxi = 10
    maxj = 10

    for i in range(maxi):
        start = numpy.array([random.randint(0,399), random.randint(0,399), 0])
        stop = numpy.array([random.randint(start[0]+1,400), random.randint(start[1]+1,400), 3])
        for j in range(maxj):
            z = maxj*i+j

            key = roiToSlice(start, stop)  
            shape = (random.randint(1,400), random.randint(1,400), 3)                      
            
            Op.inputs["outerBlockShape"].setValue(shape)
            Op.inputs["fixAtCurrent"].setValue(False)
            Op.inputs["innerBlockShape"].setValue(64)
            dest = Op.outputs["Output"][key].allocate().wait()
            assert (numpy.array(dest.shape) == numpy.array(stop -start)).all()
            
            vigra.impex.writeImage(dest,"r_%09d.jpg"  %z) 

  
    
    g.finalize()


def arraySplitter(op,img,start,stop, requests, callback, sync):
    """
    op  - Operator, already connected
    img - empty output array
    start/stop - arrays with start/stop coordinates of img
    """
    
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
     



def operatorTest(blockShape, sync = False, cache = False):
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)
  

    op = operators.OpBlockedArrayCache(g)
    inputImage = vigra.impex.readImage("ostrich.jpg")
    op.inputs["Input"].setValue(inputImage)
    op.inputs["outerBlockShape"].setValue(blockShape)
    op.inputs["fixAtCurrent"].setValue(False)
    op.inputs["innerBlockShape"].setValue(64)
       
    def notify(result, start, stop):
        tempKey = roiToSlice(start, stop)
        imgP[tempKey] = result
        #global imageCounter
        #vigra.impex.writeImage(imgP,"/net/gorgonzola/storage/cripp/lazyflow/lazyflow/examples/tt/result_%09d.jpg" % imageCounter ) 
        #imageCounter +=1          
 
    if cache:
        tempOp = OpArrayCache(g)
        tempOp.inputs["Input"].connect(op.outputs["Output"])
    
        op = tempOp    
    
    #fragmented image
    img1 = numpy.zeros(op.outputs["Output"]._shape , numpy.float32)

    start = []
    stop = []
    for i in range(img1.ndim):
        start.append(0)
        stop.append(numpy.array(img1.shape)[i])

    requests = []   
    imgP = numpy.zeros(op.outputs["Output"]._shape , numpy.float32)     

    arraySplitter(op,img1,start[:],stop[:], requests, notify, sync = sync)
      
    for r in requests:
        r.wait()

    #full image
    img2 = op.outputs["Output"][:].allocate().wait()


    assert (img2 == img1).all(),  "Op doesn't work correctly"

    print "__________________"
    print "Op works correctly"
    print "__________________"
    
    vigra.impex.writeImage(img1,"result_fullImage.jpg")     
    vigra.impex.writeImage(img2,"result_fragmentedImage.jpg" )     

    
    g.finalize()




if __name__=="__main__":   
    
    import random
    random.seed()


    test1()
     
    #imageCounter = 0

    for i in range(5):
        print "______", i , "______"
        blockShape = (random.randint(1,400), random.randint(1,400), 3) 
        operatorTest(blockShape, False, False)

    for i in range(5):
        print "______", i , "______"
        blockShape = (random.randint(1,400), random.randint(1,400), 3) 
        operatorTest(blockShape, True, False)       
        
    for i in range(5):
        print "______", i , "______"
        blockShape = (random.randint(1,400), random.randint(1,400), 3) 
        operatorTest(blockShape, False, True)
        
    for i in range(5):
        print "______", i , "______"
        blockShape = (random.randint(1,400), random.randint(1,400), 3) 
        operatorTest(blockShape, True, True)