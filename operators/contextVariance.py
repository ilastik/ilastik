from lazyflow.graph import *
from lazyflow import roi
from lazyflow.operators.generic import popFlagsFromTheKey

from lazyflow.graph import *
import context


class OpVarianceContext2DOld(Operator):
    name = "VarianceContext2D"
    description = "Compute averages and variances in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"),InputSlot("LabelsCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        #print
        #print "********************************************************************* calling notifyConnectAll",self.inputs["PMaps"].shape
        #print
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


class OpVarianceContext2D(Operator):
    name = "VarianceContext2D"
    description = "Compute averages and variances in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"),InputSlot("LabelsCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        #print
        #print "********************************************************************* calling notifyConnectAll",self.inputs["PMaps"].shape
        #print
        nclasses=self.inputs["LabelsCount"].value
        radii=self.inputs["Radii"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        #assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        if len(self.inputs["PMaps"].shape) == 3:
            #2D case        
            h,w,c=self.inputs["PMaps"].shape        
            self.outputs["Output"]._shape = (h,w,2*nclasses*len(radii))
        else:
            #3D case
            h, w, d, c = self.inputs["PMaps"].shape
            self.outputs["Output"]._shape = (h, w, d, 2*nclasses*len(radii))

        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)

    def getOutSlot(self, slot, key, result):
        
        #print "output requested for key:", key
        
        #print "VARIANCE CONTEXT, passed result of shape", result.shape
        
        radii=self.inputs["Radii"].value        
        radii=numpy.array(radii,dtype=numpy.uint32)
        maxRadius = numpy.max(radii)
        
        shape = self.outputs["Output"].shape
        axistags = self.inputs["PMaps"].axistags
        
        channelAxis=self.inputs["PMaps"].axistags.index('c')
        hasTimeAxis = self.inputs["PMaps"].axistags.axisTypeCount(vigra.AxisType.Time)
        timeAxis=self.inputs["PMaps"].axistags.index('t')

        subkey = popFlagsFromTheKey(key,axistags,'c')
        subshape=popFlagsFromTheKey(shape,axistags,'c')
        at2 = copy.copy(axistags)
        at2.dropChannelAxis()
        subshape=popFlagsFromTheKey(subshape,at2,'t')
        subkey = popFlagsFromTheKey(subkey,at2,'t')
        
        oldstart, oldstop = roi.sliceToRoi(key, shape)
        
        start, stop = roi.sliceToRoi(subkey,subshape)
        newStart, newStop = roi.extendSlice(start, stop, subshape, maxRadius, 1)
        newkey = list(roi.roiToSlice(newStart, newStop))
        #Request all the labels
        nclasses=self.inputs["LabelsCount"].value
        newkey.append(slice(0, nclasses, None))
        readKey = tuple(newkey)
        
        #print "pmaps will be computed for key:", readKey
        pmaps = self.inputs["PMaps"][readKey].allocate().wait()
        #print "pmaps computation done", pmaps.shape
        
        writeNewStart = start - newStart
        writeNewStop = writeNewStart +  stop - start
        writeNewKey = roi.roiToSlice(writeNewStart, writeNewStop)
        
        #stuff is not allocated inside, we have to do it here
        resshape = list(pmaps.shape)
        resshape[-1] = shape[-1]
        temp = vigra.VigraArray(tuple(resshape), axistags=vigra.VigraArray.defaultAxistags(len(pmaps.shape)))
        #print "allocated a temp array of size:", temp.shape
        
        
        context.varContext2Dmulti(radii, pmaps, temp)
        #print "computing done"
        #print "writeNewKey:", writeNewKey
        result[:] = temp[writeNewKey]
        
        