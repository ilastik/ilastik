import numpy
import h5py

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader


class OpObjectExtraction( Operator ):
    name = "Object Extraction"

    #RawData = InputSlot()
    #Segmentation = InputSlot()
    #FeatureNames = InputSlot( stype=Opaque )

    LabelImage = OutputSlot()
    Objects = OutputSlot( stype=Opaque )

    def __init__( self, parent = None, graph = None, register = True ):
        super(OpObjectExtraction, self).__init__(parent=parent,graph=graph,register=register)

        self._mem_h5 = h5py.File('mem.h5', driver='core', backing_store=False)
        with h5py.File('/home/bkausler/src/ilastik/tracking/relabeled-stack/objects.h5', 'r') as f:
            f.copy('/objects', self._mem_h5)

        self._labelImageReader = OpStreamingHdf5Reader( graph = graph )
        self._labelImageReader.Hdf5File.setValue(self._mem_h5)
        self._labelImageReader.InternalPath.setValue('/objects')
    
    def __del__( self ):
        self._mem_h5.close()

    def setupOutputs(self):
        self.LabelImage.meta.assignFrom(self._labelImageReader.OutputImage.meta)
    
    def execute(self, slot, roi, result):
        if slot is self.LabelImage:
            res = self._labelImageReader.OutputImage.get(roi).wait()
            return res
        

    def propagateDirty(self, inputSlot, roi):
        pass

