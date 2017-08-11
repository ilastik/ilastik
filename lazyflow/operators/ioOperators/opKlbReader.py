from __future__ import print_function
import numpy
import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot

try:
    import pyklb
    _klb_available = True
except ImportError:
    _klb_available = False

class OpKlbReader( Operator ):
    """
    Reads .klb files (Keller Lab Block Filetype).
    Requires the 'pyklb' package.
    
    See:
        - https://bitbucket.org/fernandoamat/keller-lab-block-filetype
        - https://github.com/bhoeckendorf/pyklb
    """
    FilePath = InputSlot()
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpKlbReader, self).__init__(*args, **kwargs)
        self._filepath = None

        # Late import here just to trigger an ImportError if klb isn't available.
        import pyklb
    
    def setupOutputs(self):        
        self._filepath = self.FilePath.value
        header = pyklb.readheader(self._filepath)
        
        self.Output.meta.shape = tuple(header['imagesize_tczyx'])
        self.Output.meta.axistags = vigra.defaultAxistags('tczyx')
        self.Output.meta.dtype = header['datatype'].type

    def execute(self, slot, subindex, roi, result):
        if result.flags.c_contiguous:
            pyklb.readroi_inplace(result, self._filepath, roi.start, roi.stop-1, nochecks=False)
        else:
            result[:] = pyklb.readroi(self._filepath, roi.start, roi.stop-1)

    def propagateDirty(self, slot, subindex, roi):
        assert slot is self.FilePath, \
            "Unknown input slot: {}".format( slot.name )
        self.Output.setDirty( slice(None) )

    def cleanUp(self):
        super( OpKlbReader, self ).cleanUp()

if __name__ == "__main__":
    from lazyflow.graph import Graph
    
    op = OpKlbReader(graph=Graph())
    op.FilePath.setValue("/tmp/deleteme-2.klb")
    
    print(op.Output.meta.shape)
    print(op.Output.meta.getAxisKeys())
    print(op.Output.meta.dtype)
    
    a = op.Output[:].wait()
    print(numpy.mean(a))
    