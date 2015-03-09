import cPickle as pickle

import numpy

import logging
logger = logging.getLogger(__name__)

import iiboost

from lazyflow.classifiers import LazyflowPixelwiseClassifierFactoryABC, LazyflowPixelwiseClassifierABC

class IIBoostLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    """
    This class adheres to the LazyflowPixelwiseClassifierFactoryABC interface, 
    which means it can be used by the standard classifier operators defined in lazyflow.
    
    Instances of this class can create trained instances of IIBoostLazyflowClassifier,
    which adheres to the LazyflowPixelwiseClassifierABC interface.
    
    NOTE: IIBoost needs three different (multi-channel) images:
          - raw data
          - hessian eigenvalues
          - feature channels
          
          To allow us to treat this classifier like a "normal" pixelwise classifier in ilastik/lazyflow,
          all three of images are passed in via the same numpy array.
          By convention, the input array must contain the following channels:
          channel 0: the raw grayscale data
          channel 1-9: the hessian eigenvectors, flattened into 9 channels
          channel 10-N: the remaining feature channels, (as selected by the user), 
                        which will be used below to compute integral images. 
    """
    VERSION = 1
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
    
    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None):
        """
        feature_images: A sequence of ND images.  See note above regarding required structure.  
                        Last axis must be channel.
        label_images: A sequence of ND label images.  Last axis must be channel (size=1).
        axistags: Optional.  A vigra.AxisTags object describing ALL feature_images.
        """
        logger.debug( 'training with IIBoost' )

        # Instantiate the classifier
        model = iiboost.Booster()

        # IIBoost requires both labels to be uint8, 3D only
        converted_labels = []
        for label_image in label_images:
            assert len(label_image.shape) == 4, "IIBoost expects 4D data (including channel dimension)."
            assert label_image.shape[-1] == 1, "Expected label image to have only one channel."
            converted = numpy.array( numpy.asarray(label_image[...,0], dtype=numpy.uint8) )
            converted_labels.append( converted )

        # IIBoost requires raw images to be uint8, 3D only
        # NOTE: we assume that the raw data can be found in channel 0.
        raw_images = []
        for image in feature_images:
            assert len(image.shape) == 4, "IIBoost expects 4D data (including channel)."
            raw = image[...,0].astype(dtype=numpy.uint8, order='C')
            raw_images.append( raw )

        # Extract the hessian eigenvector (hev) images
        hev_images = []
        for image in feature_images:
            hev_image = image[...,1:10]
            hev_image = hev_image.astype(dtype=numpy.float32, order='C')
            hev_image = hev_image.reshape( hev_image.shape[:-1] + (3,3) )
            hev_images.append( hev_image )

        # IIBoost requires filter images to be float32, 3D+c only
        filter_images = []
        for image in feature_images:
            assert len(image.shape) == 4, "IIBoost expects 4D data (including channel dimension)."
            filter_image = image[...,10:].astype(dtype=numpy.float32, copy=False)
            filter_images.append( filter_image )

        # Caching the integral images upstream would be difficult.
        # For now, we re-compute the integral images every time we train.
        integral_images = []
        for image in filter_images:
            integral_channels = []
            for channel_image in numpy.rollaxis(image, -1, 0):
                integral_channel = iiboost.computeIntegralImage( numpy.ascontiguousarray(channel_image) )
                integral_channels.append( integral_channel )
            integral_images.append( integral_channels )

        # Calculate anisotropy factor.
        z_anisotropy_factor = 1.0
        if axistags:
            x_tag = axistags['x']
            z_tag = axistags['z']
            if z_tag.resolution != 0.0 and x_tag.resolution != 0.0:
                z_anisotropy_factor = z_tag.resolution / x_tag.resolution
              
        model.trainWithChannels( raw_images, hev_images, converted_labels, integral_images, z_anisotropy_factor, *self._args, **self._kwargs )

        # Save for future reference
        flattened_labels = map( numpy.ndarray.flatten, converted_labels )
        all_labels = numpy.concatenate(flattened_labels)
        known_labels = numpy.unique(all_labels)
        if known_labels[0] == 0:
            known_labels = known_labels[1:]
            
        assert set([1,2]).issuperset(known_labels), "IIBoost only accepts two label values: 1 and 2"

        return IIBoostLazyflowClassifier( model, known_labels, feature_count=len(integral_images[0]) )

    def get_halo_shape(self, data_axes):
        # FIXME: What halo does IIBoost require?
        halo_shape = (100,) * (len(data_axes)-1)
        halo_shape += (0,) # no halo for channel
        return halo_shape

    @property
    def description(self):
        return "IIBoost Classifier"

    def __eq__(self, other):
        return (    isinstance(other, type(self))
                and self._args == other._args
                and self._kwargs == other._kwargs )
    def __ne__(self, other):
        return not self.__eq__(other)

# This assertion should pass if lazyflow is available.
from lazyflow.classifiers import LazyflowPixelwiseClassifierFactoryABC
assert issubclass( IIBoostLazyflowClassifierFactory, LazyflowPixelwiseClassifierFactoryABC )

class IIBoostLazyflowClassifier(LazyflowPixelwiseClassifierABC):
    """
    Adapt the IIBoost classifier to the interface lazyflow expects.    
    """
    def __init__(self, model, known_labels, feature_count):
        self._known_labels = known_labels
        self._model = model
        self._feature_count = feature_count
    
    def predict_probabilities_pixelwise(self, input_image, axistags=None):
        """
        feature_image: An ND image.  Last axis must be channel.
        axistags: Optional.  A vigra.AxisTags object describing the feature_image.
        
        NOTE: See note in factory class above concerning the expected structure of the input image.
        """
        logger.debug( 'predicting with IIBoost' )
        assert len(input_image.shape) == 4, "IIBoost expects 3D data."

        # IIBoost requires raw images to be uint8
        raw = input_image[...,0].astype(dtype=numpy.uint8, order='C')

        # Extract hessian eigenvalue channels
        hev_image = input_image[...,1:10].astype(dtype=numpy.float32, order='C')
        hev_image = hev_image.reshape( hev_image.shape[:-1] + (3,3) )
        
        # IIBoost requires filter images to be float32
        filter_image = input_image[...,10:].astype(dtype=numpy.float32, copy=False)

        # This is a debug class.  
        # As such, we recalculate the integral images every time...
        image_channels = list( numpy.rollaxis(filter_image, -1, 0) )
        image_channels = numpy.ascontiguousarray(image_channels)
        integral_channels = map( iiboost.computeIntegralImage, image_channels )

        # Calculate anisotropy factor.
        z_anisotropy_factor = 1.0
        if axistags:
            x_tag = axistags['x']
            z_tag = axistags['z']
            if z_tag.resolution != 0.0 and x_tag.resolution != 0.0:
                z_anisotropy_factor = z_tag.resolution / x_tag.resolution
        
        prediction_img = self._model.predictWithChannels( raw, hev_image, integral_channels, z_anisotropy_factor )
        assert prediction_img.dtype == numpy.float32
        print "prediction_img range: {}, {}".format( prediction_img.min(), prediction_img.max() )
        
        # Apparently the prediction image returned is NOT between 0.0 and 1.0
        prediction_img[:] -= prediction_img.min()
        prediction_img[:] /= prediction_img.max()
        
        assert prediction_img.min() == 0.0
        assert prediction_img.max() == 1.0
        
        # Image from model prediction has no channels,
        #  but lazyflow expects classifiers to produce one channel for each 
        #  label class.  Here, we simply generate the first channel by inverting the previous channel.
        prediction_img_reshaped = numpy.zeros( prediction_img.shape + (2,), dtype=numpy.float32 )
        
        if 1 in self._known_labels:
            prediction_img_reshaped[...,0] = 1.0-prediction_img
        if 2 in self._known_labels:
            prediction_img_reshaped[...,-1] = prediction_img
        
        assert prediction_img_reshaped.shape == input_image.shape[:-1] + (len(self._known_labels),), \
            "Output image had wrong shape. Expected: {}, Got {}"\
            "".format( input_image.shape[:-1] + (len(self._known_labels),), prediction_img_reshaped.shape )
        return prediction_img_reshaped
    
    @property
    def known_classes(self):
        return self._known_labels

    @property
    def feature_count(self):
        return self._feature_count

    def get_halo_shape(self, data_axes):
        # FIXME: What halo does IIBoost require?
        halo_shape = (100,) * (len(data_axes)-1)
        halo_shape += (0,) # no halo for channel
        return halo_shape

    def serialize_hdf5(self, h5py_group):
        h5py_group['known_labels'] = self._known_labels
        h5py_group['feature_count'] = self._feature_count
        
        # This field is required for all classifiers
        h5py_group['pickled_type'] = pickle.dumps( type(self) )
        
        # Just store the string IIBoost gives us
        h5py_group['serialized_model'] = self._model.serialize()

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        model_str = h5py_group['serialized_model'][()]
        model = iiboost.Booster()
        model.deserialize(model_str)
                
        known_labels = list(h5py_group['known_labels'][:])
        feature_count = h5py_group['feature_count'][()]
        return IIBoostLazyflowClassifier(model, known_labels, feature_count)

# This assertion should pass if lazyflow is available.
from lazyflow.classifiers import LazyflowPixelwiseClassifierABC
assert issubclass( IIBoostLazyflowClassifier, LazyflowPixelwiseClassifierABC )
