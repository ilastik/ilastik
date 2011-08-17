from lazyflow.graph import *
from lazyflow import roi 
import numpy

class OpShift(Operator):
    name = "Shift"
    description = "Shift the input data by a given value in a given dimension"
    #for values outside the range reflection is used   
    inputSlots = [InputSlot("Input"), InputSlot("AxisFlag"),InputSlot("ShiftValue")]
    outputSlots = [OutputSlot("Output")]    
    
    def notifyConnectAll(self):
        #set up shape and stuff
        axis_input = self.inputs["Input"].axistags
        #assert axis_input.axisTypeCount(vigra.AxisType.Channels)!=0, "Shift writes results into channel, it's needed"
        
        axkeys = [ax.key for ax in self.inputs["Input"].axistags]
        axind = axkeys.index(self.inputs["AxisFlag"].value)
        
        value = self.inputs["ShiftValue"].value
        assert value<self.inputs["Input"].shape[axind], "the shift is too large"
        
        self.outputs["Output"]._dtype = self.inputs["Input"].dtype
        self.outputs["Output"]._shape = self.inputs["Input"].shape
        self.outputs["Output"]._axistags = copy.copy(self.inputs["Input"].axistags)
        
        
        
    def getOutSlot(self, slot, key, result):
        
        axkeys = [ax.key for ax in self.inputs["Input"].axistags]
        axind = axkeys.index(self.inputs["AxisFlag"].value)
        start, stop = roi.sliceToRoi(key, self.outputs["Output"].shape)
        value = self.inputs["ShiftValue"].value
        shape = self.inputs["Input"].shape
        
        requests = []
        
        if start[axind]+value >= shape[axind]:
            #full reflection
            srckey = list(key)
            srckey[axind] = slice(shape[axind]-start[axind]-value, shape[axind]-stop[axind]-value, -1)
            req = self.inputs["Input"][tuple(srckey)].writeInto(result[key])
            requests.append(req)
        elif stop[axind]+value >= shape[axind]:
            srckey = list(key)
            srckey1 = copy.copy(srckey)
            srckey1[axind] = slice(start[axind]+value, shape[axind], None)
            destkey = copy.copy(srckey)
            destkey[axind] = slice(start[axind], shape[axind]-value, None)
            req = self.inputs["Input"][tuple(srckey1)].writeInto(result[tuple(destkey)])
            requests.append(req)
            srckey2 = copy.copy(srckey)
            srckey2[axind] = slice(-1, shape[axind]-stop[axind]-value-1, -1)
            destkey2 = copy.copy(srckey)
            destkey2[axind] = slice(shape[axind]-value, stop[axind], None)
            #bla = self.inputs["Input"][tuple(srckey2)].allocate().wait()
            #print "BLA", bla.shape
            print "SRCKEY2:", srckey2, "DESTKEY2:", destkey2
            req = self.inputs["Input"][tuple(srckey2)].writeInto(result[tuple(destkey2)])
            requests.append(req)
        else :
            #everything fits nicely
            srckey = list(key)
            srckey[axind] = slice(start[axind]+value, stop[axind]+value, None)
            print "SRCKEY", srckey, "KEY", key, "res. shape: ", result.shape, "slot shape: ", slot.shape
            bla = self.inputs["Input"][tuple(srckey)].allocate().wait()
            print "BLA", bla.shape
            
            req = self.inputs["Input"][tuple(srckey)].writeInto(result[key])
            
        for r in requests:
            r.wait()
       