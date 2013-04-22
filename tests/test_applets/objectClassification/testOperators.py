import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

import unittest
import numpy as np
import vigra
from lazyflow.graph import Graph
from ilastik.applets.objectClassification.opObjectClassification import \
    OpRelabelSegmentation, OpObjectTrain, OpObjectPredict, OpObjectClassification
    
from ilastik.applets import objectExtraction
from ilastik.applets.objectExtraction.opObjectExtraction import \
    OpRegionFeatures, OpAdaptTimeListRoi, OpObjectExtraction

FEATURES = \
[
    [ 'Count',
      'RegionCenter',
      'Coord<ArgMaxWeight >',
      'Coord<Minimum>',
      'Coord<Maximum>' ],
    []
]


def segImage():
    img = np.zeros((2, 50, 50, 50, 1), dtype=np.int)
    img[0,  0:10,  0:10,  0:10, 0] = 1
    img[0, 20:25, 20:25, 20:25, 0] = 2
    img[1,  0:10,  0:10,  0:10, 0] = 1
    img[1, 10:20, 10:20, 10:20, 0] = 2
    img[1, 20:25, 20:25, 20:25, 0] = 3
    
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')    
    return img


class TestOpRelabelSegmentation(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpRelabelSegmentation(graph=g)

    def test(self):
        segimg = segImage()
        map_ = {0 : np.array([10, 20, 30]),
                1 : np.array([40, 50, 60, 70])}
        self.op.Image.setValue(segimg)
        self.op.ObjectMap.setValue(map_)
        self.op.Features._setReady() # hack because we do not use features
        img = self.op.Output.value

        self.assertEquals(img[0, 49, 49, 49, 0], 10)
        self.assertEquals(img[1, 49, 49, 49, 0], 40)
        self.assertTrue(np.all(img[0,  0:10,  0:10,  0:10, 0] == 20))
        self.assertTrue(np.all(img[0, 20:25, 20:25, 20:25, 0] == 30))
        self.assertTrue(np.all(img[1,  0:10,  0:10,  0:10, 0] == 50))
        self.assertTrue(np.all(img[1, 10:20, 10:20, 10:20, 0] == 60))
        self.assertTrue(np.all(img[1, 20:25, 20:25, 20:25, 0] == 70))


class TestOpObjectTrain(unittest.TestCase):
    def setUp(self):
        segimg = segImage()

        rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
        rawimg = rawimg.view(vigra.VigraArray)
        rawimg.axistags = vigra.defaultAxistags('txyzc')

        g = Graph()
        self.featsop = OpRegionFeatures(FEATURES, graph=g)
        self.featsop.LabelImage.setValue(segimg)
        self.featsop.RawImage.setValue( rawimg )

        self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(graph=g)
        self._opRegFeatsAdaptOutput.Input.connect(self.featsop.Output)

        self.op = OpObjectTrain(graph=g)
        self.op.Features.resize(1)
        self.op.Features[0].connect(self._opRegFeatsAdaptOutput.Output)
        self.op.FixClassifier.setValue(False)
        self.op.ForestCount.setValue(1)

    def test_train(self):
        labels = {0 : np.array([0, 1, 2]),
                  1 : np.array([0, 1, 1, 2])}
        self.op.Labels.resize(1)
        self.op.Labels.setValue(labels)
       
        assert self.op.Classifier.ready()


class TestOpObjectPredict(unittest.TestCase):
    def setUp(self):
        segimg = segImage()
        labels = {0 : np.array([0, 1, 2]),
                  1 : np.array([0, 0, 0, 0,])}

        rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
        rawimg = rawimg.view(vigra.VigraArray)
        rawimg.axistags = vigra.defaultAxistags('txyzc')
        
        g = Graph()
        
        objectExtraction.config.selected_features = ["Count"]
        
        self.featsop = OpRegionFeatures(FEATURES, graph=g)
        self.featsop.LabelImage.setValue(segimg)
        self.featsop.RawImage.setValue( rawimg )
        assert self.featsop.Output.ready()

        self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(graph=g)
        self._opRegFeatsAdaptOutput.Input.connect(self.featsop.Output)
        assert self._opRegFeatsAdaptOutput.Output.ready()

        self.trainop = OpObjectTrain(graph=g)
        self.trainop.Features.resize(1)
        self.trainop.Features[0].connect(self._opRegFeatsAdaptOutput.Output)
        self.trainop.Labels.resize(1)
        self.trainop.Labels.setValues([labels])
        self.trainop.FixClassifier.setValue(False)
        self.trainop.ForestCount.setValue(1)
        assert self.trainop.Classifier.ready()

        self.op = OpObjectPredict(graph=g)
        self.op.Classifier.connect(self.trainop.Classifier)
        self.op.Features.connect(self._opRegFeatsAdaptOutput.Output)
        self.op.LabelsCount.setValue(2)
        assert self.op.Predictions.ready()

    def test_predict(self):
        preds = self.op.Predictions([0, 1]).wait()
        self.assertTrue(np.all(preds[0] == np.array([0, 1, 2])))
        self.assertTrue(np.all(preds[1] == np.array([0, 1, 1, 2])))
        probs = self.op.Probabilities([0, 1]).wait()
        probChannel0Time0 = self.op.ProbabilityChannels[0][0].wait()
        probChannel1Time0 = self.op.ProbabilityChannels[1][0].wait()
        probChannel0Time1 = self.op.ProbabilityChannels[0][1].wait()
        probChannel1Time1 = self.op.ProbabilityChannels[1][1].wait()
        probChannel0Time01 = self.op.ProbabilityChannels[0]([0, 1]).wait()
        assert np.all(probChannel0Time0[0]==probs[0][:, 0])
        assert np.all(probChannel1Time0[0]==probs[0][:, 1])
        assert np.all(probChannel0Time1[1]==probs[1][:, 0])
        assert np.all(probChannel1Time1[1]==probs[1][:, 1])
        assert np.all(probChannel0Time01[0]==probs[0][:, 0])
        assert np.all(probChannel0Time01[1]==probs[1][:, 0])
        
    
   
class TestFeatureSelection(unittest.TestCase):
    def setUp(self):
        segimg = segImage()
        binimg = (segimg>0).astype(np.uint8)
        labels = {0 : np.array([0, 1, 2]),
                  1 : np.array([0, 1, 1, 2])}

        rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
        rawimg = rawimg.view(vigra.VigraArray)
        rawimg.axistags = vigra.defaultAxistags('txyzc')

        g = Graph()

        objectExtraction.config.vigra_features = ["Count", "Mean", "Variance", "Skewness"]
        objectExtraction.config.other_features = []
        objectExtraction.config.selected_features = ["Count", "Mean", "Mean_excl", "Variance"]
        
        self.extrOp = OpObjectExtraction(graph=g)
        self.extrOp.BinaryImage.setValue(binimg)
        self.extrOp.RawImage.setValue(rawimg)
        assert self.extrOp.RegionFeatures.ready()

        self.trainop = OpObjectTrain(graph=g)
        self.trainop.Features.resize(1)
        self.trainop.Features.connect(self.extrOp.RegionFeatures)
        self.trainop.Labels.resize(1)
        self.trainop.Labels.setValues([labels])
        self.trainop.FixClassifier.setValue(False)
        self.trainop.ForestCount.setValue(1)
        assert self.trainop.Classifier.ready()

        
    def test_predict(self):
        rf = self.trainop.Classifier[0].wait()
        
        #pass a vector of 4 random features. vigra shouldn't complain
        #even though we computed more than 4
        dummy_feats = np.zeros((1,4), dtype=np.float32)
        dummy_feats[:] = 42
        pred = rf[0].predictProbabilities(dummy_feats)


class TestFullOperator(unittest.TestCase):
    def setUp(self):
        segimg = segImage()
        binimg = (segimg>0).astype(np.uint8)
        labels = {0 : np.array([0, 1, 2]),
                  1 : np.array([0, 1, 1, 2])}

        rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
        rawimg = rawimg.view(vigra.VigraArray)
        rawimg.axistags = vigra.defaultAxistags('txyzc')

        g = Graph()

        objectExtraction.config.vigra_features = ["Count", "Mean", "Variance", "Skewness"]
        objectExtraction.config.selected_features = ["Count", "Mean", "Mean_excl", "Variance"]
        
        self.extrOp = OpObjectExtraction(graph=g)
        self.extrOp.BinaryImage.setValue(binimg)
        self.extrOp.RawImage.setValue(rawimg)
        assert self.extrOp.RegionFeatures.ready()
        
        self.classOp = OpObjectClassification(graph=g)
        self.classOp.BinaryImages.resize(1)
        self.classOp.BinaryImages.setValues([binimg])
        self.classOp.SegmentationImages.resize(1)
        self.classOp.SegmentationImages.setValues([segimg])
        self.classOp.RawImages.resize(1)
        self.classOp.RawImages.setValues([rawimg])
        self.classOp.LabelInputs.resize(1)
        self.classOp.LabelInputs.setValues([labels])
        self.classOp.LabelsAllowedFlags.resize(1)
        self.classOp.LabelsAllowedFlags.setValues([True])
        self.classOp.ObjectFeatures.connect(self.extrOp.RegionFeatures)
        
        
    def test(self):
        assert self.classOp.Predictions.ready()
        probs = self.classOp.PredictionImages[0][:].wait()
        

if __name__ == '__main__':
    unittest.main()
