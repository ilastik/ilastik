import numpy

class SklearnLazyflowClassifier(object):
    """
    Adapt a scikit-learn classifier type to the interface lazyflow expects.
    """
    def __init__(self, classifier_type, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._classifier_type = classifier_type
        self._known_classes = []
    
    def train(self, X, y):
        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)

        assert X.ndim == 2
        assert len(X) == len(y)
        self._classifier = self._classifier_type(*self._args, **self._kwargs)
        self._classifier.fit(X, y)

        try:
            # Save for future reference
            self._known_classes = self.classifier.classes_
        except AttributeError:
            # Some sklearn classifiers don't have a 'classes_' attribute.
            self._known_classes = numpy.unique(y)
    
    def predict_probabilities(self, X):
        return self._classifier.predict_proba( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_classes
