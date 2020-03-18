from builtins import object
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.classifierOperators import OpTrainClassifierBlocked
from lazyflow.classifiers import VigraRfLazyflowClassifierFactory, VigraRfLazyflowClassifier


class TestOpTrainRandomForestBlocked(object):
    def testBasic(self):
        features = numpy.indices((100, 100)).astype(numpy.float32) + 0.5
        features = numpy.rollaxis(features, 0, 3)
        features = vigra.taggedView(features, "xyc")
        labels = numpy.zeros((100, 100, 1), dtype=numpy.uint8)
        labels = vigra.taggedView(labels, "xyc")

        labels[10, 10] = 1
        labels[10, 11] = 1
        labels[20, 20] = 2
        labels[20, 21] = 2

        graph = Graph()
        opTrain = OpTrainClassifierBlocked(graph=graph)
        opTrain.ClassifierFactory.setValue(VigraRfLazyflowClassifierFactory(10))
        opTrain.Images.resize(1)
        opTrain.Labels.resize(1)
        opTrain.nonzeroLabelBlocks.resize(1)
        opTrain.Images[0].setValue(features)
        opTrain.Labels[0].setValue(labels)
        opTrain.nonzeroLabelBlocks[0].setValue(0)  # Dummy for now (not used by operator yet)
        opTrain.MaxLabel.setValue(2)

        opTrain.Labels[0].setDirty(numpy.s_[10:11, 10:12])
        opTrain.Labels[0].setDirty(numpy.s_[20:21, 20:22])
        opTrain.Labels[0].setDirty(numpy.s_[30:31, 30:32])

        trained_classifier = opTrain.Classifier.value

        # This isn't much of a test at the moment...
        assert isinstance(trained_classifier, VigraRfLazyflowClassifier)


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
