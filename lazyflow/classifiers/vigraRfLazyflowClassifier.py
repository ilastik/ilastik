import numpy
import vigra

class VigraRfLazyflowClassifier(object):
    """
    Adapt the vigra RandomForest class to the interface lazyflow expects.
    """
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._known_labels = []
        self._classifier = None
    
    def train(self, X, y):
        # Save for future reference
        self._known_labels = numpy.unique(y)

        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)
        if y.ndim == 1:
            y = y[:, numpy.newaxis]

        assert X.ndim == 2
        assert len(X) == len(y)
        self._classifier = vigra.learning.RandomForest(*self._args, **self._kwargs)
        self._classifier.learnRF(X, y)
    
    def predict_probabilities(self, X):
        return self._classifier.predictProbabilities( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_labels
    
    @property
    def n_classes_(self):
        return len(self._known_labels)
    