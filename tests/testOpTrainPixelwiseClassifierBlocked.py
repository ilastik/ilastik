from builtins import object
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.classifierOperators import OpTrainPixelwiseClassifierBlocked, OpPixelwiseClassifierPredict
from lazyflow.classifiers import VigraRfPixelwiseClassifierFactory, VigraRfPixelwiseClassifier


class TestOpTrainPixelwiseClassifierBlocked(object):
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
        opTrain = OpTrainPixelwiseClassifierBlocked(graph=graph)
        opTrain.ClassifierFactory.setValue(VigraRfPixelwiseClassifierFactory(10))
        opTrain.Images.resize(1)
        opTrain.Labels.resize(1)
        opTrain.nonzeroLabelBlocks.resize(1)
        opTrain.Images[0].setValue(features)
        opTrain.Labels[0].setValue(labels)
        nonzero_slicings = [numpy.s_[10:20, 10:20, 0:1], numpy.s_[20:30, 20:30, 0:1]]
        opTrain.nonzeroLabelBlocks[0].setValue(nonzero_slicings)
        opTrain.MaxLabel.setValue(2)

        opTrain.Labels[0].setDirty(numpy.s_[10:11, 10:12])
        opTrain.Labels[0].setDirty(numpy.s_[20:21, 20:22])
        opTrain.Labels[0].setDirty(numpy.s_[30:31, 30:32])

        trained_classifier = opTrain.Classifier.value

        # This isn't much of a test at the moment...
        assert isinstance(trained_classifier, VigraRfPixelwiseClassifier)

        # Try predicting while we're at it...
        opPredict = OpPixelwiseClassifierPredict(graph=graph)
        opPredict.Image.connect(opTrain.Images[0])
        opPredict.LabelsCount.connect(opTrain.MaxLabel)
        opPredict.Classifier.connect(opTrain.Classifier)

        predictions = opPredict.PMaps[:].wait()
        assert predictions.shape == features.shape[:-1] + (2,)  # We used 2 input labels above.


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
