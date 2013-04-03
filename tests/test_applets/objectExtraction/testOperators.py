import unittest
import numpy as np
import vigra
from lazyflow.graph import Graph
from lazyflow.operators import OpLabelImage
from ilastik.applets.objectExtraction.opObjectExtraction import OpAdaptTimeListRoi, OpRegionFeatures

FEATURES = \
[
    [ 'Count',
      'RegionCenter',
      'Coord<ArgMaxWeight>',
      'Coord<Minimum>',
      'Coord<Maximum>' ],
    []
]

def binaryImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.float32)
    img[0,  0:10,  0:10,  0:10, 0] = 1
    img[0, 20:30, 20:30, 20:30, 0] = 1
    img[1, 20:30, 20:30, 20:30, 0] = 1
    img[1, 5:10, 5:10, 0, 0] = 1
    img = img.view( vigra.VigraArray )
    img.axistags = vigra.defaultAxistags('txyzc')

    return img

def rawImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.float32)
    img[0,  0:10,  0:10,  0:10, 0] = 200
    img[0, 20:30, 20:30, 20:30, 0] = 100
    img[1, 20:30, 20:30, 20:30, 0] = 50
    img[1, 5:10, 5:10, 0, 0] = 25
    img = img.view( vigra.VigraArray )
    img.axistags = vigra.defaultAxistags('txyzc')

    return img

class TestOpLabelImage(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpLabelImage(graph=g)
        self.img = binaryImage()
        self.op.Input.setValue(self.img)

    def test_segment(self):
        labelImg = self.op.Output.value
        labelImg = labelImg.astype(np.int)
        self.assertEquals(labelImg.shape, self.img.shape)
        vigraImage0 = vigra.analysis.labelVolumeWithBackground(self.img[0,...])
        vigraImage1 = vigra.analysis.labelVolumeWithBackground(self.img[1,...])
        
        assert np.all(np.asarray(vigraImage0)==labelImg[0,...])
        assert np.all(np.asarray(vigraImage1)==labelImg[1,...])


class TestOpRegionFeatures(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.labelop = OpLabelImage(graph=g)
        self.op = OpRegionFeatures(FEATURES, graph=g)
        self.op.LabelImage.connect(self.labelop.Output)
        self.op.RawImage.connect(self.labelop.Output) # Raw image is arbitrary for our purposes.  Just re-use the label image
        self.img = binaryImage()
        self.labelop.Input.setValue(self.img)



    def test_features(self):
        self.op.Output.fixed = False
        # FIXME: roi specification
        opAdapt = OpAdaptTimeListRoi( graph=self.op.graph )
        opAdapt.Input.connect( self.op.Output )
        
        feats = opAdapt.Output([0, 1]).wait()
        self.assertEquals(len(feats), self.img.shape[0])
        for t in feats:
            self.assertIsInstance(t, int)
            self.assertGreater(feats[t][0]['Count'].shape[0], 0)
            self.assertGreater(feats[t][0]['RegionCenter'].shape[0], 0)

        self.assertTrue(np.any(feats[0][0]['Count'] != feats[1][0]['Count']))
        self.assertTrue(np.any(feats[0][0]['RegionCenter'] != feats[1][0]['RegionCenter']))

class testOpRegionFeatures2(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.features = [["Count", "Mean"],[]]
        binimage = binaryImage()
        self.rawimage = rawImage()
        self.labelop = OpLabelImage(graph=g)
        self.op = OpRegionFeatures(self.features, graph=g)
        self.op.LabelImage.connect(self.labelop.Output)
        self.op.RawImage.setValue(self.rawimage)
        self.img = binaryImage()
        self.labelop.Input.setValue(binimage)
        
    def test(self):
        self.op.Output.fixed = False
        # FIXME: roi specification
        opAdapt = OpAdaptTimeListRoi( graph=self.op.graph )
        opAdapt.Input.connect( self.op.Output )
        
        feats = opAdapt.Output([0, 1]).wait()
        #print feats[0][0]
        self.assertEquals(len(feats), self.img.shape[0])
        for key in self.features[0]:
            #FIXME: why does it have to be [0][0]? What is the second list for?
            assert key in feats[0][0].keys()
        
        labelimage = self.labelop.Output[:].wait()
        nt = labelimage.shape[0]
        for t in range(nt):
            npcounts = np.bincount(labelimage[t,...].flat)
            counts = feats[t][0]["Count"].astype(np.uint32)
            means = feats[t][0]["Mean"]
            nobj = npcounts.shape[0]
            for iobj in range(1, nobj):
                assert npcounts[iobj]==counts[iobj]
                objmask = labelimage[t,...]==iobj
                npmean = np.mean(self.rawimage[t,...][objmask])
                assert npmean== means[iobj]
                
            


if __name__ == '__main__':
    unittest.main()
