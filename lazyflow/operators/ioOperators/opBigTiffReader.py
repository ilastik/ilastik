import numpy as np
import pytiff
import vigra

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice

import logging
logger = logging.getLogger(__name__)

class OpBigTiffReader(Operator):
    Filepath = InputSlot()
    Output = OutputSlot()

    TIFF_EXTS = ['.tif', '.tiff']

    class NotBigTiffError(Exception):
        """Raised if the file you're attempting to open isn't a BigTiff file."""
    
    def __init__(self, *args, **kwargs):
        super( OpBigTiffReader, self ).__init__( *args, **kwargs )
        self._bigtiff = None

    def cleanUp(self):
        if self._bigtiff is not None:
            self._bigtiff.close()
        super(OpBigTiffReader, self).cleanUp()

    def setupOutputs(self):
        filepath = self.Filepath.value

        with open(filepath, 'r') as f:
            # inspect the 3rd byte of the header
            # For regular tiff, should be 0x2a
            # For BigTiff, should be 0x2b
            header_start = f.read(4)
            if ord(header_start[2]) == 0x2a:
                raise OpBigTiffReader.NotBigTiffError(filepath)
            if ord(header_start[2]) != 0x2b:
                raise RuntimeError(
                    "File '{}' does not appear to start with a valid tiff or bigtiff header."
                    .format(filepath))

        bigtiff = pytiff.Tiff(filepath)

        if bigtiff.number_of_pages != 1:
            raise RuntimeError("Multipage BigTiff not supported yet.")

        
        self.Output.meta.dtype = bigtiff.dtype

        if bigtiff.samples_per_pixel > 1:
            self.Output.meta.shape = bigtiff.shape + (bigtiff.samples_per_pixel,)
            self.Output.meta.axistags = vigra.defaultAxistags('yxc')
        else:
            self.Output.meta.shape = bigtiff.shape
            self.Output.meta.axistags = vigra.defaultAxistags('yx')

        self._bigtiff = bigtiff
    
    def execute(self, slot, subindex, roi, result):
        if 'c' in self.Output.meta.axistags:
            # pytiff is weird about channel data.
            # We've got to request all channels first, and select between them ourselves.
            # (pytiff.Tiff.__getitem__ seems to always give us all channels, regardless of what we asked for.)
            
            # Futhermore, when I load the pytiff sample RGB TIFF image,
            # pytiff says it has samples_per_pixel == 3,
            # but pytiff says its shape == (400, 640, 4)
            # No idea why that is (alpha, maybe?)
            # For now, I just ignore that last channel and hope for the best...
            roi = np.array([roi.start, roi.stop])
            all_channels = self._bigtiff[roiToSlice(*roi[:,:2])]
            result[:] = all_channels[..., slice(*roi[:,-1])]
        else:
            result[:] = self._bigtiff[roiToSlice(roi.start, roi.stop)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty( slice(None) )

#
# Quick test
#
if __name__ == "__main__":
    from lazyflow.graph import Graph
    
    op = OpBigTiffReader(graph=Graph())
    #op.Filepath.setValue('/magnetic/workspace/pytiff/test_data/rgb_sample.tif')
    op.Filepath.setValue('/magnetic/workspace/pytiff/test_data/bigtif_example.tif')
    
    print op.Output.meta.shape
    print op.Output.meta.dtype
    print op.Output.meta.getAxisKeys()
    print op.Output[:10,:10].wait()
