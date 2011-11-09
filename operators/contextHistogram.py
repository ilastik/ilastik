from lazyflow.graph import *
import context
from lazyflow import roi
from lazyflow.operators.generic import popFlagsFromTheKey


class OpHistogramContext(Operator):
    name = "ContextHistogram"
    description = "Compute histograms in the neighborhoods of different sizes"
       
    inputSlots = [InputSlot("PMaps"),InputSlot("Radii"), InputSlot("BinsCount",stype='integer'), \
                  InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("Output")]   

    def notifyConnectAll(self):

        nclasses=self.inputs["LabelsCount"].value
        radii=self.inputs["Radii"].value
        nbins = self.inputs["BinsCount"].value
        
        self.outputs["Output"]._dtype = self.inputs["PMaps"].dtype
        
        #assert len(self.inputs["PMaps"].shape) == 3 , "not implemented for 3D"
        if len(self.inputs["PMaps"].shape) == 3:
            h,w,c=self.inputs["PMaps"].shape
            self.outputs["Output"]._shape = (h, w, len(radii)*nbins*c)
        else:
            h,w,d,c = self.inputs["PMaps"].shape
            self.outputs["Output"]._shape = (h, w, d, len(radii)*nbins*c)
            
        self.outputs["Output"]._axistags = copy.copy(self.inputs["PMaps"].axistags)
        #print "set the output shape as ", self.outputs["Output"].shape
        
    def getOutSlot(self, slot, key, result):
        
       # print "requested key:", key, "result shape:", result.shape
        
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
        
        start, stop = roi.sliceToRoi(subkey,subkey)
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
        
        nbins = self.inputs["BinsCount"].value
        #print "We are in the business"
        if len(pmaps.shape)==3:
            context.contextHistogram2D(radii, nbins, pmaps, temp)
        else:
            context.contextHistogram3D(radii, nbins, pmaps, temp)
        result[:] = temp[writeNewKey]
        
        
        