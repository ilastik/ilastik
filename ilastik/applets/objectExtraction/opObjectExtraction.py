import numpy
import h5py

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader

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
                    print "Cached!"
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
    #Segmentation = InputSlot()
    #FeatureNames = InputSlot( stype=Opaque )

    LabelImage = OutputSlot()
    RegionCenters = OutputSlot( stype=Opaque, rtype=list )

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph,register=register)

        self._mem_h5 = h5py.File('mem.h5', driver='core', backing_store=False)
        with h5py.File('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5', 'r') as f:
            f.copy('/objects', self._mem_h5)
            f.copy('/seg', self._mem_h5)

        self._labelImageReader = OpStreamingHdf5Reader( graph = graph )
        self._labelImageReader.Hdf5File.setValue(self._mem_h5)
        self._labelImageReader.InternalPath.setValue('/objects')

        self._segReader = OpStreamingHdf5Reader( graph = graph )
        self._segReader.Hdf5File.setValue(self._mem_h5)
        self._segReader.InternalPath.setValue('/seg')

        self._opRegCent = OpRegionCenters( graph = graph )
        self._opRegCent.LabelImage.connect(self._labelImageReader.OutputImage)

        self._regCents_cache = {}
    
    def __del__( self ):
        self._mem_h5.close()

    def setupOutputs(self):
        self.LabelImage.meta.assignFrom(self._labelImageReader.OutputImage.meta)
    
    def execute(self, slot, roi, result):
        if slot is self.LabelImage:
            res = self._labelImageReader.OutputImage.get(roi).wait()
            return res
        if slot is self.RegionCenters:
            res = self._opRegCent.Output.get( roi ).wait()
            return res

    def propagateDirty(self, inputSlot, roi):
        raise NotImplementedError

