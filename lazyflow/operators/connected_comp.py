import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot
from lazyflow.roi import sliceToRoi, roiToSlice, block_view

class OpThreshold(Operator):
    #Threshold one channel agains the rest. To be used for threshoding probability maps
    #after classification
    name = "OpThreshold"
    description = "Threshold one channel against the rest"
    category = "Learning"
    
    inputSlots = [InputSlot("Input"),InputSlot("Channel",stype='integer'),InputSlot("Threshold")]
    outputSlots = [OutputSlot("Output")]
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["Input"]
        
        self.outputs["Output"]._shape = inputSlot.shape[:-1]+(1,)
        self.outputs["Output"]._dtype = numpy.uint8
        self.outputs["Output"]._axistags = inputSlot.axistags
    
    def getOutSlot(self, slot, key, result):
        shape = self.inputs["Input"].shape
        rstart, rstop = sliceToRoi(key, shape)  
        rstop[-1] = shape[-1]
        rkey = roiToSlice(rstart,rstop)
        pred = self.inputs["Input"][rkey].allocate().wait()
        
        ch = self.inputs["Channel"].value
        th = self.inputs["Threshold"].value
        result[...,0] = numpy.where(pred[...,ch]>th, 1, 0)
        
class OpConnectedComponents(Operator):
    #perform connected components. By default, cc is done with background label 0, i.e.
    #objects of label 0 are not counted.
    
    name = "OpConnectedComponents"
    description = "Connected components"
    category = "Learning"
    
    inputSlots = [InputSlot("Input"), InputSlot("Neighborhood"), InputSlot("Background")]
    outputSlots = [OutputSlot("Output")]
    
    def notifySubConnect(self, slots, indexes):
        #FIXME: trying to set a default value here. Is it the right way?
        print "in NotifySubConnect"
        if self.inputs["Input"].connected():
            inputSlot = self.inputs["Input"]
            self.outputs["Output"]._shape = inputSlot.shape
            self.outputs["Output"]._dtype = numpy.uint32
            self.outputs["Output"]._axistags= inputSlot.axistags
            if not self.inputs["Neighborhood"].connected():
                if inputSlot.axistags.axisTypeCount(vigra.AxisType.NonChannel)==3:
                    self.inputs["Neighborhood"].setValue(26)
                elif inputSlot.axistags.axisTypeCount(vigra.AxisType.NonChannel)==2:
                    self.inputs["Neighborhood"].setValue(8)
            if not self.inputs["Background"].connected():
                self.inputs["Background"].setValue(0)
    
    def notifyConnectAll(self):
        inputSlot = self.inputs["Input"]
        self.outputs["Output"]._shape = inputSlot.shape
        self.outputs["Output"]._dtype = numpy.uint32
        self.outputs["Output"]._axistags= inputSlot.axistags
        
    def getOutSlot(self, slot, key, result):
        
        image = self.inputs["Input"][key].allocate().wait()
        neighborhood = self.inputs["Neighborhood"].value
        bg = self.inputs["Background"].value
        temp = None
        #if image.axistags.axisTypeCount(vigra.AxisType.NonChannel)==3:
        if len(image.shape)>2:
            if bg!=-1:            
                temp = vigra.analysis.labelVolumeWithBackground(image, neighborhood, bg)
            else:
                temp = vigra.analysis.labelVolume(image, neighborhood)
        #elif image.axistags.axisTypeCount(vigra.AxisType.NonChannel)==2:
        else:
            if bg!=-1:
                temp = vigra.analysis.labelImageWithBackground(image, neighborhood, bg)
            else:
                temp = vigra.analysis.labelImage(image, neighborhood)
                
        result[:] = temp[:]
        
        