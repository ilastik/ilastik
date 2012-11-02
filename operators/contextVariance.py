from lazyflow.graph import *
from lazyflow import roi

from lazyflow.graph import *
import context
import collections
import vigra

class OpVarianceContext2DOld(Operator):
    name = "VarianceContext2D"
    description = "Compute averages and variances in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"),InputSlot("LabelsCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):

        nclasses=self.inputs["LabelsCount"].value
        radii=self.inputs["Radii"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        h,w,c=self.inputs["PMaps"].shape
        
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)
        self.outputs["Output"]._shape = (h,w,2*nclasses*len(radii))

    def getOutSlot(self, slot, key, result):
        pmaps = self.inputs["PMaps"][:].allocate().wait()
        
        radii=self.inputs["Radii"].value
        
        radii=numpy.array(radii,dtype=numpy.uint32)
        print "We are in the business"
        print radii, radii.dtype
        context.varContext2Dmulti(radii,pmaps,result)




class OpContextVariance(Operator):
    name = "VarianceContext"
    description = "Compute averages and variances in the neighborhoods of different sizes"
       
    #inputSlots = [InputSlot("Input"),InputSlot("Radii"),InputSlot("LabelsCount")]
    inputSlots = [InputSlot("Input"), InputSlot("Radii")]
    outputSlots = [OutputSlot("Output")]    
    
    def setupOutputs(self):
        
        #nclasses = self.inputs["LabelsCount"].value
        radii = self.inputs["Radii"].value
        
        inputSlot = self.inputs["Input"]
        outputSlot = self.outputs["Output"]
        #copy over all the dtype and such
        outputSlot.meta.assignFrom(inputSlot.meta)
        #set the correct number of channels
        nclasses = inputSlot.meta.shape[inputSlot.meta.axistags.channelIndex]
        print "n classes at operator setup:", nclasses
        channelNum = 2*nclasses*len(radii)
        
        outputSlot.setShapeAtAxisTo('c', channelNum)
        
    def execute(self,slot,subindex, roi,result):
        axistags = self.inputs["Input"].meta.axistags
        inputShape  = self.inputs["Input"].meta.shape
        outputShape = self.outputs["Output"].meta.shape
        radii = self.inputs["Radii"].value
        #nclasses=self.inputs["LabelsCount"].value
        nclasses = self.inputs["Input"].meta.shape[self.inputs["Input"].meta.axistags.channelIndex]
        #FIXME: why do we do that? To ensure correct types for C++?
        radii = numpy.array(radii, dtype = numpy.uint32)
        maxRadius = numpy.max(radii)
        
        #print "contextVariance::execute axistags", axistags
        #print "contextVariance::execute roi", roi
        
        #Set up roi 
        roi.setInputShape(inputShape)
        
        #get srcRoi to retrieve necessary source data
        addShape = [maxRadius for dim in inputShape]
        roi_copy = copy.copy(roi)
        srcRoi = roi.expandByShape(addShape, tIndex=None, cIndex=axistags.channelIndex)
        #expand only in spatial dimensions
        srcRoi.setDim(axistags.channelIndex, 0, nclasses)
        hasTimeAxis = axistags.axisTypeCount(vigra.AxisType.Time)
        if hasTimeAxis:
            t = axistags.index['t']
            srcRoi.setDim(t, roi.start[t], roi.stop[t])
        
        source = self.inputs["Input"](srcRoi.start,srcRoi.stop).wait()
        source = vigra.VigraArray(source,axistags=axistags)
        
        #allocate space for the output
        resshape = list(source.shape)
        resshape[axistags.channelIndex] = numpy.long(outputShape[axistags.channelIndex])
        
        temp = vigra.VigraArray(tuple(resshape), axistags=axistags, dtype=self.outputs["Output"].meta.dtype )
        
        nNonsingles = len([x for x in inputShape if x>1])
        
        if (inputShape[axistags.channelIndex]>1 and nNonsingles==3 or nNonsingles==2):
            context.varContext2Dmulti(radii, source, temp)
        elif isinstance(radii[0], collections.Iterable):
            context.varContext3Danis(radii, source, temp)
        else:
            context.varContext3Dmulti(radii, source, temp)
        
        tgtRoi = self.shrinkToShape(maxRadius, srcRoi, roi_copy)
        channelIndex =self.outputs["Output"].meta.axistags.channelIndex
        tgtRoi.setDim(channelIndex, 0, self.outputs["Output"].meta.shape[channelIndex])
        
        result[:] = temp[tgtRoi.toSlice()]
        
        return result
    
    def shrinkToShape(self, maxRadius, srcRoi, roi):
        #print "roi in shrinkToShape:", roi
        tgtRoi = srcRoi.setStartToZero()
        tgtShape = roi.stop-roi.start
        #print "tgtShape", tgtShape
        tgtRoi.setInputShape(srcRoi.inputShape)
        for i in range(len(tgtRoi.start)):
            if srcRoi.start[i]!=0:
                tgtRoi.start[i]+=maxRadius
                tgtRoi.stop[i]= tgtRoi.start[i]+tgtShape[i]
                #print "case1", tgtRoi.start, tgtRoi.stop
            elif srcRoi.stop[i]!=srcRoi.inputShape[i]:
                tgtRoi.stop[i]-=maxRadius
                tgtRoi.start[i] = tgtRoi.stop[i]-tgtShape[i]
                #print "case2", tgtRoi.start, tgtRoi.stop
            else:
                tgtRoi.start[i] = roi.start[i]
                tgtRoi.stop[i] = roi.stop[i]
        
        #print "returning:", tgtRoi
        return tgtRoi
    
    
    def propagateDirty(self, inputSlot, subindex, key):
        #FIXME: propagate really
        pass

        