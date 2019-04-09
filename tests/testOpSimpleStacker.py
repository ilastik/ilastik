from builtins import object
import numpy as np
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpSimpleStacker


class TestOpSimpleStacker(object):
    def testBasic(self):
        inputA = vigra.taggedView(1 * np.ones((100, 100, 5), dtype=np.uint32), "yxc")
        inputB = vigra.taggedView(2 * np.ones((100, 100, 10), dtype=np.uint32), "yxc")
        inputC = vigra.taggedView(3 * np.ones((100, 100, 20), dtype=np.uint32), "yxc")

        op = OpSimpleStacker(graph=Graph())
        op.Images.resize(3)
        op.Images[0].setValue(inputA)
        op.Images[1].setValue(inputB)
        op.Images[2].setValue(inputC)
        op.AxisFlag.setValue("c")

        assert op.Output.ready()
        assert op.Output.meta.shape == (100, 100, 35)
        assert op.Output.meta.dtype == np.uint32


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
