from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opArrayCache import OpArrayCache
from lazyflow.operators.ioOperators import OpTiledVolumeReader

import logging
logger = logging.getLogger(__name__)

class OpCachedTiledVolumeReader(Operator):
    DescriptionFilePath = InputSlot(stype='filestring')
    Output = OutputSlot()

    def __init__(self, *args, **kwargs):
        super( OpCachedTiledVolumeReader, self ).__init__( *args, **kwargs )
        self._opReader = OpTiledVolumeReader(parent=self)
        self._opReader.DescriptionFilePath.connect( self.DescriptionFilePath )
        
        self._opCache = OpArrayCache(parent=self)        
        self._opCache.Input.connect( self._opReader.Output )
        
        self.Output.connect( self._opCache.Output )
    
    def setupOutputs(self):
        # Set the cache blockshape to match the source tiles.
        tile_shape = list(self._opReader.tiled_volume.description.tile_shape_2d)
        assert tile_shape[0] == tile_shape[1], "FIXME: This code assumes square tiles."
        
        z_index = self._opReader.Output.meta.getAxisKeys().index('z')
        tile_shape.insert(z_index, 1)
        self._opCache.blockShape.setValue( tuple(tile_shape) )
        
    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass
