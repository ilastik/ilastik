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


import random
random.seed()
import pylab
      
        

#def arraySplitter(op,img,start,stop, requests, callback, sync):
#    """
#    op  - Operator, already connected
#    img - empty output array
#    start/stop - arrays with start/stop coordinates of img
#    """
#   
#    dim = len(stop)
#    
#    #difference of start and stop
#    diff = []
#    for i in range(dim):
#        diff.append(stop[i]-start[i])
#        
#    ld = diff.index(max(diff))    
#   
#    #size of array
#    size = 1
#    for i in diff:
#        size *= i
#    
#    #random maximum size
#    bsize = random.randint(100,40)        
#
#    #if size is small, operator is applied to partial array
#    if size < bsize:
#        for i in range(dim):
#            start[i] = int(start[i]+0.5)
#            stop[i] = int(stop[i]+0.5)
#        
#        #fire request
#        req = op.outputs["Output"][roiToSlice(start,stop)].writeInto(img[roiToSlice(start,stop)])
#        if sync:
#            requests.append(req)
#            res = req.wait()
#            callback(res, start, stop)
#        else:        
#            req.notify(callback, start = start, stop = stop)
#            requests.append(req)
#        return
#    
#    #split array up into p parts
#    p =  random.randint(2,10)
#    step = diff[ld]/float(p)
#    start[ld] -= step
#    for i in range(p):
#        start[ld] += step
#        stop[ld] = start[ld] + step
#        arraySplitter(op,img,start[:],stop[:], requests, callback, sync)
#     
#
#def operatorTest(op, sync = False, cache = False):
#    
#       
#    def notify(result, start, stop):
#        tempKey = roiToSlice(start, stop)
#        imgP[tempKey] = result
#
#   
#    if cache:
#        tempOp = operators.OpArrayCache(g)
#        tempOp.inputs["Input"].connect(op.outputs["Output"])
#    
#        op = tempOp    
#    
#    #fragmented image
#    img1 = numpy.zeros(op.outputs["Output"]._shape , numpy.float32)
#
#    start = []
#    stop = []
#    for i in range(img1.ndim):
#        start.append(0)
#        stop.append(numpy.array(img1.shape)[i])
#
#    requests = []        
#    imgP = numpy.zeros(op.outputs["Output"]._shape , numpy.float32)    
#    
#    arraySplitter(op,img1,start[:],stop[:], requests, notify, sync = sync)
#      
#    print "Length of requests", len(requests)
#    for r in requests:
#        r.wait()
#
#    #full image
#    img2 = op.outputs["Output"][:].allocate().wait()
#
#    
#    if (img2 == img1).all():
#        print "_______________"
#        print "Op works correctly"
#        print "_______________"
#    else:
#        print "_______________"
#        print "Op doesn't work correctly"
#        print "_______________" 
#  
#    g.finalize()




if __name__=="__main__":
    
    s = [20,600,20,30,10]    
    img = numpy.ndarray((s[0],s[1],s[2],s[3],s[4]), dtype = float)
     
    axisKey = []
    for i in range(97,123):
        axisKey.append(chr(i))
    
    axisType = []
    axisType.append(vigra.AxisType.Time)        
    axisType.append(vigra.AxisType.Space)
    axisType.append(vigra.AxisType.Channels)
    #axisType.append(vigra.AxisType.Frequency)
    #axisType.append(vigra.AxisType.Angle)

    axisDescription = []
    axisDescription.append("Cat")
    axisDescription.append("Lion")
    axisDescription.append("Bird")
    axisDescription.append("Shark")
    axisDescription.append("Dog")
    axisDescription.append("Snake")
    axisDescription.append("Spider")
    
    import random
    random.seed() 

    axis = []

#    for i in range(5):
#        key = axisKey[random.randint(0,len(axisKey)-1)]
#        axisKey.remove(key)
#        typeFlags = axisType[random.randint(0,len(axisType)-1)]
#        if typeFlags == vigra.AxisType.Channels or typeFlags == vigra.AxisType.Time:
#            axisType.remove(typeFlags)
#        description = axisDescription[random.randint(0,len(axisDescription)-1)]
#        axis.append(vigra.AxisInfo(key = key, typeFlags = typeFlags, resolution = 0.0, description = description))
    
    info = []    
    info.append(vigra.AxisInfo(key = "x", typeFlags = vigra.AxisType.Space , resolution = 0.0, description = "Lion"))
    info.append(vigra.AxisInfo(key = "y", typeFlags = vigra.AxisType.Space , resolution = 0.0, description = "Bird"))
    info.append(vigra.AxisInfo(key = "z", typeFlags = vigra.AxisType.Space , resolution = 0.0, description = "Shark"))
    info.append(vigra.AxisInfo(key = "t", typeFlags = vigra.AxisType.Time , resolution = 0.0, description = "Cat"))
    info.append(vigra.AxisInfo(key = "c", typeFlags = vigra.AxisType.Channels , resolution = 0.0, description = "Tiger"))
    
    for i in range(5):
        inf = info[random.randint(0,len(info)-1)]
        axis.append(inf)
        info.remove(inf)
    
#    axis = defaultAxistags(5)
#    axis[0].description = "Cat"
#    axis[1].description = "Snake"
#    axis[2].description = "Bird"
#    axis[3].description = "Tiger"
#    axis[4].description = "Lion"    

    axistags=vigra.AxisTags(axis[0],axis[1],axis[2],axis[3],axis[4])

    print "_______________________"
    print axistags
    print "_______________________"

    img = vigra.VigraArray(img, axistags=axistags)
    
    g = Graph(numThreads = 1, softMaxMem = 2000*1024**2)

    
    source = OpArrayPiper(g)
    source.inputs["Input"].setValue(img)
      
    s_dytpe = source.outputs["Output"]._dtype    
    s_shape = source.outputs["Output"]._shape
    s_axistags = source.outputs["Output"]._axistags       
      
    assert (s_shape == img.shape) 
               
    for i in range (5):
        assert (s_axistags[i].description == axistags[i].description)
        assert (s_axistags[i].isType(axistags[i].typeFlags))
               
    
    print "_______________________"
    print "________source_________"
    print "_______________________"
    res = source.outputs["Output"][:].allocate().wait()
    print "Result-Shape", res.shape    
    print "_dtype", s_dytpe
    print "_shape", s_shape
    print s_axistags
    print "_______________________"    
    
    Op = {}    

#    Op[0]= OpGaussianSmoothing(g)#
#    Op[0].inputs["sigma"].setValue(5) 
#    
#    Op[1]= OpGaussianSmoothing(g)#
#    Op[1].inputs["sigma"].setValue(0.3)    
#    
    Op[2] = OpDifferenceOfGaussians(g)#
    Op[2].inputs["sigma0"].setValue(1)
    Op[2].inputs["sigma1"].setValue(2)
    
#    Op[3] = OpDifferenceOfGaussians(g)#
#    Op[3].inputs["sigma0"].setValue(0.4)
#    Op[3].inputs["sigma1"].setValue(9)
#    
#    Op[4] = OpDifferenceOfGaussians(g)#
#    Op[4].inputs["sigma0"].setValue(2.1)
#    Op[4].inputs["sigma1"].setValue(0.6)    
#    
#    Op[5] = OpLaplacianOfGaussian(g)#
#    Op[5].inputs["scale"].setValue(2.5)
#    
#    Op[5] = OpLaplacianOfGaussian(g)#
#    Op[5].inputs["scale"].setValue(0.1)
#    
#    Op[6] = OpOpening(g)#
#    Op[6].inputs["sigma"].setValue(7.1)
#
#    Op[7] = OpOpening(g)#
#    Op[7].inputs["sigma"].setValue(0.8)
#    
#    Op[8] = OpErosion(g)#
#    Op[8].inputs["sigma"].setValue(0.74)
#    
#    Op[9] = OpErosion(g)#
#    Op[9].inputs["sigma"].setValue(3.25)
#    
#    Op[10] = OpDilation(g)#
#    Op[10].inputs["sigma"].setValue(0.15)
#    
#    Op[11] = OpDilation(g)#
#    Op[11].inputs["sigma"].setValue(9.1)   
#    
#    Op[10] = OpClosing(g)#    
#    Op[10].inputs["sigma"].setValue(5.12)
#    
#    Op[11] = OpClosing(g)#
#    Op[11].inputs["sigma"].setValue(0.36) 
#     
#    Op[12] = OpGaussianGradientMagnitude(g)#
#    Op[12].inputs["sigma"].setValue(2.12)
#    
#    Op[13] = OpGaussianGradientMagnitude(g)#
#    Op[13].inputs["sigma"].setValue(0.78)
    
#    Op[14] = OpHessianOfGaussianEigenvaluesFirst(g)
#    Op[14].inputs["scale"].setValue(6.7)
#
#    Op[15] = OpHessianOfGaussianEigenvaluesFirst(g)
#    Op[15].inputs["scale"].setValue(0.24)

#    Op[16] = OpArrayCache(g)##
#    
#    Op[17] = OpArrayCache(g)##
#    
#    Op[18] = OpArrayPiper(g)##
#    
#    Op[19] = OpArrayPiper(g)##
#    
#    Op[20] = operators.OpBlockedArrayCache(g)
#    Op[20].inputs["innerBlockShape"].setValue(10)
#    Op[20].inputs["outerBlockShape"].setValue((68,18,20,3,2))
#    Op[20].inputs["fixAtCurrent"].setValue(False)
#      
#    Op[21] = operators.OpBlockedArrayCache(g)
#    Op[21].inputs["innerBlockShape"].setValue(64)
#    Op[21].inputs["outerBlockShape"].setValue((100,50,100,50,50))
#    Op[21].inputs["fixAtCurrent"].setValue(False)

#    Op[22] = operators.OpPixelOperator(g)##
#    def func1(a):
#        return a +1
#    Op[22].inputs["Function"].setValue(func1)
#    
#    Op[23] = operators.OpPixelOperator(g)##
#    def func2(a):
#        return a * 7
#    Op[23].inputs["Function"].setValue(func2)
    
#    Op[24] = OpDifferenceOfGaussians(g)
#    Op[24].inputs["sigma0"].setValue(6.29)
#    
#    Op[25] = OpDifferenceOfGaussians(g)
#    Op[25].inputs["sigma0"].setValue(0.48)
#
#    Op[26] = OpCoherenceOrientation(g)
#    Op[26].inputs["sigma0"].setValue(0.77)
#    
#    Op[27] = OpCoherenceOrientation(g)
#    Op[27].inputs["sigma0"].setValue(3.6)OpSwapAxes


    max_num = len(Op)  
     
    numList = []
    for i in Op:
        numList.append(i)
         
    import random
    random.seed()  

    pre_num = 0    
    
    for i in range(max_num):
        num = numList[random.randint(0,len(numList)-1)]
        if i == 0:
            Op[num].inputs["Input"].connect(source.outputs["Output"])
        else:
            Op[num].inputs["Input"].connect(Op[pre_num].outputs["Output"])
        
        
        print "Op Number:", num
        print Op[num].outputs["Output"]._shape
        assert (Op[num].outputs["Output"]._shape == s_shape), "Output shape %s  expected shape %s "%( Op[num].outputs["Output"]._shape,s_shape)   
        assert (Op[num].outputs["Output"]._dtype == s_dytpe)
               
        for i in range (5):
            assert (Op[num].outputs["Output"]._axistags[i].description == s_axistags[i].description)
            assert (Op[num].outputs["Output"]._axistags[i].isType(s_axistags[i].typeFlags))
            
        pre_num = num
        numList.remove(num)
       
 
    e = OpArrayPiper(g)
    e.inputs["Input"].connect(Op[pre_num].outputs["Output"]) 
      
    print "_______________________"
    print "_________end___________"
    print "_______________________"  
    res = e.outputs["Output"][:].allocate().wait()
    print "Result-Shape", res.shape
    print "_dtype", e.outputs["Output"]._dtype
    print "_shape", e.outputs["Output"]._shape
    print e.outputs["Output"]._axistags
    


    g.finalize()
    
    
    
    
    #OpGaussianGradientMagnitude(g)
    #OpHessianOfGaussianEigenvaluesFirst(g)
    
    
    #OpDifferenceOfGaussians(g)
    #OpCoherenceOrientation(g)
    #None
    #None
    #None
    