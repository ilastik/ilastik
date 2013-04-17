from vigra_objfeats import VigraObjFeats
import unittest
import numpy as np

class VigraTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.myclass = VigraObjFeats()

    def _testFeatures(self, feats):
        self.assertTrue(len(feats) > 0)
        self.assertTrue(isinstance(feats, dict))
        for k, v in feats.iteritems():
            self.assertTrue(isinstance(k, str))
            self.assertTrue(isinstance(v, dict))
            for k2, v2 in v.iteritems():
                self.assertTrue(isinstance(k2, str))
                # TODO: check parameters

    def testAvailableFeatures2D(self):
        img = np.zeros((3, 3), dtype=np.float32)
        labels = np.zeros((3, 3), dtype=np.uint32)
        feats = self.myclass.availableFeatures(img, labels)
        self._testFeatures(feats)

    def testAvailableFeatures3D(self):
        img = np.zeros((3, 3, 3), dtype=np.float32)
        labels = np.zeros((3, 3, 3), dtype=np.uint32)
        feats = self.myclass.availableFeatures(img, labels)
        self._testFeatures(feats)


if __name__ == '__main__':
    unittest.main()