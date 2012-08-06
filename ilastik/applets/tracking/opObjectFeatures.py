import vigra 
import vigra.analysis
import numpy as np
import numpy
import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.request import Request

class OpRegionCenters( Operator ):
    LabelImage = InputSlot()
    Output = OutputSlot( stype=Opaque )

    
    def __init__( self, parent=None, graph=None, register=True ):
        super(OpRegionCenters, self).__init__(parent=parent,
                                              graph=graph,
                                              register=register)
        pass

    def setupOutputs( self ):
        self.Output.meta.shape = self.LabelImage.meta.shape
    
    def execute( self, slot, roi, result ):
        if slot is self.Output:
            def extract( a ):
                labels = numpy.asarray(a, dtype=numpy.uint32)
                data = numpy.asarray(a, dtype=numpy.float32)
                print "opRegCent: extracting", t
                feats = vigra.analysis.extractRegionFeatures(data, labels, features=['RegionCenter'], ignoreLabel=0)
                print "opRegCents: done"
                centers = numpy.asarray(feats['RegionCenter'], dtype=numpy.uint16)
                centers = centers[1:,:]
                return centers
                
            print "opRegCent: loading"
            reqs = []
            for t in range(roi.start[0], roi.stop[0]):
                troi = copy.copy(roi)
                troi.start[0] = t
                troi.stop[0] = t + 1
                a = self.LabelImage.get(troi).wait()
                a = a[0,...,0]

                
                print "requested at ", t
                res = extract(a)


            return None
