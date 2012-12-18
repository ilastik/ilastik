from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import List, SubRegion
from lazyflow.operators.obsolete.generic import OpSubRegion
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
import numpy
import h5py
import vigra


class OpObjectExtractionMultiClass(Operator):
    name = "Object Extraction Multi-Class"
    
    # not necessarily a binary image (will be thresholded in the first step)
    Images = InputSlot()
    RawImage = InputSlot()

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    RegionCenters = OutputSlot(stype=Opaque, rtype=List)
    RegionFeatures = OutputSlot(stype=Opaque, rtype=List)
    ClassMapping = OutputSlot(stype=Opaque, rtype=List)
#    DistanceTransform = OutputSlot()
#    MaximumDistanceTransform = OutputSlot()        # regional maximums of the distance transform    
#    RegionLocalCenters = OutputSlot(stype=Opaque, rtype=List)  
    BinaryImage = OutputSlot()

    # channel 0: background channel, i.e. background vs. non-background
    # channel 2: division channel, i.e. division vs. non-division
    backgroundChannel = 0
    divisionChannel = 2
    
    def __init__(self, parent=None, graph=None):        
        super(OpObjectExtractionMultiClass, self).__init__(parent=parent, graph=graph)
    
        self._opThresholding = OpThresholding(parent=self,graph=graph)
        self._opThresholding.Threshold.setValue(0.5)
        self._opThresholding.Input.connect(self.Images)
                
        self._opObjectExtraction = OpObjectExtraction(parent=self,graph=graph)
        self._opObjectExtraction.BinaryImage.connect(self._opThresholding.BinaryImage)
        self._opObjectExtraction.RawImage.connect(self.RawImage)
        
        # set the background label for each channel: label 1 for channel 0, label 0 for channel 2, 
        # the labelimage of channel 1 will not be computed, set to -1
        self._opObjectExtraction.BackgroundLabels.setValue([1,-1,0]) 
        
#        self._opDistanceTransform = OpDistanceTransform3D(parent=self,graph=graph)
#        self._opDistanceTransform.Image.connect(self._opObjectExtraction.LabelImage)     
#        
#        self._opRegionalMaximum = OpRegionalMaximum(parent=self,graph=graph)
#        self._opRegionalMaximum.Image.connect(self._opDistanceTransform.DistanceTransformImage)
#        self._opRegionalMaximum.LabelImage.connect(self._opObjectExtraction.LabelImage)   
                        
        self._opClassExtraction = OpClassExtraction(parent=self,graph=graph)
        self._opClassExtraction.LabelImage.connect(self._opObjectExtraction.LabelImage)
        self._opClassExtraction.RegionFeatures.connect(self._opObjectExtraction.RegionFeatures)
        
        self._opClassExtraction.BackgroundChannel.setValue(self.backgroundChannel)
        self._opClassExtraction.DivisionChannel.setValue(self.divisionChannel)
        
        self.ClassMapping.connect(self._opClassExtraction.ClassMapping)        
#        self.DistanceTransform.connect(self._opDistanceTransform.DistanceTransformImage)
#        self.RegionLocalCenters.connect(self._opRegionalMaximum.RegionLocalCenters)
#        self.MaximumDistanceTransform.connect(self._opRegionalMaximum.MaximumImage)

    def setupOutputs(self):       
        shape = list(self.Images.meta.shape)
        shape[-1] = 1
        self.LabelImage.meta.assignFrom(self.RawImage.meta)
        self.LabelImage.meta.dtype = numpy.uint32
        self.LabelImage.meta.shape = shape     
        
        self.ObjectCenterImage.meta.assignFrom(self.RawImage.meta)
        self.ObjectCenterImage.meta.shape = shape
        
        self.RegionCenters.meta.shape = self.Images.meta.shape[0:1]
        self.RegionCenters.meta.dtype = object
        
        self.RegionFeatures.meta.shape = self.Images.meta.shape[0:1]
        self.RegionFeatures.meta.dtype = object
        
        self.ClassMapping.meta.shape = self.Images.meta.shape[0:1]
        self.ClassMapping.meta.dtype = object
        
        self.BinaryImage.meta.assignFrom(self.Images.meta)
        self.BinaryImage.meta.shape = shape
        self.BinaryImage.meta.dtype = numpy.uint32
        
                
    def execute(self, slot, subindex, roi, result):
        bgChannel = self.backgroundChannel        
   
        if slot == self.LabelImage:
            assert(roi.stop[-1] - roi.start[-1] == 1), "more than 1 channel requested"
            roi.start[-1] = bgChannel
            roi.stop[-1] = bgChannel+1                   
            result = self._opClassExtraction.LabelImage.get(roi).wait()
            return result
        if slot == self.ObjectCenterImage:
            assert(roi.stop[-1] - roi.start[-1] == 1), "more than 1 channel requested"
            roi.start[-1] = bgChannel
            roi.stop[-1] = bgChannel+1                    
            result = self._opObjectExtraction.ObjectCenterImage.get(roi).wait()
            return result
        if slot == self.BinaryImage:
            assert(roi.stop[-1] - roi.start[-1] == 1), "more than 1 channel requested"
            roi.start[-1] = bgChannel
            roi.stop[-1] = bgChannel+1                   
            result = self._opThresholding.BinaryImage.get(roi).wait()
            return result            
        if slot == self.RegionCenters:
            feats = self._opObjectExtraction.RegionCenters.get(roi).wait()
            feats_result = {}
            for t in roi:
                feats_at = feats[t]
                assert(len(feats_at) == self.Images.meta.shape[-1]), "number of channels in feature list differs from number of channels in input"
                feats_at_wo_channels = feats_at[bgChannel]                
                feats_result[t] = feats_at_wo_channels
            result = feats_result
            return result
        if slot == self.RegionFeatures:
            feats = self._opObjectExtraction.RegionFeatures.get(roi).wait()
            feats_result = {}
            for t in roi:
                feats_at = feats[t]
                assert(len(feats_at) == self.Images.meta.shape[-1]), "number of channels in feature list differs from number of channels in input"
                feats_at_wo_channels = feats_at[bgChannel]                
                feats_result[t] = feats_at_wo_channels
            result = feats_result
            return result
        
        
        
class OpClassExtraction(Operator):    
    name = "Class Extraction"
    
    LabelImage = InputSlot()    
    RegionFeatures = InputSlot()
    BackgroundChannel = InputSlot(stype='opaque') # index of background channel
    DivisionChannel = InputSlot(stype='opaque')   # index of division channel
    
    ClassMapping = OutputSlot(stype=Opaque, rtype=List)
    
    def __init__( self, parent=None, graph=None ):
        super(OpClassExtraction, self).__init__(parent=parent, graph=graph)
        self._cache = {}
    
    def setupOutputs(self):        
        self.ClassMapping.meta.shape = self.LabelImage.meta.shape[0:1]
        self.ClassMapping.meta.dtype = object
    
    def execute(self, slot, subindex, roi, result):
        def extract( labelImageBg, labelImageDiv, regionFeaturesBg, regionFeaturesDiv ):
            # label 0 is not used
            prob = [[0,0]] + [[1,0]] * len(regionFeaturesBg['Count'] - 1 )
            for labelDiv, volDiv in enumerate(regionFeaturesDiv['Count']):
                # skip the first label, since label 0 is not used in connected components
                if labelDiv == 0:
                    continue
                coordDiv = regionFeaturesDiv['Coord<ArgMaxWeight>'][labelDiv]
                labelBg = labelImageBg[tuple(coordDiv)]
                assert labelBg != 0, str(labelDiv) + ', ' + str(coordDiv)+ ', ' + str(labelImageBg.shape) + ', ' +  str(labelDiv) + ', ' + str(labelBg)
                assert labelBg < len(regionFeaturesBg['Count']), str(labelDiv) + ', ' + str(coordDiv)+ ', ' + str(labelImageBg.shape) + ', ' +  str(labelDiv) + ', ' + str(labelBg)                 
                assert volDiv > 0
                volBg = regionFeaturesBg['Count'][labelBg]
                assert volBg > 0
                p = volDiv / float(volBg)

                if prob[labelBg][0] != 1:
                    prob[labelBg][1] += p 
                    prob[labelBg][0] = 1-prob[labelBg][1]
                else:  
                    prob[labelBg] = [1-p, p]  # [ P(non-division), P(division) ]
            return prob
        
        bgChannel = self.BackgroundChannel.value
        divChannel = self.DivisionChannel.value
          
        probs = {}
        for t in roi:
            print "Class Extraction at " + str(t) + " "
            if t in self._cache:
                probs_at = self._cache[t]
            elif t == self.LabelImage.meta.shape[0] - 1:
                rfBg = self.RegionFeatures.get([t]).wait()
                rfBg = rfBg[bgChannel]
                prob = [[1,0]] * (len(rfBg[0]['Count']) - 1)            
                probs_at = prob 
                self._cache[t] = probs_at
            else:
                tcroi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 2) * [0,] + [bgChannel,], 
                                  stop = [t+1,] + list(self.LabelImage.meta.shape[1:-1]) + [bgChannel+1,])
                liBg = self.LabelImage.get(tcroi).wait()
                liBg = liBg[0,...,0] 
                rfBg = self.RegionFeatures.get([t]).wait()
                rfBg = rfBg[t][bgChannel]
                
                tcroi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 2) * [0,] + [divChannel,], 
                                  stop = [t+1,] + list(self.LabelImage.meta.shape[1:-1]) + [divChannel+1,])
                liDiv = self.LabelImage.get(tcroi).wait()
                liDiv = liDiv[0,...,0] # assumes t,x,y,z,c
                rfDiv = self.RegionFeatures.get([t]).wait()
                rfDiv = rfDiv[t][divChannel]
                probs_at = extract(liBg, liDiv, rfBg, rfDiv)
                self._cache[t] = probs_at
            probs[t] = probs_at

        return probs
            

    def propagateDirty(self, slot, subindex, roi):
        self.ClassMapping.setDirty(roi)
                        
    
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


class OpDistanceTransform3D( Operator ):
    name = "Distance Transform 3D"
    
    Image = InputSlot()    
    
    DistanceTransformImage = OutputSlot()
    # Pull the following output slot to compute the distance transform image.
    # This slot is introduced to allow for a precomputation of the output image and
    # write the results into a compressed hdf5 virtual file instead of allocating
    # space for all the requests.
    DistanceTransformComputation = OutputSlot(stype="float")

    def __init__(self, parent=None, graph=None):
        super(OpDistanceTransform3D, self).__init__(parent=parent,graph=graph)
        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)        
        self._processedTimeSteps = []
        self._fixed = True
        
    def setupOutputs( self ):        
        self.DistanceTransformImage.meta.assignFrom( self.Image.meta )
        self.DistanceTransformComputation.meta.dtype = numpy.float
        self.DistanceTransformComputation.meta.shape = [0]
            
        self.DistanceTransformImage.meta.dtype = numpy.uint8
        
#        m = self.DistanceTransformImage.meta           
#        self._mem_h5.create_dataset( 'DistanceTransform', shape=m.shape, dtype=numpy.float, compression=1 )
        
    def __del__( self ):
        self._mem_h5.close()
        
    def execute( self, slot, subindex, roi, destination ):        
        if slot is self.DistanceTransformImage:
            if self._fixed:
                destination[:] = 255
                return destination
            
            destination = self._mem_h5['DistanceTransform'][roi.toSlice()]
            return destination
        
        if slot is self.DistanceTransformComputation:
            # assumes t,x,y,z,c           
            for t in range(roi.starto[0],roi.stop[0]):            
                if t not in self._processedTimeSteps:
                    print "Computing Distance Transform Image at " + str(t) + " "
                    sroi = SubRegion(self.Image, start=[t,0,0,0,0], stop=[t+1,] + list(self.Image.meta.shape[1:]))   
                    a = self.Image.get(sroi).wait()
                    a = a[0,...,0].astype(numpy.float32)                    
                    self._mem_h5['DistanceTransform'][t,...,0] = vigra.filters.distanceTransform3D( a, background=False)
                    self._processedTimeSteps.append(t)
            
            
            
class OpRegionalMaximum( Operator ):
    name = "Regional Maximum"
    
    Image = InputSlot() # Distance Transform Image
    LabelImage = InputSlot()    
    
    MaximumImage = OutputSlot()
    # Pull the following output slot to compute the distance transform image.
    # This slot is introduced to allow for a precomputation of the output image and
    # write the results into a compressed hdf5 virtual file instead of allocating
    # space for all the requests.
    MaximumImageComputation = OutputSlot(stype="float")
        
    RegionLocalCenters = OutputSlot(stype=Opaque, rtype=List)    

    def __init__(self, parent=None, graph=None):
        super(OpRegionalMaximum, self).__init__(parent=parent,graph=graph)
        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)                
        self._processedTimeSteps = []
        self._fixed = True
        self._cache = {}
        
    def setupOutputs( self ):        
        self.MaximumImage.meta.assignFrom( self.Image.meta )
        self.MaximumImage.meta.dtype = numpy.uint8
        self.MaximumImageComputation.meta.dtype = numpy.float
        self.MaximumImageComputation.meta.shape = [0]
        
#        m = self.MaximumImage.meta           
#        self._mem_h5.create_dataset( 'MaximumImage', shape=m.shape, dtype=numpy.float, compression=1 )
        
        
    def __del__( self ):
        self._mem_h5.close()
        
    def execute( self, slot, subindex, roi, destination ):        
        if slot is self.MaximumImage:            
            if self._fixed:
                destination[:] = 255
                return destination
                        
            destination = self._mem_h5['MaximumImage'][roi.toSlice()]
            return destination
        
        if slot is self.MaximumImageComputation:
            # assumes t,x,y,z,c           
            for t in range(roi.start[0],roi.stop[0]):            
                if t not in self._processedTimeSteps:
                    print "Computing Maximum Image at " + str(t) + " "
                    sroi = SubRegion(self.Image, start=[t,0,0,0,0], stop=[t+1,] + list(self.Image.meta.shape[1:]))   
                    a = self.Image.get(sroi).wait()
                    a = a[0,...,0].astype(numpy.float32)
                    self._mem_h5['MaximumImage'][t,...,0] = vigra.analysis.extendedLocalMaxima3D(a)
                    self._processedTimeSteps.append(t)
        
        if slot is self.RegionLocalCenters:
            def extract( maximumImg, labelImg ):
                # label 0 is not used                
                feat = [ [] for i in range(numpy.max(labelImg)+1) ]
                idxes = numpy.where(maximumImg>0)
                labels = labelImg[idxes]
                for idx, coord in enumerate(zip(idxes[0],idxes[1],idxes[2])):
                    l = labels[idx]
                    assert l is not 0
                    
                    feat[l].append(coord) # or l+1????? since label 0 is not included
                    assert int(l) == int(labelImg[coord]), str(l) + ' ' + str(labelImg[coord]) + ' ' + str(coord)                                
                return feat
                return 0
            
            feats = {}
            for t in roi:
                print "Extracting RegionLocalCenters at t = " + str(t) + " "
                if str(t) in self._cache:
                    feats_at = self._cache[str(t)]                    
                else:
                    troi = SubRegion( self.Image, 
                                      start = [t,] + (len(self.Image.meta.shape) - 1) * [0,], 
                                      stop = [t+1,] + list(self.Image.meta.shape[1:]))
                    maxImg = self.MaximumImage.get(troi).wait()
                    maxImg = maxImg[0,...,0] # assumes t,x,y,z,c
                    labelImg = self.LabelImage.get(troi).wait()
                    labelImg = labelImg[0,...,0] # assumes t,x,y,z,c                    
                    feats_at = extract(maxImg, labelImg)
                    
                    self._cache[str(t)] = feats_at
                feats[t] = feats_at
    
            return feats
        