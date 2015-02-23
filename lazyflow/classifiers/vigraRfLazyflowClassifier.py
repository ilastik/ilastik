import os
import tempfile
import cPickle as pickle

import numpy
import vigra
import h5py

from lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

class VigraRfLazyflowClassifierFactory(LazyflowVectorwiseClassifierFactoryABC):
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
    
    def create_and_train(self, X, y):
        logger.debug( 'training single-threaded vigra RF' )

        # Save for future reference
        known_labels = numpy.unique(y)

        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)
        if y.ndim == 1:
            y = y[:, numpy.newaxis]

        assert X.ndim == 2
        assert len(X) == len(y)
        classifier = vigra.learning.RandomForest(*self._args, **self._kwargs)
        classifier.learnRF(X, y)

        return VigraRfLazyflowClassifier( classifier, known_labels )

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

assert issubclass( VigraRfLazyflowClassifierFactory, LazyflowVectorwiseClassifierFactoryABC )

class VigraRfLazyflowClassifier(LazyflowVectorwiseClassifierABC):
    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, vigra_rf, known_labels):
        self._known_labels = known_labels
        self._vigra_rf = vigra_rf
    
    def predict_probabilities(self, X):
        logger.debug( 'predicting single-threaded vigra RF' )
        return self._vigra_rf.predictProbabilities( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_labels

    @property
    def feature_count(self):
        return self._vigra_rf.featureCount()

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
            cacheFile.copy(h5py_group, 'forest')

        forest = vigra.learning.RandomForest(cachePath, 'forest')
        known_labels = list(h5py_group['known_labels'][:])

        os.remove(cachePath)
        os.rmdir(tmpDir)

        return VigraRfLazyflowClassifier( forest, known_labels )

assert issubclass( VigraRfLazyflowClassifier, LazyflowVectorwiseClassifierABC )
