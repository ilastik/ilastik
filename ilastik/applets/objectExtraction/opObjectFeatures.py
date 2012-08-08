import vigra 
import vigra.analysis
import numpy as np
import numpy
import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import SubRegion
from lazyflow.request import Request

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
