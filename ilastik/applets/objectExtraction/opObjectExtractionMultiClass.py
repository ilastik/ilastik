from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List
from lazyflow.operators.obsolete.generic import OpSubRegion
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
import numpy
import h5py
#from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction


class OpObjectExtractionMultiClass(Operator):
    name = "Object Extraction Multi-Class"
    
    # not necessarily a binary image (will be thresholded in the first step)
    Images = InputSlot()   

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    RegionCenters = OutputSlot(stype=Opaque, rtype=List)
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)
    ClassMapping = OutputSlot(stype=Opaque, rtype=List)
    BinaryImage = OutputSlot()
    

    def __init__(self, parent=None, graph=None):        
        super(OpObjectExtractionMultiClass, self).__init__(parent=parent, graph=graph)
        print "OpObjectExtractionMultiClass::init"

        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        
        self._opThresholding = OpThresholding(graph=graph)
        self._opThresholding.Threshold.setValue(0.5)
        self._opThresholding.Input.connect(self.Images)
        self.BinaryImage.connect(self._opThresholding.BinaryImage)
        
        # TODO: generalize to m classes
        self._opSubRegionBgImage = OpSubRegion(graph=graph)        
        self._opSubRegionBgImage.inputs["Input"].connect(self._opThresholding.BinaryImage)
                
        self._opSubRegionDivImage = OpSubRegion(graph=graph)
        self._opSubRegionDivImage.inputs["Input"].connect(self._opThresholding.BinaryImage)        
        
        self._opObjectExtractionBg = OpObjectExtraction(graph=graph)
        self._opObjectExtractionBg.BinaryImage.connect(self._opSubRegionBgImage.outputs["Output"])
        # TODO: is this background label really needed or does the operator read the background label from 0,0,0,0?
        self._opObjectExtractionBg.BackgroundLabel.setValue(1)
        
        self._opObjectExtractionDiv = OpObjectExtraction(graph=graph)
        self._opObjectExtractionDiv.BinaryImage.connect(self._opSubRegionDivImage.outputs["Output"])
        self._opObjectExtractionDiv.BackgroundLabel.setValue(0)
        
        self.LabelImage.connect(self._opObjectExtractionBg.LabelImage)
        self.ObjectCenterImage.connect(self._opObjectExtractionBg.ObjectCenterImage)
        self.RegionCenters.connect(self._opObjectExtractionBg.RegionCenters)
        self.RegionFeatures.connect(self._opObjectExtractionBg.RegionFeatures)
        
        self._opClassExtraction = OpClassExtraction(graph=graph)
        self._opClassExtraction.inputs["LabelImageBg"].connect(self._opObjectExtractionBg.LabelImage)
        self._opClassExtraction.inputs["LabelImageDiv"].connect(self._opObjectExtractionDiv.LabelImage)
        self._opClassExtraction.inputs["RegionFeaturesBg"].connect(self._opObjectExtractionBg.RegionFeatures)
        self._opClassExtraction.inputs["RegionFeaturesDiv"].connect(self._opObjectExtractionDiv.RegionFeatures)
        
        self.ClassMapping.connect(self._opClassExtraction.outputs["ClassMapping"])        
        

    def setupOutputs(self):
        print "setupOutputs: Inputs.shape " + str(self.Images.meta.shape)
        # TODO: set values to channel 0 (if label 0 == bg)
        # assumes that background == label 0, assumes t,x,y,z,c        
        backgroundlabel = 0
        start = (len(self.Images.meta.shape) - 1) * [0,] + [backgroundlabel,]   
        print "WARNING: number of time frames restricted to 2 for debugging purposes"      
#        stop = list(self.Images.meta.shape[0:-1]) + [backgroundlabel + 1,]
        stop = [1,] + list(self.Images.meta.shape[1:-1]) + [backgroundlabel + 1,]                
        self._opSubRegionBgImage.inputs["Start"].setValue(tuple(start))        
        self._opSubRegionBgImage.inputs["Stop"].setValue(tuple(stop)) 
        
        # assumes that division == label 2, assumes t,x,y,z,c
        divisionlabel = 2
        start[-1] = divisionlabel        
        stop[-1] = divisionlabel + 1                
        self._opSubRegionDivImage.inputs["Start"].setValue(tuple(start))        
        self._opSubRegionDivImage.inputs["Stop"].setValue(tuple(stop))        
        
#        # TODO: why do I have to call this explicitly?? -> because the output hasn't been pulled yet, 
#        # other than the one of the bgOperator, since that's connected to the LabelImage
#        print "setting up div object extraction"
#        self._opObjectExtractionDiv.setupOutputs()
    
    def execute(self, slot, subindex, roi, result):
        pass

    def propagateDirty(self, inputSlot, roi):
        raise NotImplementedError

    def updateLabelImageAt( self, t, c ):        
        if c == 0: 
            print 'updating labels for background binary image'
            self._opObjectExtractionBg.updateLabelImageAt(t)
        elif c == 2:
            print 'updating labels for division binary image'
            self._opObjectExtractionDiv.updateLabelImageAt(t)
        else:
            raise Exception, 'invalid channel'
        

class OpClassExtraction(Operator):    
    name = "Class Extraction"
    
    LabelImageBg = InputSlot()
    LabelImageDiv = InputSlot()
    RegionFeaturesBg = InputSlot()
    RegionFeaturesDiv = InputSlot()
    
    ClassMapping = OutputSlot(stype=Opaque, rtype=List)
    
    def setupOutputs(self):
        pass
    
    def execute(self, slot, subindex, roi, result):
        # initialize prob dict with 1.0 for all bg labels
        # get both labelimages (roi)
        # for all div labels
            # lookup bg-label for the current div label
            # lookup bg-volume for this bg-label
            # lookup div-volume for this bg-label
            # prob[bg-label] = ratio, 1-ratio
        # return the dict (do not use result!)
        pass
    
    def propagateDirty(self, slot, subindex, roi):
        pass
        

class OpThresholding(Operator):
    name = "Thresholding"
    
    Input = InputSlot()
    Threshold = InputSlot()
    BinaryImage = OutputSlot()
    
    maximum = None
    def setupOutputs(self):
        self.BinaryImage.meta.dtype = numpy.uint8
        self.BinaryImage.meta.shape = self.Input.meta.shape
        self.BinaryImage.meta.axistags = self.Input.meta.axistags
    
    def execute(self, slot, subindex, roi, result):
        img = self.Input.get(roi).wait()
        threshold = self.Threshold.value
        if self.maximum is None:
            self.maximum = numpy.ceil(numpy.max(img))
        threshold *= self.maximum            
        return (img > threshold)        
    
    def propagateDirty(self, slot, subindex, roi):
        pass
    