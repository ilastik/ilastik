import numpy
import h5py
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion, List

class OpLabelImage( Operator ):
    name = "Label Image Accessor"
    BinaryImage = InputSlot()
    # List of background label in the order of channels of the binary image; -1 if the label image 
    # should not be computed for that channel
    BackgroundLabels = InputSlot( stype=Opaque, rtype=List )
    
    LabelImage = OutputSlot()
    # Pull the following output slot to compute the label image.
    # This slot is introduced in order to do a precomputation of the output image and
    # to write the results into a compressed hdf5 virtual file instead of allocating
    # space for all the requests.
    LabelImageComputation = OutputSlot(stype="float")
    
    def __init__(self, parent=None, graph=None):
        super(OpLabelImage, self).__init__(parent=parent,graph=graph)
        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)        
        self._processedTimeSteps = []
        
    def setupOutputs( self ):        
        self.LabelImage.meta.assignFrom( self.BinaryImage.meta )
        self.LabelImage.meta.dtype = numpy.uint32
        self.LabelImageComputation.meta.dtype = numpy.float
        self.LabelImageComputation.meta.shape = [0]        
        
        m = self.LabelImage.meta
        self._mem_h5.create_dataset( 'LabelImage', shape=m.shape, dtype=numpy.uint32, compression=1 )                
        
        
    def __del__( self ):
        self._mem_h5.close()
        
    def execute( self, slot, subindex, roi, destination ):
        if slot is self.LabelImage:
            for t in range(roi.start[0],roi.stop[0]):
                if t not in self._processedTimeSteps:
                    destination[t-roi.start[0]:t-roi.start[0]+1,...] = 0
                else:                                        
                    destination[t-roi.start[0]:t-roi.start[0]+1,...] = self._mem_h5['LabelImage'][roi.toSlice()]
            return destination
        
        if slot is self.LabelImageComputation:
            channels = self.BinaryImage.meta.shape[-1]
            for t in range(roi.start[0],roi.stop[0]):
                if t not in self._processedTimeSteps:
                    for c in range(channels):                    
                        print "Calculating LabelImage at t=" + str(t) + ", c=" + str(c) + " "                    
                        sroi = SubRegion(self.BinaryImage, start=[t,0,0,0,c], 
                                         stop=[t+1,] + list(self.BinaryImage.meta.shape[1:-1]) + [c+1,])
                        a = self.BinaryImage.get(sroi).wait()        
                        a = numpy.array(a[0,...,0],dtype=numpy.uint8)
                        backgroundLabel = self.BackgroundLabels.value[c]                        
                        if backgroundLabel != -1:
                            self._mem_h5['LabelImage'][t,...,c] = vigra.analysis.labelVolumeWithBackground( a, background_value = backgroundLabel )                     
                    self._processedTimeSteps.append(t)
  
    def propagateDirty(self, slot, subindex, roi):        
        if slot is self.BinaryImage:
            self.LabelImage.setDirty(roi)
        elif slot is self.BackgroundLabels: 
            self.LabelImage.setDirty(roi)
        else:
            print "Unknown dirty input slot: " + str(slot.name)
            


class OpRegionFeatures( Operator ):
    name = "Region Features"

    LabelImage = InputSlot()
    Output = OutputSlot( stype=Opaque, rtype=List )

    def __init__( self, parent=None, graph=None ):
        super(OpRegionFeatures, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

    def setupOutputs( self ):
        self.Output.meta.shape = self.LabelImage.meta.shape[0:1] # number of time steps
        self.Output.meta.dtype = object
    
    def execute( self, slot, subindex, roi, result ):
        if slot is self.Output:
            def extract( a ):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data, labels, features=['RegionCenter', 'Count', 'Coord<ArgMaxWeight>'], ignoreLabel=0)
                return feats
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers
                
            numChannels = self.LabelImage.meta.shape[-1]
            feats = {}            
            for t in roi:
                if t in self._cache:                    
                    feats_at = self._cache[t]
                elif self.fixed:
                    feats_at = { 'RegionCenter': numpy.asarray([[]]), 'Count': numpy.asarray([[]]), 'Coord<ArgMaxWeight>': numpy.asarray([[]]) }                    
                else:    
                    feats_at = []
                    for c in range(numChannels):
                        print "RegionFeatures at t=" + str(t) + ", c=" + str(c) + " "                                    
                        tcroi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 2) * [0,] 
                                           + [c,], stop = [t+1,] + list(self.LabelImage.meta.shape[1:-1]) + [c+1,])
                        a = self.LabelImage.get(tcroi).wait()
                        a = a[0,...,0] # assumes t,x,y,z,c
                        feats_at.append(extract(a))
                    self._cache[t] = feats_at
                feats[t] = feats_at

            return feats
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.LabelImage:
            self.Output.setDirty(List(self.Output, range(roi.start[0], roi.stop[0]))) 


class OpRegionCenters( Operator ):
    name = "Region Centers"
    
    LabelImage = InputSlot()
    Output = OutputSlot( stype=Opaque, rtype=List )

    
    def __init__( self, parent=None, graph=None ):
        super(OpRegionCenters, self).__init__(parent=parent,
                                              graph=graph)
        self._cache = {}
        self.fixed = True

    def setupOutputs( self ):        
        self.Output.meta.shape = self.LabelImage.meta.shape[0:1]
        self.Output.meta.dtype = object
    
    def execute( self, slot, subindex, roi, result ):
        if slot is self.Output:
            def extract( a ):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data, labels, features=['RegionCenter', 'Count'], ignoreLabel=0)
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers
            
            numChannels = self.LabelImage.meta.shape[-1]
            centers = {}
            for t in roi:                
                if t in self._cache:
                    centers_at = self._cache[t]
                elif self.fixed:
                    centers_at = numpy.asarray([], dtype=numpy.uint16)
                else:
                    centers_at = []
                    for c in range(numChannels):
                        print "RegionCenters at t=" + str(t) + ", c=" + str(c) + " "                                    
                        tcroi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 2) * [0,] 
                                           + [c,], stop = [t+1,] + list(self.LabelImage.meta.shape[1:-1] + [c+1,]))
                        a = self.LabelImage.get(tcroi).wait()
                        a = a[0,...,0] # assumes t,x,y,z,c
                        centers_at.append(extract(a))
                    self._cache[t] = centers_at
                centers[t] = centers_at                    

            return centers
        
    def propagateDirty(self, slot, subindex, roi):
        if slot is self.LabelImage:
            self.Output.setDirty(List(self.Output, range(roi.start[0], roi.stop[0]))) 


class OpObjectExtraction( Operator ):
    name = "Object Extraction"

    RawImage = InputSlot()# optional=True )
    BinaryImage = InputSlot()
    BackgroundLabels = InputSlot()

    LabelImage = OutputSlot()
    ObjectCenterImage = OutputSlot()
    RegionCenters = OutputSlot( stype=Opaque, rtype=List )
    RegionFeatures = OutputSlot( stype=Opaque, rtype=List )

    def __init__( self, parent = None, graph = None ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph)

        self._reg_cents = {}

        self._opLabelImage = OpLabelImage( parent=self, graph = graph )
        self._opLabelImage.BinaryImage.connect( self.BinaryImage )
        self._opLabelImage.BackgroundLabels.connect( self.BackgroundLabels)
        self.LabelImage.connect(self._opLabelImage.LabelImage)
        
        self._opRegCent = OpRegionCenters( parent=self, graph = graph )
        self._opRegCent.LabelImage.connect( self.LabelImage )

        self._opRegFeats = OpRegionFeatures( parent=self, graph = graph )
        self._opRegFeats.LabelImage.connect( self.LabelImage )

    def setupOutputs(self):
        m = self.BinaryImage.meta
        
        self._reg_cents = dict.fromkeys(xrange(m.shape[0]), numpy.asarray([], dtype=numpy.uint16))        
        
        self.ObjectCenterImage.meta.assignFrom(self.BinaryImage.meta)
        self.LabelImage.meta.assignFrom(self.BinaryImage.meta)
        self.RegionFeatures.meta.shape = self.BinaryImage.meta.shape[0:1] # number of timesteps
        self.RegionFeatures.meta.dtype = object
        self.RegionCenters.meta.shape = self.BinaryImage.meta.shape[0:1]  # number of timesteps
        self.RegionCenters.meta.dtype = object
                
        
    def execute(self, slot, subindex, roi, result):        
        if slot is self.ObjectCenterImage:
            return self._execute_ObjectCenterImage( roi, result )
        if slot is self.RegionCenters:
            res = self._opRegCent.Output.get( roi ).wait()
            return res
        if slot is self.RegionFeatures:
            res = self._opRegFeats.Output.get( roi ).wait()
            return res

    def __contained_in_subregion( self, roi, coords ):
        b = True
        for i in range(len(coords)):
            b = b and (roi.start[i] <= coords[i] and coords[i] < roi.stop[i])
        return b

    def __make_key( self, roi, coords ):
        return (coords[0] - roi.start[0],
                coords[1] - roi.start[1],
                coords[2] - roi.start[2],
                coords[3] - roi.start[3],
                coords[4] - roi.start[4],)
                
    
    def _execute_ObjectCenterImage( self, roi, result ):
        result[:] = 0
        for t in range(roi.start[0], roi.stop[0]):
            for ch in range(roi.start[-1], roi.stop[-1]):
                centers = self.RegionFeatures( [t] ).wait()[t][ch]['RegionCenter']
                centers = numpy.asarray( centers, dtype=numpy.uint32)
                if centers.size:
                    centers = centers[1:,:]
                for row in range(0,centers.shape[0]):
                    x = centers[row,0]
                    y = centers[row,1]
                    z = centers[row,2]
                
                    # mark center
                    c =  (t,x,y,z,ch)
                    if self.__contained_in_subregion( roi, c ): 
                        result[self.__make_key(roi,c)] = 255
    
                    # make the point into a cross
                    c =  (t,x-1,y,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y-1,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y,z-1,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
    
                    c =  (t,x+1,y,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y+1,z,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
                    c =  (t,x,y,z+1,0)
                    if self.__contained_in_subregion( roi, c ):
                        result[self.__make_key(roi, c)] = 255
        
        return result
