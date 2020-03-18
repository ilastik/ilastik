from builtins import object
import numpy
import vigra
from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot
from lazyflow.operators.operators import OpBlockedArrayCache


class OpOnes(Operator):
    Output = OutputSlot()

    def __init__(self, shape, dtype, *args, **kwargs):
        super(OpOnes, self).__init__(*args, **kwargs)
        self._shape = shape
        self._dtype = dtype

    def setupOutputs(self):
        self.Output.meta.shape = self._shape
        self.Output.meta.dtype = self._dtype
        self.Output.meta.axistags = vigra.defaultAxistags("tzyxc"[5 - len(self._shape) :])

    def execute(self, slot, subindex, roi, result):
        result[:] = 1
        return result

    def propagateDirty(self, slot, subindex, roi):
        pass


class TestOpBlockedArrayCache_BIG_INPUT(object):
    def test(self):
        graph = Graph()
        opOnes = OpOnes((4000, 30000, 30000, 4), numpy.uint8, graph=graph)

        opCache = OpBlockedArrayCache(graph=graph)

        with opCache.setup_ram_context:
            opCache.Input.connect(opOnes.Output)
            opCache.BlockShape.setValue((1, 256, 256, 999))
            opCache.fixAtCurrent.setValue(False)

        assert (
            opCache.setup_ram_context.ram_increase_mb < 10
        ), "Cache book-keeping members are consuming more RAM than expected."

        data = opCache.Output((1500, 10000, 20000, 3), (1510, 10050, 20200, 4)).wait()
        assert (data == 1).all()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
