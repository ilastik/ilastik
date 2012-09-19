from lazyflow.graph import *
from lazyflow import roi

from lazyflow.graph import *
import context
import collections


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
    name = "VarianceContext2D"
    description = "Compute averages and variances in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("Input"),InputSlot("Radii"),InputSlot("LabelsCount")]
    outputSlots = [OutputSlot("Output")]    
    
    def setupOutputs(self):
        
        nclasses = self.inputs["LabelsCount"].value
        radii = self.inputs["Radii"].value
        
        inputSlot = self.inputs["Input"]
        outputSlot = self.outputs["Output"]
        #copy over all the dtype and such
        outputSlot.meta.assignFrom(inputSlot.meta)
        #set the correct number of channels
        channelNum = 2*nclasses*len(radii)
        
        outputSlot.setShapeAtAxisTo('c', channelNum)
    '''
    def notifyConnectAll(self):
        #print
        #print "** calling notifyConnectAll",self.inputs["PMaps"].shape
        #print
        nclasses=self.inputs["LabelsCount"].value
        radii=self.inputs["Radii"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        #assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        
        if len(self.inputs["PMaps"].shape) == 3:
            #2D case
            print "initializing 2d variance context"
            h,w,c=self.inputs["PMaps"].shape        
            self.outputs["Output"]._shape = (h,w,2*nclasses*len(radii))
        else:
            #3D case
            print "initializing 3d variance context"
            h, w, d, c = self.inputs["PMaps"].shape
            self.outputs["Output"]._shape = (h, w, d, 2*nclasses*len(radii))

        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)
    '''
        
        
    def execute(self,slot,subindex, roi,result):
        axistags = self.inputs["Input"].meta.axistags
        inputShape  = self.inputs["Input"].meta.shape
        outputShape = self.outputs["Output"].meta.shape
        radii = self.inputs["Radii"].value
        nclasses=self.inputs["LabelsCount"].value
        #FIXME: why do we do that? To ensure correct types for C++?
        radii = numpy.array(radii, dtype = numpy.uint32)
        maxRadius = numpy.max(radii)
        print "execute of opAutocontextVariance called with:"
        print "roi:", roi
        print "result shape:", result.shape
        print "axistags:", axistags
        
        '''
        #Set up roi 
        roi.setInputShape(inputShape)
        
        #get srcRoi to retrieve necessary source data
        addShape = [maxRadius for dim in inputShape]
        srcRoi = roi.expandByShape(addShape)
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
        resshape[axistags.channelIndex] = outputShape[axistags.channelIndex]
        temp = vigra.VigraArray(tuple(resshape), axistags=axistags)
        #print "allocated a temp array of size:", temp.shape
        
        nNonsingles = len([x for x in inputShape if x>1])
        
        if (inputShape[axistags.channelIndex]>1 and nNonsingles==3 or nNonsingles==2):
            context.varContext2Dmulti(radii, source, temp)
        elif isinstance(radii[0], collections.Iterable):
            context.varContext3Danis(radii, source, temp)
        else:
            context.varContext3Dmulti(radii, source, temp)
        
        tgtKey = roi.setStartToZero().expandWithShape()
        
        #Setup iterator to meet the special needs of each filter
        self.setupIterator(source, result)
        #get vigraRois to work with vigra filter
        vigraRoi = roi.centerIn(source.shape).popAxis('ct')
        for srckey,trgtkey in self.iterator:
            mask = roi.setStartToZero().maskWithShape(result[trgtkey].shape).toSlice()
            result[trgtkey] = self.vigraFilter(source=source[srckey],roi=vigraRoi)[mask]
            
        '''
        
        return result
    
    def propagateDirty(self, inputSlot, subindex, key):
        #FIXME: propagate really
        pass
    '''
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
        
        if len(pmaps.shape)==3:
            context.varContext2Dmulti(radii, pmaps, temp)
        elif isinstance(radii[0], collections.Iterable):
            context.varContext3Danis(radii, pmaps, temp)
        else:
            context.varContext3Dmulti(radii, pmaps, temp)
        #print "computing done"
        #print "writeNewKey:", writeNewKey
        result[:] = temp[writeNewKey]
    '''
        