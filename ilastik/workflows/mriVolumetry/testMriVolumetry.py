import unittest

from ilastik.workflows.mriVolumetry.opSmoothing import OpCostVolumeFilter
from ilastik.workflows.mriVolumetry.opMriVolFilter import OpFanOut
from ilastik.workflows.mriVolumetry.opMriVolFilter import OpMriBinarizeImage
from ilastik.workflows.mriVolumetry.opMriVolFilter import OpMriVolFilter
from ilastik.workflows.mriVolumetry.opImplementationChoice import OpImplementationChoice

from lazyflow.graph import Graph
from lazyflow.operator import Operator, InputSlot, OutputSlot
from lazyflow.operators import OpMaxChannelIndicatorOperator
from lazyflow.operators import OpArrayPiper
from lazyflow.operators import OpPixelOperator
from lazyflow.operators import OpSingleChannelSelector

import numpy as np

import vigra


class TestOpCostVolumeFilter(unittest.TestCase):
    def setUp(self):
        self.vol = np.random.rand(120, 130, 110)
        # necessary for meta information, convert to vigra array
        self.vol = vigra.taggedView(self.vol, axistags='xyz')
        self.vol = self.vol.withAxes(*'txyzc')
        self.sig = 1.2

    def testUsage(self):
        g = Graph()
        op = OpCostVolumeFilter(graph=g)
        op.Input.setValue(self.vol)
        op.Configuration.setValue({'sigma': self.sig})
        out = op.Output[0:1, ...].wait()
        assert out.shape == self.vol.shape, \
            'In and output data differs in shape'


class TestOpMriBinarizeImage(unittest.TestCase):
    def setUp(self):
        self.num_channels = 4
        self.vol = np.random.randint(1, self.num_channels, size=(120,130,110))
        # necessary for meta information, convert to vigra array 
        self.vol = vigra.taggedView(self.vol, axistags='xyz')
        self.BackgroundChannel = 2
        self.ActiveChannels = [2, 0, 0, 2]

    def testUsage(self):
        g = Graph()
        op = OpMriBinarizeImage(graph=g)
        op.Input.setValue(self.vol)
        op.ActiveChannels.setValue(self.ActiveChannels)

        out = op.Output[...].wait()
        assert out.shape == self.vol.shape, \
            'In and output data differs in shape'
        assert np.all(np.unique(out) == [0, 1]), \
            'Not a binary image (0,1)'

class TestOpFanOut(unittest.TestCase):
    def setUp(self):
        self.num_channels = 4
        self.vol = np.random.randint(1, self.num_channels, size=(120,130,110))
        # necessary for meta information, convert to vigra array 
        self.vol = vigra.taggedView(self.vol, axistags='xyz')

    def testUsage(self):
        g = Graph()
        op = OpFanOut(graph=g)
        op.Input.setValue(self.vol)
        op.NumChannels.setValue(self.num_channels)

        assert len(op.Output) == self.num_channels
        for c in range(self.num_channels):
            out = op.Output[c][...].wait()
            out = vigra.taggedView(out, axistags = op.Output[c].meta.axistags)
            assert np.all((self.vol==c) == out)


class TestOpImplementationChoice(unittest.TestCase):
    def setUp(self):
        pass

    def TestUsage(self):
        class ABC(Operator):
            Input = InputSlot()
            Output = OutputSlot()

        choices = {'pipe': OpArrayPiper,
                   'chan': OpMaxChannelIndicatorOperator}

        wrap = OpImplementationChoice(ABC, graph=Graph())
        wrap.implementations = choices
 
        wrap.Implementation.setValue('pipe')
        vol = np.zeros((2, 10, 15, 20, 3))
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)
        # check if connection is done properly
        assert vol.shape == wrap.Output.meta.shape, "inner op not connected"
        # check if piping works
        out = wrap.Output[...].wait()

        vol2 = np.zeros((5, 6, 7))
        vol2 = vigra.taggedView(vol2, axistags='xyz')
        wrap.Input.setValue(vol2)
        # check if setupOutputs still works
        assert vol2.shape == wrap.Output.meta.shape, "setupOutputs not called"

        wrap.Implementation.setValue('chan')
        vol = np.zeros((2, 10, 15, 20, 3))
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)
        # check if operator is switched
        assert wrap.Output.meta.dtype == np.uint8, "op not switched"

    def TestAdvancedUsage(self):
        class ABC(Operator):
            Input = InputSlot()
            Output = OutputSlot()
            # needed by OpPixelOperator
            Function = InputSlot(optional=True)
            # needed by OpSingleChannelSelector
            Index = InputSlot(optional=True)

        choices = {'pixop': OpPixelOperator,
                   'chan': OpSingleChannelSelector}

        wrap = OpImplementationChoice(ABC, graph=Graph())
        wrap.implementations = choices
 
        wrap.Implementation.setValue('pixop')
        vol = np.zeros((2, 10, 15, 20, 3), dtype=np.int)
        vol = vigra.taggedView(vol, axistags='txyzc')
        wrap.Input.setValue(vol)
        wrap.Function.setValue(lambda x: x+1)
        # check if connection is done properly
        assert vol.shape == wrap.Output.meta.shape, "inner op not connected"
        # check if piping works
        out = wrap.Output[...].wait()
        # check if correct operator in use
        assert np.all(out == 1)

        wrap.Implementation.setValue('chan')
        wrap.Index.setValue(0)
        # check if operator is switched
        out = wrap.Output[...].wait()
        ts = wrap.Output.meta.getTaggedShape()
        if 'c' in ts:
            assert ts['c'] == 1, "op not switched"


class TestOpMriVolFilter(unittest.TestCase):
    def setUp(self):
        shape = (4, 100, 150, 200)
        vol = np.random.randint(0, 255, size=shape)
        vol = vigra.taggedView(vol, axistags='txyz')
        self.vol = vol
        pred = np.zeros(shape + (2,))
        pred = vigra.taggedView(pred, axistags='txyzc')
        pred[..., 1] = vol/255.0
        pred[..., 0] = 1 - pred[..., 1]
        self.pred = pred

    def testGaussian(self):
        g = Graph()
        op = OpMriVolFilter(graph=g)
        op.Method.setValue('gaussian')
        op.RawInput.setValue(self.vol)
        op.Input.setValue(self.pred)
        op.Configuration.setValue({'sigma': 0.2})
        op.Threshold.setValue(0)
        
        op.ActiveChannels.setValue(np.ones((2,), dtype=np.int))
        op.LabelNames.setValue(np.asarray(["black", "white"]))

        out = op.ArgmaxOutput[...].wait()

    def testGuided(self):
        g = Graph()
        op = OpMriVolFilter(graph=g)
        op.Method.setValue('guided')
        op.RawInput.setValue(self.vol)
        op.Input.setValue(self.pred)
        d = {'sigma': 0.2, 'eps': 0.2, 'guided': False}
        op.Configuration.setValue(d)
        op.Threshold.setValue(0)
        
        op.ActiveChannels.setValue(np.ones((2,), dtype=np.int))
        op.LabelNames.setValue(np.asarray(["black", "white"]))

        out = op.ArgmaxOutput[...].wait()

if __name__ == "__main__": 
    unittest.main()


