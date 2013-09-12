import numpy as np
import vigra
import unittest

from lazyflow.operators.classifierOperators import OpPredictRandomForest, \
    OpTrainRandomForest
from lazyflow.graph import Graph


class TestOther(unittest.TestCase):

    def setUp(self):

        graph=Graph()

        volShape = (100, 100, 20, 1)
        labelsShape = volShape
        featsShape = volShape[:3] + (5,)

        img = np.random.randint(0, 256, size=volShape).astype(np.uint8)
        labels = np.random.randint(1, 3, size=labelsShape).astype(np.uint8)
        features = np.zeros(featsShape)
        for f in range(featsShape[3]):
            features[..., f] = labels.squeeze() * (f+1)/featsShape[3]

        opPredict = OpPredictRandomForest(graph=graph)
        opTrain = OpTrainRandomForest(graph=graph)
        opTrain.fixClassifier.setValue(False)

        opPredict.Classifier.connect(opTrain.Classifier)
        opPredict.LabelsCount.setValue(2)

        self.opPredict = opPredict
        self.opTrain = opTrain
        self.img = img
        self.labels = labels
        self.features = features

    def testRegular(self):
        opTrain = self.opTrain
        opPredict = self.opPredict

        opPredict.Image.setValue(self.features)

        opTrain.Images.resize(1)
        opTrain.Images[0].setValue(self.features)
        opTrain.Labels.resize(1)
        opTrain.Labels[0].setValue(self.labels)
        out = opPredict.PMaps[...].wait()
        preds = np.where(out[..., 0] > out[..., 1], 1, 2)

        np.testing.assert_array_equal(
            preds, self.labels.squeeze(),
            err_msg="Training data is not predicted correctly")

    def testNonContiguous(self):
        # make features non-contiguous
        opTrain = self.opTrain
        opPredict = self.opPredict
        features = self.features
        labels = self.labels
        newfeats = np.swapaxes(features, 0, 2)
        newlabels = np.swapaxes(labels, 0, 2)

        assert np.may_share_memory(newfeats, features)

        opTrain.Images.resize(1)
        opTrain.Images[0].setValue(newfeats)
        opPredict.Image.setValue(newfeats)
        opTrain.Labels.resize(1)
        opTrain.Labels[0].setValue(newlabels)
        out = opPredict.PMaps[...].wait()
