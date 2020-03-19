from builtins import object
import numpy
from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory, ParallelVigraRfLazyflowClassifier


class TestParallelVigraRfLazyflowClassifier(object):
    def setup_method(self, method):
        # Classic XOR problem:
        # 2 features:
        # - negative product ==> class 1
        # - non-negative product ==> class 2
        feature_grid = numpy.mgrid[-5:5, -5:5]
        feature_matrix = numpy.concatenate(feature_grid.transpose())

        labels = (feature_matrix.prod(axis=-1) >= 0).astype(numpy.uint32) + 1
        labels = labels.flat[:]

        unseen_data = [[1.5, 2.5], [-1.5, -2.5], [3.4, -4.0], [-1.2, 2.0]]
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
        assert list(classifier.known_classes) == [1, 2]

        # Predict
        probabilities = classifier.predict_probabilities(self.prediction_data)
        assert probabilities.shape == (4, 2)
        assert probabilities.dtype == numpy.float32
        assert (0 <= probabilities).all() and (probabilities <= 1.0).all()
        assert (numpy.argmax(probabilities, axis=-1) + 1 == self.expected_classes).all()

    def test_with_feature_importance(self):
        # Initialize factory
        factory = ParallelVigraRfLazyflowClassifierFactory(10, variable_importance_enabled=True)

        # Train
        classifier = factory.create_and_train(self.training_feature_matrix, self.training_labels)
        assert isinstance(classifier, ParallelVigraRfLazyflowClassifier)
        assert list(classifier.known_classes) == [1, 2]
        assert len(classifier.feature_names) == 2

        # Predict
        probabilities = classifier.predict_probabilities(self.prediction_data)
        assert probabilities.shape == (4, 2)
        assert probabilities.dtype == numpy.float32
        assert (0 <= probabilities).all() and (probabilities <= 1.0).all()
        assert (numpy.argmax(probabilities, axis=-1) + 1 == self.expected_classes).all()

    def test_pickle_fields(self):
        """
        Classifier factories are meant to be pickled and restored, but that only
        works if the thing we're restoring has the EXACT SAME MEMBERS as the
        current version of the class.

        Any changes to the factory's member variables will change it's pickled representation.
        Therefore, we store a special member named VERSION as both a class member
        AND instance member (see LazyflowVectorwiseClassifierFactoryABC.__new__),
        so we can check for compatibility before attempting to unpickle a factory.

        In this test, we verify that the pickle interface hasn't changed.

        IF THIS TEST FAILS:
            - Think about whether that's what you intended (see below)
            - Update ParallelVigraRfLazyflowClassifierFactory.VERSION
            - and then change the version and members listed below.

        ... but think hard about whether or not the changes you made to
        ParallelVigraRfLazyflowClassifierFactory are important, because they will
        invalidate stored classifiers in existing ilastik project files.
        (The project file should still load, but a warning will be shown, explaining that
        the user will need to train a new classifer.)

        """
        factory = ParallelVigraRfLazyflowClassifierFactory(10, variable_importance_enabled=True)
        members = set(factory.__dict__.keys())

        # Quick way to get the updated set of members.
        # print members

        assert ParallelVigraRfLazyflowClassifierFactory.VERSION == 2
        assert members == set(
            [
                "VERSION",
                "_variable_importance_path",
                "_kwargs",
                "_variable_importance_enabled",
                "_num_trees",
                "_label_proportion",
                "_num_forests",
            ]
        )


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
