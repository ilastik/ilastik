import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot, MultiInputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader


class OpLabelImage( Operator ):
    BinaryImage = InputSlot()
    LabelImageWithBackground = OutputSlot()

    def setupOutputs( self ):
        self.LabelImageWithBackground.meta.assignFrom( self.BinaryImage.meta )

    def execute( self, slot, roi, destination ):
        if slot is self.LabelImageWithBackground:
            a = self.BinaryImage.get(roi).wait()
            assert(a.shape[0] == 1)
            assert(a.shape[-1] == 1)
            destination[0,...,0] = vigra.analysis.labelVolumeWithBackground( a[0,...,0] )
            return destination

class OpRegionCenters( Operator ):
    LabelImage = InputSlot()
    Output = OutputSlot( stype=Opaque, rtype=list )

    
    def __init__( self, parent=None, graph=None, register=True ):
        super(OpRegionCenters, self).__init__(parent=parent,
                                              graph=graph,
                                              register=register)
        self._cache = {}

    def setupOutputs( self ):
        self.Output.meta.shape = self.LabelImage.meta.shape
        self.Output.meta.dtyp = self.LabelImage.meta.dtype
    
    def execute( self, slot, roi, result ):
        if slot is self.Output:
            def extract( a ):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                feats = vigra.analysis.extractRegionFeatures(data, labels, features=['RegionCenter'], ignoreLabel=0)
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers
                
            centers = {}
            for t in roi:
                if t in self._cache:
                    centers_at = self._cache[t]
                else:
                    troi = SubRegion( self.LabelImage, start = [t,] + (len(self.LabelImage.meta.shape) - 1) * [0,], stop = [t+1,] + list(self.LabelImage.meta.shape[1:]))
                    a = self.LabelImage.get(troi).wait()
                    a = a[0,...,0] # assumes t,x,y,z,c
                    centers_at = extract(a)
                    self._cache[t] = centers_at
                centers[t] = centers_at

            return centers

class OpObjectExtraction( Operator ):
    name = "Object Extraction"

    #RawData = InputSlot()
    BinaryImage = InputSlot()
    #FeatureNames = InputSlot( stype=Opaque )

    LabelImage = OutputSlot()
    RegionCenters = OutputSlot( stype=Opaque, rtype=list )

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph,register=register)

        self._mem_h5 = h5py.File(str(id(self)), driver='core', backing_store=False)

        self._opLabelImage = OpLabelImage( graph = graph )
        self._opLabelImage.BinaryImage.connect( self.BinaryImage )

        self._opRegCent = OpRegionCenters( graph = graph )

        self._regCents_cache = {}
    
    def __del__( self ):
        self._mem_h5.close()

    def setupOutputs(self):
        self.LabelImage.meta.assignFrom(self.BinaryImage.meta)
        m = self.LabelImage.meta
        self._mem_h5.create_dataset( 'LabelImage', shape=m.shape, dtype=m.dtype, compression=1 )
    
    def execute(self, slot, roi, result):
        if slot is self.LabelImage:
            result = self._mem_h5['LabelImage'][roi.toSlice()]
            return result
        if slot is self.RegionCenters:
            res = self._opRegCent.Output.get( roi ).wait()
            return res

    def propagateDirty(self, inputSlot, roi):
        raise NotImplementedError

    def updateLabelImage( self ):
        m = self.LabelImage.meta
        for t in range(0, 1):#meta.shape[0]):
            print "Calculating LabelImage at", t
            start = [t,] + (len(m.shape) - 1) * [0,]
            stop = [t+1,] + list(m.shape[1:])
            a = self.BinaryImage.get(SubRegion(self.BinaryImage, start=start, stop=stop)).wait()
            a = a[0,...,0]
            self._mem_h5['LabelImage'][0,...,0] = vigra.analysis.labelVolumeWithBackground( a )
        self.LabelImage.setDirty(SubRegion(self.LabelImage))
