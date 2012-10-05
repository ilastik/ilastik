from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List, SubRegion
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

#        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)
        
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
        print "WARNING: number of time frames restricted to 3 for debugging purposes"      
#        stop = list(self.Images.meta.shape[0:-1]) + [backgroundlabel + 1,]
        stop = [3,] + list(self.Images.meta.shape[1:-1]) + [backgroundlabel + 1,]                
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
    
    def __init__( self, parent=None, graph=None ):
        super(OpClassExtraction, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
#        self.fixed = True
    
    def setupOutputs(self):
        pass
    
    def execute(self, slot, subindex, roi, result):
        def extract( labelImageBg, labelImageDiv, regionFeaturesBg, regionFeaturesDiv ):
            try:
                prob = [[1,0]] * (len(regionFeaturesBg['Count']) - 1)
            except:
                raise
            for labelDiv, volDiv in enumerate(regionFeaturesDiv['Count']):
                # skip the first label, since label 0 is not used in connected components
                if labelDiv == 0:
                    continue
                coordDiv = regionFeaturesDiv['Coord<ArgMaxWeight>'][labelDiv]
                labelBg = labelImageBg[tuple(coordDiv)]
                assert labelBg != 0, str(labelDiv) + ', ' + str(coordDiv)+ ', ' + str(labelImageBg.shape) + ', ' +  str(labelDiv) + ', ' + str(labelBg) 
                #+ ', ' + str(labelImageBg[tuple(regionFeaturesDiv[0]['Coord<Minimum>'][labelDiv])])+ ', ' + str(labelImageBg[tuple(regionFeaturesDiv[0]['Coord<ArgMaxWeight>'][labelDiv])])+ ', ' + str(labelImageBg[tuple(regionFeaturesDiv[0]['Coord<ArgMinWeight>'][labelDiv])])
                assert volDiv > 0
                volBg = regionFeaturesBg['Count'][labelBg]
                assert volBg > 0
                p = volDiv / float(volBg) 
                prob[labelBg] = [1-p, p]  # [ P(non-division), P(division) ]
            return prob
            
        probs = {}
        for t in roi:
            print "Class Extraction at", t
            if t in self._cache:
                probs_at = self._cache[t]
#            elif self.fixed:
#                probs_at = numpy.asarray([])
            elif t == self.LabelImageBg.meta.shape[0] - 1:
                rfBg = self.RegionFeaturesBg.get([t]).wait()
                prob = [[1,0]] * (len(rfBg[0]['Count']) - 1)            
                probs_at = prob 
                self._cache[t] = probs_at
            else:
                troi = SubRegion( self.LabelImageBg, start = [t,] + (len(self.LabelImageBg.meta.shape) - 1) * [0,], stop = [t+1,] + list(self.LabelImageBg.meta.shape[1:]))
                liBg = self.LabelImageBg.get(troi).wait()
                liBg = liBg[0,...,0] # assumes t,x,y,z,c
                rfBg = self.RegionFeaturesBg.get([t]).wait()
                rfBg = rfBg[t]                
                liDiv = self.LabelImageDiv.get(troi).wait()
                liDiv = liDiv[0,...,0] # assumes t,x,y,z,c
                rfDiv = self.RegionFeaturesDiv.get([t]).wait()
                rfDiv = rfDiv[t]
                probs_at = extract(liBg, liDiv, rfBg, rfDiv)
                self._cache[t] = probs_at
            probs[t] = probs_at

        return probs
    
    
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
    