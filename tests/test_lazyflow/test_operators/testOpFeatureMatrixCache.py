from builtins import object
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.opFeatureMatrixCache import OpFeatureMatrixCache
from lazyflow.operators.opBlockedArrayCache import OpBlockedArrayCache


class TestOpFeatureMatrixCache(object):
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
        # Use a cache for the labels so we can control the ideal_blockshape
        # This ensures that the blockwise behavior is tested, even though we're
        # testing with tiny data that would normally fall into a single block.
        opLabelCache = OpBlockedArrayCache(graph=graph)
        opLabelCache.BlockShape.setValue((10, 10, 1))
        opLabelCache.Input.setValue(labels)

        opFeatureMatrixCache = OpFeatureMatrixCache(graph=graph)
        opFeatureMatrixCache.LabelImage.connect(opLabelCache.Output)
        opFeatureMatrixCache.FeatureImage.setValue(features)

        labels_and_features = opFeatureMatrixCache.LabelAndFeatureMatrix.value
        assert labels_and_features.shape == (0, 3), "Empty feature matrix has wrong shape: {}".format(
            labels_and_features.shape
        )

        opFeatureMatrixCache.LabelImage.setDirty(numpy.s_[10:11, 10:12])
        opFeatureMatrixCache.LabelImage.setDirty(numpy.s_[20:21, 20:22])
        opFeatureMatrixCache.LabelImage.setDirty(numpy.s_[30:31, 30:32])

        labels_and_features = opFeatureMatrixCache.LabelAndFeatureMatrix.value
        assert labels_and_features.shape == (4, 3)
        assert (labels_and_features[:, 0] == 1).sum() == 2
        assert (labels_and_features[:, 0] == 2).sum() == 2

        # Can't check for equality because feature blocks can be in a random order.
        # Just check that all features are present, regardless of order.
        for feature_vec in [[10.5, 10.5], [10.5, 11.5], [20.5, 20.5], [20.5, 21.5]]:
            assert feature_vec in labels_and_features[:, 1:]


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
