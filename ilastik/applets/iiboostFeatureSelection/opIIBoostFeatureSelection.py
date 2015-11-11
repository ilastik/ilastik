import copy
import numpy
import vigra
from functools import partial

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.operators.operators import OpSlicedBlockedArrayCache, OpUnblockedArrayCache
from lazyflow.roi import enlargeRoiForHalo, roiToSlice
from lazyflow.request import Request, RequestPool

from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
from iiboost import computeEigenVectorsOfHessianImage, computeIntegralImage

from ilastik.applets.base.applet import DatasetConstraintError

import logging
logger = logging.getLogger(__name__)

# By default, we pre-select the features listed in the IIBoost paper.
# (GGM from 1.0 - 5.0 and ST EVs from 1.0 - 5.0)
# The user can override these settings in the GUI.
ScalesList = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
FeatureIds = [ 'GaussianSmoothing',
               'LaplacianOfGaussian',
               'GaussianGradientMagnitude',
               'DifferenceOfGaussians',
               'StructureTensorEigenvalues',
               'HessianOfGaussianEigenvalues' ]

#                                sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
default_feature_matrix = numpy.array( [[ True, False, False, False, False, False, False],   # Gaussian
                                       [False, False, False, False, False, False, False],   # L of G
                                       [False, False,  True,  True,  True,  True, False],   # GGM
                                       [False, False, False, False, False, False, False],   # Diff of G
                                       [False, False,  True,  True,  True,  True, False],   # ST EVs
                                       [False, False, False, False, False, False, False]] ) # H of G EVs

class OpIIBoostFeatureSelection(Operator):
    """
    This operator produces an output image with the following channels:
    
    channel  0:       Raw Input (the input is just duplicated as an output channel)
    channels 1-10:    The 9 elements of the hessian eigenvector matrix (a 3x3 matrix flattened into 9 channels)
    channels 11-11+N: The 'integral images' of any features provided by the standard OpFeatureSelection operator.
    
    This operator owns an instance of the standard OpFeatureSelection operator, and 
    exposes the same slot interface so the GUI can configure that inner operator transparently. 
    """
    
    # All inputs are directly passed to internal OpFeatureSelection
    InputImage = InputSlot()
    Scales = InputSlot(value=ScalesList)
    FeatureIds = InputSlot(value=FeatureIds)
    SelectionMatrix = InputSlot(value=default_feature_matrix)
    FeatureListFilename = InputSlot(stype="str", optional=True)

    # This output is only for the GUI.  It's taken directly from OpFeatureSelection.
    # Unlike the OutputImage slot, it provides the raw features, NOT the integral images.
    FeatureLayers = OutputSlot(level=1)

    # These outputs are taken from OpFeatureSelection, but we add to them.
    OutputImage = OutputSlot()
    CachedOutputImage = OutputSlot()

    def __init__(self, filter_implementation, *args, **kwargs):
        super( OpIIBoostFeatureSelection, self ).__init__(*args, **kwargs)
        self.opFeatureSelection = OpFeatureSelection(filter_implementation, parent=self)
        
        self.opFeatureSelection.InputImage.connect( self.InputImage )
        self.opFeatureSelection.Scales.connect( self.Scales )
        self.opFeatureSelection.FeatureIds.connect( self.FeatureIds )
        self.opFeatureSelection.SelectionMatrix.connect( self.SelectionMatrix )
        self.opFeatureSelection.FeatureListFilename.connect( self.FeatureListFilename )        
        self.FeatureLayers.connect( self.opFeatureSelection.FeatureLayers )

        self.WINDOW_SIZE = self.opFeatureSelection.WINDOW_SIZE

        # The "normal" pixel features are integrated.
        self.opIntegralImage = OpIntegralImage( parent=self )
        self.opIntegralImage.Input.connect( self.opFeatureSelection.OutputImage )

        self.opIntegralImage_from_cache = OpIntegralImage( parent=self )
        self.opIntegralImage_from_cache.Input.connect( self.opFeatureSelection.CachedOutputImage )

        # We use an UNBLOCKED cache to store integral features, because a blocked cache would service 
        #  requests by concatenating neighboring blocks.  That is not a valid operation for integral images. 
        self.opIntegralImageCache = OpUnblockedArrayCache( parent=self )
        self.opIntegralImageCache.Input.connect( self.opIntegralImage_from_cache.Output )
                
        # Note: OutputImage and CachedOutputImage are not directly connected.
        #       Their data is obtained in execute(), below.
        
        self.opHessianEigenvectors = OpHessianEigenvectors( parent=self )
        self.opHessianEigenvectors.Input.connect( self.InputImage )
        
        # The operator above produces an image with weird axes,
        #  so let's convert it to a multi-channel image for easy handling.
        self.opConvertToChannels = OpConvertEigenvectorsToChannels( parent=self )
        self.opConvertToChannels.Input.connect( self.opHessianEigenvectors.Output )
        
        # Create a cache for the hessian eigenvector image data
        self.opHessianEigenvectorCache = OpSlicedBlockedArrayCache(parent=self)
        self.opHessianEigenvectorCache.name = "opHessianEigenvectorCache"
        self.opHessianEigenvectorCache.Input.connect(self.opConvertToChannels.Output)
        self.opHessianEigenvectorCache.fixAtCurrent.setValue(False)

        self.InputImage.notifyReady(self.checkConstraints)
        
        self.input_axistags = None
        self.InputImage.notifyMetaChanged(self._handleMetaChanged)
    
    def checkConstraints(self, *args):
        tagged_shape = self.InputImage.meta.getTaggedShape()
        if 't' in tagged_shape:
            raise DatasetConstraintError(
                 "IIBoost Pixel Classification: Feature Selection",
                 "This classifier handles only 3D data. Your input data has a time dimension, which is not allowed.")

        if not set('xyz').issubset(tagged_shape.keys()):
            raise DatasetConstraintError(
                 "IIBoost Pixel Classification: Feature Selection",
                 "This classifier handles only 3D data. Your input data does not have all three spatial dimensions (xyz).")

    def _handleMetaChanged(self, slot):
        if self.input_axistags != self.InputImage.meta.axistags:
            self.InputImage.setDirty( slice(None) )

    def setupOutputs(self):
        # Output shape is the same as the inner operator, 
        #  except with 10 extra channels (1 raw + 9 hessian eigenvector elements)
        output_shape = self.opIntegralImage.Output.meta.shape
        output_shape = output_shape[:-1] + ( output_shape[-1] + 10, )

        self.OutputImage.meta.assignFrom( self.opIntegralImage.Output.meta )
        self.CachedOutputImage.meta.assignFrom( self.opIntegralImageCache.Output.meta )
        self.OutputImage.meta.shape = output_shape
        self.CachedOutputImage.meta.shape = output_shape

        channel_names = ['Raw Data']
        channel_names += ['Hessian Eigenvectors Element {}'.format(i) for i in range(9)]
        channel_names += self.opIntegralImage.Output.meta.channel_names
        self.OutputImage.meta.channel_names = channel_names
        self.CachedOutputImage.meta.channel_names = channel_names

        # If we know the data resolution, fine-tune the hessian eigenvalue sigma
        x_tag = self.InputImage.meta.axistags['x']
        if x_tag.resolution != 0.0:
            # This formula comes from Carlos Becker (email from 2015-03-11)
            hessian_ev_sigma = 3.5 / 6.8 * x_tag.resolution
        else:
            hessian_ev_sigma = 3.5
        self.opHessianEigenvectors.Sigma.setValue( hessian_ev_sigma )

        # Copy the cache block settings from the standard pixel feature operator.
        self.opHessianEigenvectorCache.innerBlockShape.setValue( self.opFeatureSelection.opPixelFeatureCache.innerBlockShape.value )
        self.opHessianEigenvectorCache.outerBlockShape.setValue( self.opFeatureSelection.opPixelFeatureCache.outerBlockShape.value )

    def propagateDirty(self, slot, subindex, roi):
        # All channels are dirty
        num_channels = self.OutputImage.meta.shape[-1]
        dirty_start = tuple(roi.start[:-1]) + (num_channels,)
        dirty_stop = tuple(roi.stop[:-1]) + (num_channels,)
        self.OutputImage.setDirty(dirty_start, dirty_stop)

    def execute(self, slot, subindex, roi, result):
        assert slot == self.OutputImage or slot == self.CachedOutputImage

        # Combine all three 'feature' images into one big result
        spatial_roi = ( tuple(roi.start[:-1]), tuple(roi.stop[:-1]) )
        
        raw_roi = ( spatial_roi[0] + (0,),
                    spatial_roi[1] + (1,) )

        hess_ev_roi = ( spatial_roi[0] + (0,),
                        spatial_roi[1] + (9,) )

        features_roi = ( spatial_roi[0] + (0,),
                         spatial_roi[1] + (roi.stop[-1]-10,) )

        # Raw request is the same in either case (there is no cache)
        raw_req = self.InputImage(*raw_roi)
        if self.InputImage.meta.dtype == self.OutputImage.meta.dtype:
            raw_req.writeInto(result[...,0:1])
            raw_req.wait()
        else:
            # Can't use writeInto because we need an implicit dtype cast here.
            result[...,0:1] = raw_req.wait()            
        
        # Pull the rest of the channels from different sources, depending on cached/uncached slot.        
        if slot == self.OutputImage:
            hev_req = self.opConvertToChannels.Output(*hess_ev_roi).writeInto(result[...,1:10])
            feat_req = self.opIntegralImage.Output(*features_roi).writeInto(result[...,10:])
        elif slot == self.CachedOutputImage:
            hev_req = self.opHessianEigenvectorCache.Output(*hess_ev_roi).writeInto(result[...,1:10])
            feat_req = self.opIntegralImageCache.Output(*features_roi).writeInto(result[...,10:])
        
        hev_req.submit()
        feat_req.submit()
        hev_req.wait()
        feat_req.wait()

class OpHessianEigenvectors( Operator ):
    """
    Operator to call iiboost's hessian eigenvector function.
    Takes a 3D 1-channel image as input and returns a 5D xyzij output, 
    where the i,j axes are the eigenvector index and eigenvector element index, respectively.
    """
    Input = InputSlot()
    Sigma = InputSlot(value=3.5) # FIXME: What is the right sigma to use?
    Output = OutputSlot()
    
    WINDOW_SIZE = 2.0 # Used to calculate halo
    
    def __init__(self, *args, **kwargs):
        super( OpHessianEigenvectors, self ).__init__(*args, **kwargs)
        self.z_anisotropy_factor = 1.0
    
    def setupOutputs(self):
        assert len(self.Input.meta.shape) == 4, "Data must be exactly 3D+c (no time axis)"
        assert self.Input.meta.getAxisKeys()[-1] == 'c'
        assert self.Input.meta.shape[-1] == 1, "Input must be 1-channel"
        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.dtype = numpy.float32
        self.Output.meta.shape = self.Input.meta.shape[:-1] + (3,3)
        
        # axistags: start with input, drop channel and append i,j
        input_axistags = copy.copy(self.Input.meta.axistags)
        tag_list = [tag for tag in input_axistags]
        tag_list = tag_list[:-1]
        tag_list.append( vigra.AxisInfo('i', description='eigenvector index') )
        tag_list.append( vigra.AxisInfo('j', description='eigenvector component') )
        
        self.Output.meta.axistags = vigra.AxisTags(tag_list)

        # Calculate anisotropy factor.
        x_tag = self.Input.meta.axistags['x']
        z_tag = self.Input.meta.axistags['z']
        self.z_anisotropy_factor = 1.0
        if z_tag.resolution != 0.0 and x_tag.resolution != 0.0:
            self.z_anisotropy_factor = z_tag.resolution / x_tag.resolution
            logger.debug( "Anisotropy factor: {}/{} = {}".format( z_tag.resolution, x_tag.resolution, self.z_anisotropy_factor ) )
    
    def execute(self, slot, subindex, roi, result):
        # Remove i,j slices from roi, append channel slice to roi.
        input_roi = ( tuple(roi.start[:-2]) + (0,),
                      tuple(roi.stop[:-2]) + (1,) )

        enlarged_roi, result_roi = self._enlarge_roi_for_halo(*input_roi)
        
        # Request input
        input_data = self.Input(*enlarged_roi).wait()
        
        # Drop singleton channel axis
        input_data = input_data[...,0]
        
        # We need a uint8 array, in C-order.
        input_data = input_data.astype( numpy.uint8, order='C', copy=False )

        # Compute. (Note that we drop the 
        eigenvectors = computeEigenVectorsOfHessianImage(input_data, 
                                                         zAnisotropyFactor=self.z_anisotropy_factor, 
                                                         sigma=self.Sigma.value)
        
        # sanity checks...
        assert (eigenvectors.shape[:-2] == (numpy.array(enlarged_roi[1]) - enlarged_roi[0])[:-1]).all(), \
            "eigenvector image has unexpected shape: {}".format( eigenvectors.shape )
        assert eigenvectors.shape[-2:] == (3,3)

        # Copy to output.
        
        result[:] = eigenvectors[roiToSlice(*result_roi)][..., slice(roi.start[-1], roi.stop[-1])]

    def propagateDirty(self, slot, subindex, roi):
        if slot is self.Sigma:
            self.Output.setDirty( slice(None) )
        elif slot is self.Input:
            enlarged_roi, _ = self._enlarge_roi_for_halo(roi.start, roi.stop)
    
            dirty_start = tuple(enlarged_roi[0, :-1]) + (0,0)
            dirty_stop = tuple(enlarged_roi[1, :-1]) + (3,3)
            self.Output.setDirty(dirty_start, dirty_stop)
        else:
            assert False, 'Unhandled dirty slot: {}'.format( slot )

    def _enlarge_roi_for_halo(self, start, stop):
        """
        Given a roi of INPUT coordinates (3D+c, not 3D+ij),
          enlarge it with an appropriate halo.  Also return the "result roi".
        (See enlargeRoiForHalo() docs for details.)
        """
        assert len(self.Input.meta.shape) == 4, "Data must be exactly 3D+c (no time axis)"
        assert self.Input.meta.getAxisKeys()[-1] == 'c'

        spatial_axes = (True, True, True, False) # don't enlarge channel roi
        enlarged_roi, result_roi = enlargeRoiForHalo( start, 
                                                      stop, 
                                                      self.Input.meta.shape, 
                                                      self.Sigma.value, 
                                                      window=self.WINDOW_SIZE, 
                                                      enlarge_axes=spatial_axes,
                                                      return_result_roi=True )
        return enlarged_roi, result_roi

class OpConvertEigenvectorsToChannels(Operator):
    """
    Reshapes the 3D+i,j output from OpHessianEigenvectors into a 3D+c array, 
    where the 3x3 i,j axes have been converted to a single (9,) channel axis.
    
    This is only useful because most operators in lazyflow expect a channel axis, 
    and don't know how to handle (i,j) pixels.
    
    (This operator doesn't do any real 'work', it just reshapes the input.)
    """
    Input = InputSlot()
    Output = OutputSlot()
    
    def setupOutputs(self):
        input_shape = self.Input.meta.shape
        input_axiskeys = self.Input.meta.getAxisKeys()
        assert input_shape[-2:] == (3,3)
        assert input_axiskeys[-2:] == ['i', 'j']

        tag_list = [tag for tag in self.Input.meta.axistags]
        tag_list = tag_list[:-2]
        tag_list.append( vigra.defaultAxistags('c')[0] )

        self.Output.meta.assignFrom(self.Input.meta)
        self.Output.meta.shape = input_shape[:-2] + (9,)
        self.Output.meta.axistags = vigra.AxisTags(tag_list)

    def execute(self, slot, subindex, roi, result):
        # We could go through the necessary contortions to avoid this requirement, 
        #  but it's not a realistic use-case for now.
        assert roi.start[-1] == 0, "Requests to this operator must include all channels"
        assert roi.stop[-1] == 9, "Requests to this operator must include all channels"
        
        input_roi = ( tuple(roi.start[:-1]) + (0,0),
                      tuple(roi.stop[:-1]) + (3,3) )
        
        input_shape = numpy.array(input_roi[1]) - input_roi[0]

        if result.flags["C_CONTIGUOUS"]:
            result = result.reshape( input_shape )
            self.Input(*input_roi).writeInto(result).wait()
        else:
            input_data = self.Input(*input_roi).wait()
            assert input_data.shape[-2:] == (3,3)
            input_data = input_data.reshape(input_data.shape[:-2] + (9,))
            assert input_data.shape == result.shape
            result[:] = input_data[:]
        
    def propagateDirty(self, slot, subindex, roi):
        dirty_start = tuple(roi.start[:-2]) + (0,)
        dirty_stop = tuple(roi.stop[:-2]) + (9,)
        self.Output.setDirty(dirty_start, dirty_stop)
            
class OpIntegralImage(Operator):
    """
    Computes the integral image of the input volume.
    For multi-channel volumes, the integral image for each channel is computed independently.
    
    The integral image operation is equivalent to:

    output = input_image.copy()
    for i in range(a.ndim):
        np.add.accumulate(output, axis=i, out=output)

    (That is, simply integrate over all axes of the volume.)
    
    But here, we use iiboost.computeIntegralImage() because 
      it seems to be faster than the above numpy code.
    """ 
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        assert len(self.Input.meta.shape) == 4, "Data must be exactly 3D+c (no time axis)"
        assert self.Input.meta.getAxisKeys()[-1] == 'c'

        self.Output.meta.assignFrom( self.Input.meta )
        self.Output.meta.dtype = numpy.float32
        
        if self.Input.meta.channel_names:
            self.Output.meta.channel_names = ["Integrated " + name for name in self.Input.meta.channel_names]

    def execute(self, slot, subindex, roi, result):

        def compute_for_channel(output_channel, input_channel):
            input_roi = numpy.array( (roi.start, roi.stop) )
            input_roi[:,-1] = (input_channel, input_channel+1)
            input_req = self.Input(*input_roi)

            # If possible, use the result array itself as a scratch area
            if self.Input.meta.dtype == result.dtype:
                input_req.writeInto( result[...,output_channel:output_channel+1] )        

            input_data = input_req.wait()
            input_data = input_data.astype(numpy.float32, order='C', copy=False)
            input_data = input_data[...,0] # drop channel axis
            result[..., output_channel] = computeIntegralImage(input_data)

        pool = RequestPool()
        for output_channel, input_channel in enumerate(range(roi.start[-1], roi.stop[-1])):
            pool.add( Request( partial( compute_for_channel, output_channel, input_channel ) ) )
        pool.wait()
    
    def propagateDirty(self, slot, subindex, roi):
        self.Output.setDirty(roi.start, roi.stop)

