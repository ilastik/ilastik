import warnings
import numpy

# Note: tifffile can also be imported from skimage.external.tifffile.tifffile_local,
#       but we can't use that module because it is based on a version of tifffile that has a bug.
#       (It doesn't properly import the tifffile.c extension module.)
#import skimage.external.tifffile.tifffile_local as tifffile
import tifffile

import vigra
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.roi import roiToSlice
from lazyflow.request import RequestLock

import logging
logger = logging.getLogger(__name__)

class OpTiffReader(Operator):
    """
    Reads TIFF files as an ND array. We use two different libraries:
    
    - To read the image metadata (determine axis order), we use tifffile.py (by Christoph Gohlke)
    - To actually read the data, we use vigra (which supports more compression types, e.g. JPEG)
    
    Note: This operator intentionally ignores any colormap 
          information and uses only the raw stored pixel values.
          (In fact, avoiding the colormapping is not trivial using the tifffile implementation.)
    
    TODO: Add an option to output color-mapped pixels.
    """
    Filepath = InputSlot()
    Output = OutputSlot()

    TIFF_EXTS = ['.tif', '.tiff']
    
    def __init__(self, *args, **kwargs):
        super( OpTiffReader, self ).__init__( *args, **kwargs )
        self._filepath = None
        self._page_shape = None
    
    def setupOutputs(self):
        assert map(int, tifffile.__version__.split('.')) >= [0,9,2], \
            "This code requires at tifffile 0.9.2 or greater."

        self._filepath = self.Filepath.value
        with tifffile.TiffFile(self._filepath) as tiff_file:
            series = tiff_file.series[0]
            if len(tiff_file.series) > 1:
                raise RuntimeError("Don't know how to read TIFF files with more than one image series.\n"
                                   "(Your image has {} series".format( len(tiff_file.series) ))
    
            axes = series.axes
            shape = series.shape
            pages = series.pages
            first_page = pages[0]
    
            dtype_code = first_page.dtype
            if first_page.is_indexed:
                # For now, we don't support colormaps.
                # Drop the (last) channel axis
                # (Yes, there can be more than one :-/)
                last_C_pos = axes.rfind('C')
                assert axes[last_C_pos] == 'C'
                axes = axes[:last_C_pos] + axes[last_C_pos+1:]
                shape = shape[:last_C_pos] + shape[last_C_pos+1:]
    
                # first_page.dtype refers to the type AFTER colormapping.
                # We want the original type.
                key = (first_page.sample_format, first_page.bits_per_sample)
                dtype_code = self._dtype = tifffile.TIFF_SAMPLE_DTYPES.get(key, None)
                
            # From the tifffile.TiffPage code:
            # -----
            # The internal, normalized '_shape' attribute is 6 dimensional:
            # 
            # 0. number planes  (stk)
            # 1. planar samples_per_pixel
            # 2. image_depth Z  (sgi)
            # 3. image_length Y
            # 4. image_width X
            # 5. contig samples_per_pixel
    
            (N, P, D, Y, X, S) = first_page._shape
            assert N == 1, "Don't know how to handle any number of planes except 1 (per page)"
            assert P == 1, "Don't know how to handle any number of planar samples per pixel except 1 (per page)"
            assert D == 1, "Don't know how to handle any image depth except 1"
    
            if S == 1:
                self._page_shape = (Y,X)
                self._page_axes = 'yx'
            else:
                assert shape[-3:] == (Y,X,S)
                self._page_shape = (Y,X,S)
                self._page_axes = 'yxc'
                assert 'C' not in axes, \
                    "If channels are in separate pages, then each page can't have multiple channels itself.\n"\
                    "(Don't know how to weave multi-channel pages together.)"
    
            self._non_page_shape = shape[:-len(self._page_shape)]
            assert shape == self._non_page_shape + self._page_shape
            assert self._non_page_shape or len(pages) == 1
            
            axes = axes.lower().replace('s', 'c')
            axes = list(axes)

            for i, axis in enumerate(axes):
                if axis not in 'tzcyx':
                    for k in 'tzc':
                        if k not in axes:
                            axes[i] = k
                            warnings.warn( "Encountered unknown TIFF axis label '{}'.  Re-interpreting as '{}'"
                                           .format( axis.upper(), k.upper() ) )
                            break
                    if axis in axes:
                        raise RuntimeError("Image has an 'I' or 'Q' (unknown) axis type, and I don't know what it represents. "
                                           "(Separate T,Z,C axes already exist.)")
            
            axes = "".join(axes)
            
            self.Output.meta.shape = shape
            self.Output.meta.axistags = vigra.defaultAxistags( axes )
            self.Output.meta.dtype = numpy.dtype(dtype_code).type
            self.Output.meta.ideal_blockshape = ((1,) * len(self._non_page_shape)) + self._page_shape

    def execute(self, slot, subindex, roi, result):
        """
        Use vigra (not tifffile) to read the result.
        This allows us to support JPEG-compressed TIFFs.
        """
        num_page_axes = len(self._page_shape)
        roi = numpy.array( [roi.start, roi.stop] )
        page_index_roi = roi[:, :-num_page_axes]
        roi_within_page = roi[:, -num_page_axes:]

        logger.debug("Roi: {}".format(map(tuple, roi)))

        # Read each page out individually
        page_index_roi_shape = page_index_roi[1] - page_index_roi[0]
        for roi_page_ndindex in numpy.ndindex(*page_index_roi_shape):
            if self._non_page_shape:
                tiff_page_ndindex = roi_page_ndindex + page_index_roi[0]
                tiff_page_list_index = numpy.ravel_multi_index(tiff_page_ndindex, self._non_page_shape)
                logger.debug( "Reading page: {} = {}".format( tuple(tiff_page_ndindex), tiff_page_list_index ) )
                page_data = vigra.impex.readImage(self._filepath, dtype='NATIVE', index=int(tiff_page_list_index), order='C')
            else:
                # Only a single page
                page_data = vigra.impex.readImage(self._filepath, dtype='NATIVE', index=0, order='C')

            page_data = page_data.withAxes(self._page_axes)
            assert page_data.shape == self._page_shape, \
                "Unexpected page shape: {} vs {}".format( page_data.shape, self._page_shape )
            
            result[ roi_page_ndindex ] = page_data[roiToSlice(*roi_within_page)]

    def propagateDirty(self, slot, subindex, roi):
        if slot == self.Filepath:
            self.Output.setDirty( slice(None) )

if __name__ == "__main__":
    from lazyflow.graph import Graph
    
    graph = Graph()
    opReader = OpTiffReader(graph=graph)
    opReader.Filepath.setValue('/tmp/out.ome.tiff')
    print opReader.Output.meta.axistags
    print opReader.Output.meta.shape
    print opReader.Output.meta.dtype
    #print opReader.Output[2:3,2:3,2:3,10:20,20:50].wait().shape

#     opReader.Filepath.setValue('/magnetic/data/synapse_small.tiff')
#     print opReader.Output.meta.axistags
#     print opReader.Output.meta.shape
#     print opReader.Output.meta.dtype

