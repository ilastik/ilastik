import pickle as pickle
import numpy
import catboost
import vigra
from .lazyflowClassifier import LazyflowVectorwiseClassifierABC, LazyflowVectorwiseClassifierFactoryABC

import logging

logger = logging.getLogger(__name__)


class CatBoostClassifierFactory(LazyflowVectorwiseClassifierFactoryABC):
    """
    A factory for creating and training catboost classifiers.
    """

    VERSION = 1  # This is used to determine compatibility of pickled classifier factories.
    # You must bump this if any instance members are added/removed/renamed.

    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def create_and_train(self, X, y, feature_names=None):
        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)

        assert X.ndim == 2
        assert len(X) == len(y)
        classifier = catboost.CatBoostClassifier(*self._args, **self._kwargs)
        logger.debug("Training new classifier: {}".format(type(classifier).__name__))
        classifier.fit(X, y)

        known_classes = numpy.sort(vigra.analysis.unique(y))

        return CatBoostLazyflowClassifier(classifier, known_classes, X.shape[1], feature_names)

    @property
    def description(self):
        return "CatBoost Classifier"

    def __eq__(self, other):
        return (
            isinstance(other, type(self))
            and self._args == other._args
            and self._kwargs == other._kwargs
        )

    def __ne__(self, other):
        return not self.__eq__(other)


assert issubclass(CatBoostClassifierFactory, LazyflowVectorwiseClassifierFactoryABC)


class CatBoostLazyflowClassifier(LazyflowVectorwiseClassifierABC):

    VERSION = 1  # Used for pickling compatibility

    class VersionIncompatibilityError(Exception):
        pass

    def __init__(self, classifier, known_classes, feature_count, feature_names):
        self._classifier = classifier
        self._known_classes = known_classes
        self._feature_count = feature_count
        self._feature_names = feature_names

        self.VERSION = CatBoostLazyflowClassifier.VERSION

    def predict_probabilities(self, X):
        logger.debug("Predicting with classifier: {}".format(type(self._classifier).__name__))
        return self._classifier.predict_proba(numpy.asarray(X, dtype=numpy.float32))

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
        h5py_group["pickled_classifier"] = numpy.void(pickle.dumps(self, 0))

        # This is a required field for all classifiers
        h5py_group["pickled_type"] = numpy.void(pickle.dumps(type(self), 0))

    @classmethod
    def deserialize_hdf5(cls, h5py_group):
        classifier = pickle.loads(h5py_group["pickled_classifier"][()].tostring())
        if not hasattr(classifier, "VERSION") or classifier.VERSION != cls.VERSION:
            raise cls.VersionIncompatibilityError(
                "Version mismatch. Deserialized classifier version does not match this code base."
            )
        return classifier


assert issubclass(CatBoostLazyflowClassifier, LazyflowVectorwiseClassifierABC)
