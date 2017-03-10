from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache
from lazyflow.operators.ioOperators import OpTiledVolumeReader

import logging
logger = logging.getLogger(__name__)

class OpCachedTiledVolumeReader(Operator):
    DescriptionFilePath = InputSlot(stype='filestring')

    VolumeDescription = OutputSlot()
    CachedOutput = OutputSlot()
    UncachedOutput = OutputSlot()
    
    SpecifiedOutput = OutputSlot()  # specified as either Cached or Uncached in the 
                                    # volume description file, depending on the 'cache_tiles' setting.

    def __init__(self, *args, **kwargs):
        super( OpCachedTiledVolumeReader, self ).__init__( *args, **kwargs )
        self._opReader = OpTiledVolumeReader(parent=self)
        self._opReader.DescriptionFilePath.connect( self.DescriptionFilePath )
        
        self.UncachedOutput.connect( self._opReader.Output )
        
        self._opCache = OpBlockedArrayCache(parent=self)        
        self._opCache.Input.connect( self._opReader.Output )
        self._opCache.fixAtCurrent.setValue(False)
        
        self.CachedOutput.connect( self._opCache.Output )
    
    def setupOutputs(self):
        # Set the cache blockshape to match the source tiles.
        tile_shape = list(self._opReader.tiled_volume.description.tile_shape_2d_yx)
        assert tile_shape[0] == tile_shape[1], "FIXME: This code assumes square tiles."
        
        z_index = self._opReader.Output.meta.getAxisKeys().index('z')
        tile_shape.insert(z_index, 1)
        self._opCache.innerBlockShape.setValue( tuple(tile_shape) )
        self._opCache.BlockShape.setValue( tuple(tile_shape) )

        self.VolumeDescription.setValue( self._opReader.tiled_volume.description )
        
        if self._opReader.tiled_volume.description.cache_tiles:
            self.SpecifiedOutput.connect( self._opCache.Output )
        else:
            self.SpecifiedOutput.connect( self._opReader.Output )

    def execute(self, slot, subindex, roi, result):
        assert False, "Shouldn't get here."

    def propagateDirty(self, slot, subindex, roi):
        pass
