import cPickle as pickle

import numpy

import logging
logger = logging.getLogger(__name__)

import IIBoost

from lazyflow.classifiers import LazyflowPixelwiseClassifierFactoryABC, LazyflowPixelwiseClassifierABC

class IIBoostLazyflowClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    """
    This class adheres to the LazyflowPixelwiseClassifierFactoryABC interface, 
    which means it can be used by the standard classifier operators defined in lazyflow.
    
    Instances of this class can create trained instances of IIBoostLazyflowClassifier,
    which adheres to the LazyflowPixelwiseClassifierABC interface.
    """
    VERSION = 1
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
    
    def create_and_train_pixelwise(self, orig_filter_images, label_images):
        logger.debug( 'training with IIBoost' )

        # Instantiate the classifier
        model = IIBoost.Booster()

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
        for image in orig_filter_images:
            assert len(image.shape) == 4, "IIBoost expects 4D data (including channel)."
            raw = numpy.asarray(image[...,0], dtype=numpy.uint8)
            raw = numpy.array( raw )
            raw_images.append( raw )

        # IIBoost requires filter images to be float32, 3D+c only
        filter_images = []
        for image in orig_filter_images:
            assert len(image.shape) == 4, "IIBoost expects 4D data (including channel dimension)."
            filter_image = numpy.asarray(image, dtype=numpy.float32)
            filter_image = numpy.array(image)
            filter_images.append( filter_image )

        # This is a debug class.  
        # As such, we recalculate the integral images every time...                
        integral_images = []
        for image in filter_images:
            integral_channels = []
            for channel_image in numpy.rollaxis(image, -1, 0):
                integral_channel = model.computeIntegralImage( channel_image )
                integral_channels.append( integral_channel )
            integral_images.append( integral_channels )

        # Finally, train!
        model.trainWithChannels( raw_images, converted_labels, integral_images, *self._args, **self._kwargs )

        # Save for future reference
        flattened_labels = map( numpy.ndarray.flatten, converted_labels )
        all_labels = numpy.concatenate(flattened_labels)
        known_labels = numpy.unique(all_labels)
        if known_labels[0] == 0:
            known_labels = known_labels[1:]

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
    
    def predict_probabilities_pixelwise(self, image):
        logger.debug( 'predicting with IIBoost' )
        assert len(image.shape) == 4, "IIBoost expects 3D data."

        # IIBoost requires both raw images and labels to be uint8
        raw = numpy.asarray(image, dtype=numpy.uint8)[...,0]
        raw = numpy.array( raw )

        # This is a debug class.  
        # As such, we recalculate the integral images every time...                
        image_channels = list( numpy.rollaxis(image, -1, 0) )
        integral_channels = map( self._model.computeIntegralImage, image_channels )
        
        prediction_img = self._model.predictWithChannels( raw, integral_channels )
        # Image from model prediction has no channels,
        #  but lazyflow expects classifiers to produce one channel for each 
        #  label class.  Here, we simply insert zero-channels for all but the last channel.
        prediction_img_reshaped = numpy.zeros( prediction_img.shape + (len(self._known_labels),), dtype=numpy.float32 )
        prediction_img_reshaped[...,-1] = prediction_img
        
        assert prediction_img_reshaped.shape == image.shape[:-1] + (len(self._known_labels),), \
            "Output image had wrong shape. Expected: {}, Got {}"\
            "".format( image.shape[:-1] + (len(self._known_labels),), prediction_img_reshaped.shape )
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
        model = IIBoost.Booster()
        model.deserialize(model_str)
                
        known_labels = list(h5py_group['known_labels'][:])
        feature_count = h5py_group['feature_count'][()]
        return IIBoostLazyflowClassifier(model, known_labels, feature_count)

# This assertion should pass if lazyflow is available.
from lazyflow.classifiers import LazyflowPixelwiseClassifierABC
assert issubclass( IIBoostLazyflowClassifier, LazyflowPixelwiseClassifierABC )
