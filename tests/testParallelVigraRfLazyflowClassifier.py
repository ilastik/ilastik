import numpy
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory, ParallelVigraRfLazyflowClassifier

class TestParallelVigraRfLazyflowClassifier(object):
    
    def setUp(self):
        # Classic XOR problem:
        # 2 features:
        # - negative product ==> class 1
        # - non-negative product ==> class 2
        feature_grid = numpy.mgrid[-5:5,-5:5]
        feature_matrix = numpy.concatenate(feature_grid.transpose())
        
        labels = (feature_matrix.prod(axis=-1) >= 0).astype(numpy.uint32) + 1
        labels = labels.flat[:]

        unseen_data = [[ 1.5,  2.5],
                       [-1.5, -2.5],
                       [ 3.4, -4.0],
                       [-1.2,  2.0]]
        expected_classes = (numpy.prod(unseen_data, axis=-1) > 0).astype(numpy.uint32) + 1

        self.training_feature_matrix = feature_matrix
        self.training_labels = labels
        self.prediction_data = unseen_data
        self.expected_classes = expected_classes
        
    def test_basic(self):
        # Initialize factory
        factory = ParallelVigraRfLazyflowClassifierFactory(10)
        
        # Train
        classifier = factory.create_and_train(self.training_feature_matrix, self.training_labels)
        assert isinstance(classifier, ParallelVigraRfLazyflowClassifier)
        assert list(classifier.known_classes) == [1,2]

        # Predict        
        probabilities = classifier.predict_probabilities( self.prediction_data )
        assert probabilities.shape == (4,2)
        assert probabilities.dtype == numpy.float32
        assert (0 <= probabilities).all() and (probabilities <= 1.0).all()
        assert (numpy.argmax(probabilities, axis=-1)+1 == self.expected_classes).all()

    def test_with_feature_importance(self):
        # Initialize factory
        factory = ParallelVigraRfLazyflowClassifierFactory(10, variable_importance_enabled=True)
        
        # Train
        classifier = factory.create_and_train(self.training_feature_matrix, self.training_labels)
        assert isinstance(classifier, ParallelVigraRfLazyflowClassifier)
        assert list(classifier.known_classes) == [1,2]
        assert len(classifier.feature_names) == 2

        # Predict        
        probabilities = classifier.predict_probabilities( self.prediction_data )
        assert probabilities.shape == (4,2)
        assert probabilities.dtype == numpy.float32
        assert (0 <= probabilities).all() and (probabilities <= 1.0).all()
        assert (numpy.argmax(probabilities, axis=-1)+1 == self.expected_classes).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
