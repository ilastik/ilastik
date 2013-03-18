import unittest
import numpy as np
from lazyflow.graph import Graph
from ilastik.applets.objectExtraction.opObjectExtraction import OpLabelImage, OpRegionFeatures

FEATURES = [
    'Count',
    'RegionCenter',
    'Coord<ArgMaxWeight>',
    'Coord<Minimum>',
    'Coord<Maximum>',
]

def binaryImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.float32)
    img[0,  0:10,  0:10,  0:10, 0] = 1
    img[0, 20:30, 20:30, 20:30, 0] = 1
    img[1, 20:30, 20:30, 20:30, 0] = 1

    return img

class TestOpLabelImage(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpLabelImage(graph=g)
        self.img = binaryImage()
        self.op.BinaryImage.setValue(self.img)

    def test_segment(self):
        self.op.LabelImageComputation.value
        labelImg = self.op.LabelImage.value
        labelImg = labelImg.astype(np.int)
        self.assertEquals(labelImg.shape, self.img.shape)
        self.assertTrue(labelImg.min() == 0)
        self.assertTrue(labelImg.max() == 2)


class TestOpRegionFeatures(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.labelop = OpLabelImage(graph=g)
        self.op = OpRegionFeatures(features=FEATURES, graph=g)
        self.op.LabelImage.connect(self.labelop.LabelImage)
        self.img = binaryImage()
        self.labelop.BinaryImage.setValue(self.img)

    def test_features(self):
        self.op.Output.fixed = False
        # FIXME: roi specification
        self.labelop.LabelImageComputation.value
        feats = self.op.Output([0, 1]).wait()
        self.assertEquals(len(feats), self.img.shape[0])
        for t in feats:
            self.assertIsInstance(t, int)
            self.assertGreater(feats[t][0]['Count'].shape[0], 0)
            self.assertGreater(feats[t][0]['RegionCenter'].shape[0], 0)

        self.assertTrue(np.any(feats[0][0]['Count'] != feats[1][0]['Count']))
        self.assertTrue(np.any(feats[0][0]['RegionCenter'] != feats[1][0]['RegionCenter']))

if __name__ == '__main__':
    unittest.main()
