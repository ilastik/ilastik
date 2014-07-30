import unittest

from opCostVolumeFilter import OpCostVolumeFilter
from lazyflow.graph import Graph

import numpy as np

import vigra

class TestOpCostVolumeFilter(unittest.TestCase):
    def setUp(self):
        self.vol = np.random.rand((120,130,110))
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







