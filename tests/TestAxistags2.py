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






def add_Op(graph, OpNum=None):
    a_Op = {}        
    import random
    random.seed()    
    
    a_Op[0]= OpGaussianSmoothing(graph)#
    a_Op[0].inputs["sigma"].setValue(0.2) 
    
    a_Op[1]= OpGaussianSmoothing(graph)#
    a_Op[1].inputs["sigma"].setValue(0.3)    
    
    a_Op[2] = OpDifferenceOfGaussians(graph)#
    a_Op[2].inputs["sigma0"].setValue(1)
    a_Op[2].inputs["sigma1"].setValue(0.2)
        
    a_Op[3] = OpDifferenceOfGaussians(graph)#
    a_Op[3].inputs["sigma0"].setValue(0.4)
    a_Op[3].inputs["sigma1"].setValue(1.9)
    
    a_Op[4] = OpDifferenceOfGaussians(graph)#
    a_Op[4].inputs["sigma0"].setValue(1.1)
    a_Op[4].inputs["sigma1"].setValue(0.6)    
    
    a_Op[5] = OpLaplacianOfGaussian(graph)#
    a_Op[5].inputs["scale"].setValue(1.5)
    
    a_Op[5] = OpLaplacianOfGaussian(graph)#
    a_Op[5].inputs["scale"].setValue(0.1)
    
    a_Op[6] = OpOpening(graph)#
    a_Op[6].inputs["sigma"].setValue(1.1)

    a_Op[7] = OpOpening(graph)#
    a_Op[7].inputs["sigma"].setValue(0.8)
    
    a_Op[8] = OpErosion(graph)#
    a_Op[8].inputs["sigma"].setValue(0.74)
    
    a_Op[9] = OpErosion(graph)#
    a_Op[9].inputs["sigma"].setValue(1.25)
    
    a_Op[10] = OpDilation(graph)#
    a_Op[10].inputs["sigma"].setValue(0.15)
    
    a_Op[11] = OpDilation(graph)#
    a_Op[11].inputs["sigma"].setValue(0.1)   
    
    a_Op[10] = OpClosing(graph)#    
    a_Op[10].inputs["sigma"].setValue(1.12)
    
    a_Op[11] = OpClosing(graph)#
    a_Op[11].inputs["sigma"].setValue(0.36) 
     
    a_Op[12] = OpGaussianGradientMagnitude(graph)#
    a_Op[12].inputs["sigma"].setValue(1.12)
    
    a_Op[13] = OpGaussianGradientMagnitude(graph)#
    a_Op[13].inputs["sigma"].setValue(0.78)
        
#    a_Op[14] = OpHessianOfGaussianEigenvaluesFirst(graph)
#    a_Op[14].inputs["scale"].setValue(6.7)

#    a_Op[15] = OpHessianOfGaussianEigenvaluesFirst(graph)
#    a_Op[15].inputs["scale"].setValue(0.24)
    
    a_Op[16] = OpArrayCache(graph)##
    
    a_Op[17] = OpArrayCache(graph)##
    
    a_Op[18] = OpArrayPiper(graph)##
    
    a_Op[19] = OpArrayPiper(graph)##
        
    a_Op[20] = operators.OpBlockedArrayCache(graph)
    a_Op[20].inputs["innerBlockShape"].setValue(7)
    a_Op[20].inputs["outerBlockShape"].setValue((5,18,20,3,2))
    a_Op[20].inputs["fixAtCurrent"].setValue(False)
          
    a_Op[21] = operators.OpBlockedArrayCache(graph)
    a_Op[21].inputs["innerBlockShape"].setValue(64)
    a_Op[21].inputs["outerBlockShape"].setValue((10,5,10,5,5))
    a_Op[21].inputs["fixAtCurrent"].setValue(False)
    
    a_Op[22] = operators.OpPixelOperator(graph)##
    def func1(a):
        return a +1
    a_Op[22].inputs["Function"].setValue(func1)
    
    a_Op[23] = operators.OpPixelOperator(graph)##
    def func2(a):
        return a * 7
    a_Op[23].inputs["Function"].setValue(func2)
#        
#    a_Op[24] = OpDifferenceOfGaussians(graph)
#    a_Op[24].inputs["sigma0"].setValue(6.29)
#    
#    a_Op[25] = OpDifferenceOfGaussians(graph)
#    a_Op[25].inputs["sigma0"].setValue(0.48)
#
#    a_Op[26] = OpCoherenceOrientation(graph)
#    a_Op[26].inputs["sigma0"].setValue(0.77)
#    
#    a_Op[27] = OpCoherenceOrientation(graph)
#    a_Op[27].inputs["sigma0"].setValue(3.6)
    
    if OpNum in a_Op:
        return a_Op[OpNum]
    else:
        a_List = []
        for i in a_Op:
            a_List.append(i)
        return a_Op[a_List[random.randint(0,len(a_List)-1)]]





def connect_Multi20_Stacker(graph, source, Op):
    """
    source - Source-Operator
    Op - Dictionnary of preset Operators
    """    
    s_dytpe = source.outputs["Output"]._dtype    
    s_shape = source.outputs["Output"]._shape
    s_axistags = source.outputs["Output"]._axistags 
    
    numList = []
    for i in Op:
        numList.append(i)
     
    max_num = len(numList)     
     
    import random
    random.seed()  
  
    
    List_Mul_20 = {}    
    List_Stacker_20 = {}
    
    Multi_20 = Op20ToMulti(graph)
    Stacker_20 = OpMultiArrayStacker(graph)
    
    for j in range(max_num/20+1):        
        List_Mul_20[j] = Op20ToMulti(graph)
        #for z in range(20):
        #    List_Mul_20[j].inputs["Input%02d" %(z)].disconnect()              
        List_Stacker_20[j] = OpMultiArrayStacker(graph)
        
        sub_Max = min(max_num-j*20,20)
        for i in range(sub_Max):
            num = numList[random.randint(0,len(numList)-1)]
            Op[num].inputs["Input"].connect(source.outputs["Output"])
            List_Mul_20[j].inputs["Input%02d" %i].connect(Op[num].outputs["Output"])
            numList.remove(num)    

        List_Stacker_20[j].inputs["Images"].connect(List_Mul_20[j].outputs["Outputs"])
        List_Stacker_20[j].inputs["AxisFlag"].setValue('c')
        List_Stacker_20[j].inputs["AxisIndex"].setValue(s_axistags.index('c'))
        Multi_20.inputs["Input%02d" %j].connect(List_Stacker_20[j].outputs["Output"])

        print "_______________________"             
        print "Stacker_Number:", j
        print List_Stacker_20[j].outputs["Output"]._shape
        print "_______________________"
        temp_shape = list(s_shape)
        temp_shape[s_axistags.index('c')] = s_shape[s_axistags.index('c')]*sub_Max
        assert (List_Stacker_20[j].outputs["Output"]._shape == tuple(temp_shape)) 
        assert (List_Stacker_20[j].outputs["Output"]._dtype == s_dytpe)
                  
        for i in range (5):
            assert (List_Stacker_20[j].outputs["Output"]._axistags[i].description == s_axistags[i].description)
            assert (List_Stacker_20[j].outputs["Output"]._axistags[i].isType(s_axistags[i].typeFlags))
                
    Stacker_20.inputs["Images"].connect(Multi_20.outputs["Outputs"])
    Stacker_20.inputs["AxisFlag"].setValue('c')
    Stacker_20.inputs["AxisIndex"].setValue(s_axistags.index('c'))

    print "_______________________" 
    print "_______________________"
    print "Big Stacker"
    print Stacker_20.outputs["Output"]._shape
    print "_______________________"
    print "_______________________"
    temp_shape = list(s_shape)
    temp_shape[s_axistags.index('c')] = s_shape[s_axistags.index('c')]*max_num
    assert (Stacker_20.outputs["Output"]._shape == tuple(temp_shape)), "OutputShape: %s  expected Shape %s" %(Stacker_20.outputs["Output"]._shape, tuple(temp_shape) ) 
    assert (Stacker_20.outputs["Output"]._dtype == s_dytpe)
                  
    for i in range (5):
        assert (Stacker_20.outputs["Output"]._axistags[i].description == s_axistags[i].description)
        assert (Stacker_20.outputs["Output"]._axistags[i].isType(s_axistags[i].typeFlags))

    return Stacker_20




def createVigraAxistags():
    
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
    
    return axistags


def connect_random(graph, source, Op): 
    """
    source - Source-Operator
    Op - Dictionnary of preset Operators
    """
    s_dytpe = source.outputs["Output"]._dtype    
    s_shape = source.outputs["Output"]._shape
    s_axistags = source.outputs["Output"]._axistags     
       
    numList = []
    for i in Op:
        numList.append(i)
     
    max_num = len(numList)      
     
    import random
    random.seed()  

    pre_num = 0 
    num = 0
    
    for i in range(max_num):
        num = numList[random.randint(0,len(numList)-1)]
        if i == 0:
            Op[num].inputs["Input"].connect(source.outputs["Output"])
        else:
            Op[num].inputs["Input"].connect(Op[pre_num].outputs["Output"])
        
        
        print "Op Name:", Op[num].name
        print Op[num].outputs["Output"]._shape
        assert (Op[num].outputs["Output"]._shape == s_shape), "Output shape %s  expected shape %s "%( Op[num].outputs["Output"]._shape,s_shape)   
        assert (Op[num].outputs["Output"]._dtype == s_dytpe)
               
        for i in range (5):
            assert (Op[num].outputs["Output"]._axistags[i].description == s_axistags[i].description)
            assert (Op[num].outputs["Output"]._axistags[i].isType(s_axistags[i].typeFlags))
            
        pre_num = num
        numList.remove(num)
    
    return Op[num]






if __name__=="__main__":
    
    s = [10,10,10,10,10]    
    img = numpy.ndarray((s[0],s[1],s[2],s[3],s[4]), dtype = float)
     
    axistags = createVigraAxistags()
    
    print "_______________________"
    print axistags
    print "_______________________"
    
    img = vigra.VigraArray(img, axistags=axistags)
    
    g = Graph()

    
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
    
    
#    Op = {}       
#
#    for i in range(0,42):
#        Op[i] = add_Op(g)
#
#    max_num = len(Op)  
#    print "MAX:" , max_num
#   
#    stacker = connect_Multi20_Stacker(g,source, Op)   
    
    Op = {}       

    for i in range(0,12):
        Op[i] = add_Op(g) 
    

    max_num = len(Op)  
    print "MAX:" , max_num
    
    rand_op = connect_random(g,source, Op)

    


    e = OpArrayPiper(g)
    e.inputs["Input"].connect(rand_op.outputs["Output"]) 
      
    print "_______________________"
    print "_________end___________"
    print "_______________________"  
    print "_dtype", e.outputs["Output"]._dtype
    print "_shape", e.outputs["Output"]._shape
    print e.outputs["Output"]._axistags
    res = e.outputs["Output"][:].allocate().wait()
    print "Result-Shape", res.shape
    

    assert (e.outputs["Output"]._shape == s_shape), "Output shape %s  expected shape %s "%( e.outputs["Output"]._shape,s_shape)   
    assert (e.outputs["Output"]._dtype == s_dytpe)
               
    for i in range (5):
        assert (e.outputs["Output"]._axistags[i].description == s_axistags[i].description)
        assert (e.outputs["Output"]._axistags[i].isType(s_axistags[i].typeFlags))




    g.finalize()
    
    
    
    
    #OpGaussianGradientMagnitude(g)
    #OpHessianOfGaussianEigenvaluesFirst(g)
    
    
    #OpDifferenceOfGaussians(g)
    #OpCoherenceOrientation(g)
    #None
    #None
    #None