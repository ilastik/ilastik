import unittest

from ilastik.workflows.mriVolumetry.opCostVolumeFilter import OpCostVolumeFilter, OpFanOut
# from opCostVolumeFilter import OpCostVolumeFilter
from lazyflow.graph import Graph

import numpy as np

import vigra

class TestOpCostVolumeFilter(unittest.TestCase):
    def setUp(self):
        self.vol = np.random.rand(120,130,110)
        # necessary for meta information, convert to vigra array 
        self.vol = vigra.taggedView(self.vol, axistags='xyz')
        self.sig = 1.2

    def testUsage(self):
        g = Graph()
        op = OpCostVolumeFilter(graph=g)
        op.Input.setValue(self.vol)
        op.Sigma.setValue(self.sig)
        out = op.Output[...].wait()
        assert out.shape == self.vol.shape, \
            'In and output data differs in shape'  


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

if __name__ == "__main__": 
    unittest.main()


