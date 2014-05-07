import numpy
import vigra

from .lazyflowClassifier import LazyflowClassifierABC, LazyflowClassifierFactoryABC

class VigraRfLazyflowClassifierFactory(LazyflowClassifierFactoryABC):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
    
    def create_and_train(self, X, y):
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

assert issubclass( VigraRfLazyflowClassifierFactory, LazyflowClassifierFactoryABC )

class VigraRfLazyflowClassifier(LazyflowClassifierABC):
    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, vigra_rf, known_labels):
        self._known_labels = known_labels
        self._vigra_rf = vigra_rf
    
    def predict_probabilities(self, X):
        return self._vigra_rf.predictProbabilities( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_labels

assert issubclass( VigraRfLazyflowClassifier, LazyflowClassifierABC )
