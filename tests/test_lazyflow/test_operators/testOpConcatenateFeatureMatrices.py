from builtins import object
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.opFeatureMatrixCache import OpFeatureMatrixCache
from lazyflow.operators.opConcatenateFeatureMatrices import OpConcatenateFeatureMatrices


class TestOpConcatenateFeatureMatrices(object):
    def testBasic(self):
        graph = Graph()
        op1 = self._getMatrixOp(graph)
        op2 = self._getMatrixOp(graph)

        opConcatenate = OpConcatenateFeatureMatrices(graph=graph)
        opConcatenate.FeatureMatrices.resize(2)
        opConcatenate.FeatureMatrices[0].connect(op1.LabelAndFeatureMatrix)
        opConcatenate.FeatureMatrices[1].connect(op2.LabelAndFeatureMatrix)
        opConcatenate.ProgressSignals.resize(2)
        opConcatenate.ProgressSignals[0].connect(op1.ProgressSignal)
        opConcatenate.ProgressSignals[1].connect(op2.ProgressSignal)

        result = opConcatenate.ConcatenatedOutput.value
        assert result.shape == (8, 3)
        assert (result[:, 0] == 1).sum() == 4
        assert (result[:, 0] == 2).sum() == 4

    def _getMatrixOp(self, graph):
        features = numpy.indices((100, 100)).astype(numpy.float32) + 0.5
        features = numpy.rollaxis(features, 0, 3)
        features = vigra.taggedView(features, "xyc")
        labels = numpy.zeros((100, 100, 1), dtype=numpy.uint8)
        labels = vigra.taggedView(labels, "xyc")

        labels[10, 10] = 1
        labels[10, 11] = 1
        labels[20, 20] = 2
        labels[20, 21] = 2

        opFeatureMatrixCache = OpFeatureMatrixCache(graph=graph)
        opFeatureMatrixCache.FeatureImage.setValue(features)
        opFeatureMatrixCache.LabelImage.setValue(labels)

        opFeatureMatrixCache.LabelImage.setDirty(numpy.s_[10:11, 10:12])
        opFeatureMatrixCache.LabelImage.setDirty(numpy.s_[20:21, 20:22])
        opFeatureMatrixCache.LabelImage.setDirty(numpy.s_[30:31, 30:32])

        return opFeatureMatrixCache


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
