import numpy
from .lazyflowClassifier import LazyflowClassifierABC, LazyflowClassifierFactoryABC

class SklearnLazyflowClassifierFactory(LazyflowClassifierFactoryABC):
    """
    A factory for creating and training sklearn classifiers.
    """
    def __init__(self, classifier_type, *args, **kwargs):
        """
        classifier_type: The sklearn class to instantiate, e.g. sklearn.ensemble.RandomForestClassifier
        args, kwargs: Passed on to the classifier constructor.
        """
        self._args = args
        self._kwargs = kwargs
        self._classifier_type = classifier_type

    def create_and_train(self, X, y):
        X = numpy.asarray(X, numpy.float32)
        y = numpy.asarray(y, numpy.uint32)

        assert X.ndim == 2
        assert len(X) == len(y)
        sklearn_classifier = self._classifier_type(*self._args, **self._kwargs)
        sklearn_classifier.fit(X, y)

        try:
            # Save for future reference
            known_classes = sklearn_classifier.classes_
        except AttributeError:
            # Some sklearn classifiers don't have a 'classes_' attribute.
            known_classes = numpy.unique(y)
        
        return SklearnLazyflowClassifier( sklearn_classifier, known_classes )

    @property
    def description(self):
        return self._classifier_type.__class__.__name__
    
assert issubclass( SklearnLazyflowClassifierFactory, LazyflowClassifierFactoryABC )

class SklearnLazyflowClassifier(LazyflowClassifierABC):
    def __init__(self, sklearn_classifier, known_classes):
        self._sklearn_classifier = sklearn_classifier
        self._known_classes = known_classes
    
    def predict_probabilities(self, X):
        return self._sklearn_classifier.predict_proba( numpy.asarray(X, dtype=numpy.float32) )
    
    @property
    def known_classes(self):
        return self._known_classes

assert issubclass( SklearnLazyflowClassifier, LazyflowClassifierABC )
