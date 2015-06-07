import cPickle as pickle
import numpy
from lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

import logging
logger = logging.getLogger(__name__)

class SklearnLazyflowClassifierFactory(LazyflowVectorwiseClassifierFactoryABC):
    """
    A factory for creating and training sklearn classifiers.
    """
    VERSION = 1 # This is used to determine compatibility of pickled classifier factories.
                # You must bump this if any instance members are added/removed/renamed.
    
    def __init__(self, classifier_type, *args, **kwargs):
        """
        classifier_type: The sklearn class to instantiate, e.g. sklearn.ensemble.RandomForestClassifier
        args, kwargs: Passed on to the classifier constructor.
        """
        self._args = args
        self._kwargs = kwargs
        self._classifier_type = classifier_type

    def create_and_train(self, X, y, feature_names=None):
        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)

        assert X.ndim == 2
        assert len(X) == len(y)
        sklearn_classifier = self._classifier_type(*self._args, **self._kwargs)
        logger.debug( 'Training new sklearn classifier: {}'.format( type(sklearn_classifier).__name__ ) )
        sklearn_classifier.fit(X, y)

        try:
            # Save for future reference
            known_classes = sklearn_classifier.classes_
        except AttributeError:
            # Some sklearn classifiers don't have a 'classes_' attribute.
            known_classes = numpy.unique(y)
        
        return SklearnLazyflowClassifier( sklearn_classifier, known_classes, X.shape[1], feature_names )

    @property
    def description(self):
        return self._classifier_type.__name__

    def __eq__(self, other):
        return (    isinstance(other, type(self))
                and self._classifier_type == other._classifier_type
                and self._args == other._args
                and self._kwargs == other._kwargs )
    def __ne__(self, other):
        return not self.__eq__(other)

assert issubclass( SklearnLazyflowClassifierFactory, LazyflowVectorwiseClassifierFactoryABC )

class SklearnLazyflowClassifier(LazyflowVectorwiseClassifierABC):

    VERSION = 2 # Used for pickling compatibility

    class VersionIncompatibilityError(Exception):
        pass

    def __init__(self, sklearn_classifier, known_classes, feature_count, feature_names):
        self._sklearn_classifier = sklearn_classifier
        self._known_classes = known_classes
        self._feature_count = feature_count
        self._feature_names = feature_names

        self.VERSION = SklearnLazyflowClassifier.VERSION
    
    def predict_probabilities(self, X):
        logger.debug( 'Predicting with sklearn classifier: {}'.format( type(self._sklearn_classifier).__name__ ) )
        return self._sklearn_classifier.predict_proba( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_classes

    @property
    def feature_count(self):
        return self._feature_count

    @property
    def feature_names(self):
        return self._feature_names

    def serialize_hdf5(self, h5py_group):
        h5py_group['pickled_classifier'] = pickle.dumps( self )

        # This is a required field for all classifiers
        h5py_group['pickled_type'] = pickle.dumps( type(self) )

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        pickled = h5py_group['pickled_classifier'][()]
        classifier = pickle.loads( pickled )
        if not hasattr(classifier, "VERSION") or classifier.VERSION != cls.VERSION:
            raise cls.VersionIncompatibilityError("Version mismatch. Deserialized classifier version does not match this code base.")
        return classifier

assert issubclass( SklearnLazyflowClassifier, LazyflowVectorwiseClassifierABC )
