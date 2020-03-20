from builtins import object
import numpy as np
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpRelabelConsecutive


class TestOpRelabelConsecutive(object):
    @classmethod
    def setup_class(cls):
        try:
            import pandas
        except ImportError:
            import nose

            raise nose.SkipTest

    def test_simple(self):
        op = OpRelabelConsecutive(graph=Graph())

        labels = 2 * np.arange(0, 100, dtype=np.uint8).reshape((10, 10))
        labels = vigra.taggedView(labels, "yx")
        op.Input.setValue(labels)
        relabeled = op.Output[:].wait()
        assert (relabeled == labels // 2).all()

    def test_startlabel(self):
        op = OpRelabelConsecutive(graph=Graph())
        op.StartLabel.setValue(10)

        labels = 2 * np.arange(0, 100, dtype=np.uint8).reshape((10, 10))
        labels = vigra.taggedView(labels, "yx")
        op.Input.setValue(labels)
        relabeled = op.Output[:].wait()
        assert (relabeled == 10 + labels // 2).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
