import os
import tempfile
import cPickle as pickle

import numpy
import vigra
import h5py

from lazyflowClassifier import LazyflowPixelwiseClassifierABC, LazyflowPixelwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

class VigraRfPixelwiseClassifierFactory(LazyflowPixelwiseClassifierFactoryABC):
    """
    An implementation of LazyflowPixelwiseClassifierFactoryABC using a vigra RandomForest.
    This exists for testing purposes only. (it is normally better to use the vector-wise 
    classifier so lazyflow can cache the feature matrices).
    This implementation is simple and un-optimized.
    """
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
    
    def create_and_train_pixelwise(self, feature_images, label_images, axistags=None, feature_names=None):
        logger.debug( 'training pixel-wise vigra RF' )
        
        all_features = numpy.ndarray( shape=(0, feature_images[0].shape[-1]), dtype=numpy.float32 )
        all_labels = numpy.ndarray( shape=(0,1), dtype=numpy.uint32 )

        # Extract label points and corresponding feature vectors
        for feature_image, label_image in zip(feature_images, label_images):
            label_coords = numpy.nonzero(label_image)[:-1] # discard channel
            label_vector = label_image[label_coords]
            feature_matrix = feature_image[label_coords]
            all_features = numpy.concatenate((all_features, feature_matrix), axis=0)
            all_labels = numpy.concatenate((all_labels, label_vector), axis=0)
        
        # Save for future reference
        known_labels = numpy.unique(all_labels)

        assert len(all_features) == len(all_labels)
        classifier = vigra.learning.RandomForest(*self._args, **self._kwargs)
        classifier.learnRF(all_features, all_labels)

        return VigraRfPixelwiseClassifier( classifier, known_labels, feature_names )

    def get_halo_shape(self, data_axes):
        # No halo necessary, but since this classifier is for testing purposes, let's add one anyway.
        halo = tuple(range( len(data_axes)-1 ))
        return halo + (0,) # (no channel halo)

    def estimated_ram_usage_per_requested_predictionchannel(self):
        return 4

    @property
    def description(self):
        temp_rf = vigra.learning.RandomForest( *self._args, **self._kwargs )
        return "Vigra Random Forest ({} trees)".format( temp_rf.treeCount() )

    def __eq__(self, other):
        return (    isinstance(other, type(self))
                and self._args == other._args
                and self._kwargs == other._kwargs )
    def __ne__(self, other):
        return not self.__eq__(other)

assert issubclass( VigraRfPixelwiseClassifierFactory, LazyflowPixelwiseClassifierFactoryABC )

class VigraRfPixelwiseClassifier(LazyflowPixelwiseClassifierABC):
    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, vigra_rf, known_labels, feature_names):
        self._known_labels = known_labels
        self._vigra_rf = vigra_rf
        self._feature_names = feature_names
    
    def predict_probabilities_pixelwise(self, X, axistags=None):
        logger.debug( 'predicting PIXELWISE vigra RF' )
        
        # reshape the image into a 2D feature matrix
        matrix_shape = (numpy.prod(X.shape[:-1]), X.shape[-1])
        feature_matrix = numpy.reshape( X, matrix_shape )

        # Run classifier
        probabilities = self._vigra_rf.predictProbabilities( feature_matrix.view(numpy.ndarray) )
        
        # Reshape into an image.
        # Choose the prediction image shape carefully:
        #
        # Most classifiers omit a channel entirely if there are no labels given for a particular class,
        # So the number of prediction channels we got is the same as the number of known_classes
        # But if the classifier attempts to "help us out" by including channels for "missing" labels,
        #  then we want to just return the whole thing.
        num_probability_channels = max( len(self.known_classes), probabilities.shape[-1] )

        prediction_shape = X.shape[:-1] + (num_probability_channels,)
        return numpy.reshape(probabilities, prediction_shape)
    
    @property
    def known_classes(self):
        return self._known_labels

    @property
    def feature_count(self):
        return self._vigra_rf.featureCount()

    @property
    def feature_names(self):
        return self._feature_names
    
    def get_halo_shape(self, data_axes):
        # No halo necessary, but since this classifier is for testing purposes, let's add one anyway.
        halo = tuple(range( len(data_axes)-1 ))
        return halo + (0,) # (no channel halo)

    def serialize_hdf5(self, h5py_group):
        # Due to non-shared hdf5 dlls, vigra can't write directly to
        # our open hdf5 group. Instead, we'll use vigra to write the
        # classifier to a temporary file.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        self._vigra_rf.writeHDF5(cachePath, 'forest')

        # Open the temp file and copy to our project group
        with h5py.File(cachePath, 'r') as cacheFile:
            h5py_group.copy(cacheFile['forest'], 'forest')

        h5py_group['known_labels'] = self._known_labels
        h5py_group['feature_names'] = self._feature_names
        
        # This field is required for all classifiers
        h5py_group['pickled_type'] = pickle.dumps( type(self) )

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        # Due to non-shared hdf5 dlls, vigra can't read directly
        # from our open hdf5 group. Instead, we'll copy the
        # classfier data to a temporary file and give it to vigra.
        tmpDir = tempfile.mkdtemp()
        cachePath = os.path.join(tmpDir, 'tmp_classifier_cache.h5').replace('\\', '/')
        with h5py.File(cachePath, 'w') as cacheFile:
            cacheFile.copy(h5py_group['forest'], 'forest')

        forest = vigra.learning.RandomForest(cachePath, 'forest')
        known_labels = list(h5py_group['known_labels'][:])
        feature_names = list(h5py_group['feature_names'][:])

        os.remove(cachePath)
        os.rmdir(tmpDir)

        return VigraRfPixelwiseClassifier( forest, known_labels, feature_names )

assert issubclass( VigraRfPixelwiseClassifier, LazyflowPixelwiseClassifierABC )
