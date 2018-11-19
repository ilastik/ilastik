###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
#TODO: refactor
#TODO: test many more operators


import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

import unittest
import numpy as np
import vigra
from lazyflow.graph import Graph
from ilastik.applets.objectClassification.opObjectClassification import \
    OpRelabelSegmentation, OpObjectTrain, OpObjectPredict, OpObjectClassification, \
    OpBadObjectsToWarningMessage, OpMaxLabel
    
from ilastik.applets.counting.opCounting import \
    OpCounting, OpMean, OpVolumeOperator,OpLabelPipeline, \
    OpPredictionPipelineNoCache,OpPredictionPipeline

from ilastik.applets.counting.countingOperators import OpTrainCounter, OpPredictCounter, OpLabelPreviewer

 
# def segImage():
#     '''
#     #a 50x50x50 cube over 2 time points
#     #  * t=0: 1 object 5x5x5, 1 object 10x10x10
#     #  * t=1: 1 object 5x5x5, 2 objects 10x10x10
#     '''
#     
#     img = np.zeros((2, 50, 50, 50, 1), dtype=np.int)
#     img[0,  0:10,  0:10,  0:10, 0] = 1
#     img[0, 20:25, 20:25, 20:25, 0] = 2
#     img[1,  0:10,  0:10,  0:10, 0] = 1
#     img[1, 10:20, 10:20, 10:20, 0] = 2
#     img[1, 20:25, 20:25, 20:25, 0] = 3
#     
#     img = img.view(vigra.VigraArray)
#     img.axistags = vigra.defaultAxistags('txyzc')    
#     return img
# 
def emptyImage():
    '''
    an empty 5D image 
    '''
    img = np.zeros((2, 50, 50, 50, 0), dtype=np.int)
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')    
    return img

def imageWithRandomNoise():
    '''
    an empty 5D image 
    '''
    img = np.random.rand(2*50*50*50).reshape(2, 50, 50, 50, 1)
    
    img = img.view(vigra.VigraArray)
    img.axistags = vigra.defaultAxistags('txyzc')    
    return img
 
class TestOpMean(unittest.TestCase):
    def setUp(self):
        g = Graph()
        self.op = OpMean(graph=g)
 
    def test(self):
        rimg = imageWithRandomNoise()
        self.op.Input.setValue(rimg)
        mean = self.op.Output.value
        #FIXME: why is it this the region ?
        np.testing.assert_allclose(np.mean(rimg.view(np.ndarray),axis=2),mean.view(np.ndarray)[...,0:1,0])

        
# class TestOpObjectTrain(unittest.TestCase):
#     
#     nRandomForests = 1
#     def setUp(self):
#         segimg = segImage()
#  
#         rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
#         rawimg = rawimg.view(vigra.VigraArray)
#         rawimg.axistags = vigra.defaultAxistags('txyzc')
#  
#         feats = {"Standard Object Features": 
#                     {"Count":{}, "RegionCenter":{}, "Coord<Principal<Kurtosis>>":{}, "Coord<Minimum>":{}, "Coord<Maximum>":{}} 
#                 }
#  
#         g = Graph()
#         self.featsop = OpRegionFeatures(graph=g)
#         self.featsop.LabelImage.setValue(segimg)
#         self.featsop.RawImage.setValue( rawimg )
#         self.featsop.Features.setValue(feats)
#         self.assertTrue(self.featsop.Output.ready(), "The output of operator {} was not ready after connections took place.".format(self.featsop))
#  
#         self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(graph=g)
#         self._opRegFeatsAdaptOutput.Input.connect(self.featsop.Output)
#         self.assertTrue(self._opRegFeatsAdaptOutput.Output.ready(), "The output of operator {} was not ready after connections took place.".format(self._opRegFeatsAdaptOutput))
#  
#         self.op = OpObjectTrain(graph=g)
#         self.op.Features.resize(1)
#         self.op.Features[0].connect(self._opRegFeatsAdaptOutput.Output)
#         self.op.SelectedFeatures.setValue(feats)
#         self.op.FixClassifier.setValue(False)
#         self.op.ForestCount.setValue(self.nRandomForests)
#  
#     def test_train(self):
#         ##
#         # Test OpObjectTrain
#         ##
#          
#         labels = {0 : np.array([0, 1, 2]),
#                   1 : np.array([0, 1, 1, 2])}
#         self.op.Labels.resize(1)
#         self.op.Labels.setValue(labels)
#         
#         self.assertTrue(self.op.Classifier.ready(), "The output of operator {} was not ready after connections took place.".format(self.op))
#          
#         results = self.op.Classifier[:].wait()
#         self.assertEquals(len(results), self.nRandomForests)
#          
#         for randomForest in results:
#             self.assertIsInstance(randomForest, vigra.learning.RandomForest)

# 
# 
# class TestOpObjectPredict(unittest.TestCase):
#     def setUp(self):
#         segimg = segImage()
#         labels = {0 : np.array([0, 1, 2]),
#                   1 : np.array([0, 0, 0, 0,])}
# 
#         rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
#         rawimg = rawimg.view(vigra.VigraArray)
#         rawimg.axistags = vigra.defaultAxistags('txyzc')
#         
#         g = Graph()
#         
#         features = {"Standard Object Features": {"Count":{}}}
#         
#         self.featsop = OpRegionFeatures(graph=g)
#         self.featsop.LabelImage.setValue(segimg)
#         self.featsop.RawImage.setValue( rawimg )
#         self.featsop.Features.setValue(features)
#         self.assertTrue(self.featsop.Output.ready(), "The output of operator {} was not ready after connections took place.".format(self.featsop))
# 
#         self._opRegFeatsAdaptOutput = OpAdaptTimeListRoi(graph=g)
#         self._opRegFeatsAdaptOutput.Input.connect(self.featsop.Output)
#         self.assertTrue(self._opRegFeatsAdaptOutput.Output.ready(), "The output of operator {} was not ready after connections took place.".format(self._opRegFeatsAdaptOutput))
# 
#         self.trainop = OpObjectTrain(graph=g)
#         self.trainop.Features.resize(1)
#         self.trainop.Features[0].connect(self._opRegFeatsAdaptOutput.Output)
#         self.trainop.SelectedFeatures.setValue(features)
#         self.trainop.Labels.resize(1)
#         self.trainop.Labels.setValues([labels])
#         self.trainop.FixClassifier.setValue(False)
#         self.trainop.ForestCount.setValue(1)
#         self.assertTrue(self.trainop.Classifier.ready(), "The output of operator {} was not ready after connections took place.".format(self.trainop))
# 
#         self.op = OpObjectPredict(graph=g)
#         self.op.Classifier.connect(self.trainop.Classifier)
#         self.op.Features.connect(self._opRegFeatsAdaptOutput.Output)
#         self.op.SelectedFeatures.setValue(features)
#         self.op.LabelsCount.setValue(2)
#         self.assertTrue(self.op.Predictions.ready(), "The output of operator {} was not ready after connections took place.".format(self.op))
# 
#     def test_predict(self):
#         ###
#         # test whether prediction works correctly
#         
#         # label 1 is 'big object', label 2 is 'small object'
#         ###
#         preds = self.op.Predictions([0, 1]).wait()
#         self.assertTrue(np.all(preds[0] == np.array([0, 1, 2])))
#         self.assertTrue(np.all(preds[1] == np.array([0, 1, 1, 2])))
#         
#     def test_probabilities(self):
#         ###
#         # test whether the probability channel slots and the total probability slot return the same values
#         ###
#         probs = self.op.Probabilities([0, 1]).wait()
#         probChannel0Time0 = self.op.ProbabilityChannels[0][0].wait()
#         probChannel1Time0 = self.op.ProbabilityChannels[1][0].wait()
#         probChannel0Time1 = self.op.ProbabilityChannels[0][1].wait()
#         probChannel1Time1 = self.op.ProbabilityChannels[1][1].wait()
#         probChannel0Time01 = self.op.ProbabilityChannels[0]([0, 1]).wait()
#         
#         self.assertTrue( np.all(probChannel0Time0[0]==probs[0][:, 0]) )
#         self.assertTrue( np.all(probChannel1Time0[0]==probs[0][:, 1]) )
#         
#         self.assertTrue( np.all(probChannel0Time1[1]==probs[1][:, 0]) )
#         self.assertTrue( np.all(probChannel1Time1[1]==probs[1][:, 1]) )
#         
#         self.assertTrue( np.all(probChannel0Time01[0]==probs[0][:, 0]) )
#         self.assertTrue( np.all(probChannel0Time01[1]==probs[1][:, 0]) )
#         
# 
#  
# class TestFeatureSelection(unittest.TestCase):
#     def setUp(self):
#         segimg = segImage()
#         binimg = (segimg>0).astype(np.uint8)
#         labels = {0 : np.array([0, 1, 2]),
#                   1 : np.array([0, 1, 1, 2])}
# 
#         rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
#         rawimg = rawimg.view(vigra.VigraArray)
#         rawimg.axistags = vigra.defaultAxistags('txyzc')
# 
#         g = Graph()
# 
#         features = {"Standard Object Features": {"Count":{}, "RegionCenter":{}, "Coord<Principal<Kurtosis>>":{}, \
#                                       "Coord<Minimum>":{}, "Coord<Maximum>":{}, "Mean":{}, \
#                                       "Mean in neighborhood":{"margin":(30, 30, 1)}}}
#         
#         sel_features = {"Standard Object Features": {"Count":{}, "Mean":{}, "Mean in neighborhood":{"margin":(30, 30, 1)}, "Variance":{}}}
#         
#         self.extrOp = OpObjectExtraction(graph=g)
#         self.extrOp.BinaryImage.setValue(binimg)
#         self.extrOp.RawImage.setValue(rawimg)
#         self.extrOp.Features.setValue(features)
#     
#         assert self.extrOp.RegionFeatures.ready()
# 
#         self.trainop = OpObjectTrain(graph=g)
#         self.trainop.Features.resize(1)
#         self.trainop.Features.connect(self.extrOp.RegionFeatures)
#         self.trainop.SelectedFeatures.setValue(sel_features)
#         self.trainop.Labels.resize(1)
#         self.trainop.Labels.setValues([labels])
#         self.trainop.FixClassifier.setValue(False)
#         self.trainop.ForestCount.setValue(1)
#         
#         assert self.trainop.Classifier.ready()
# 
#         
#     def test_predict(self):
#         rf = self.trainop.Classifier[0].wait()
#         
#         #pass a vector of 4 random features. vigra shouldn't complain
#         #even though we computed more than 4
#         dummy_feats = np.zeros((1,4), dtype=np.float32)
#         dummy_feats[:] = 42
#         pred = rf[0].predictProbabilities(dummy_feats)
#         
# 
# class TestOpBadObjectsToWarningMessage(unittest.TestCase):
#     def setUp(self):
#         g = Graph()
#         
#         self.op = OpBadObjectsToWarningMessage(graph=g)
#         
#     def test_false_input_format(self):
#         ###
#         # test whether wrong formats are rejected
#         ###
#     
#         with self.assertRaises(TypeError):
#             self.op.BadObjects.setValue([])
#         with self.assertRaises(TypeError):
#             self.op.BadObjects.setValue({'objects':{}, 'feats': None})
#         
#     def test_true_input_format(self):
#         ###
#         # test whether right formats are accepted and correctly processed
#         ###
#         
#         # valid format, bad features existent
#         self.op.BadObjects.setValue({'objects':{1: {0: [1,2]}}, 'feats': set()})
#         self.assertNotEquals(self.op.WarningMessage.value, {})
#         notimemsg=self.op.WarningMessage.value
#         
#         # valid format, bad features existent
#         self.op.BadObjects.setValue({'objects':{1: {0: [1,2], 1:[]}}, 'feats': set()})
#         self.assertIsNotNone(self.op.WarningMessage.value)
#         timemsg=self.op.WarningMessage.value
#         
#         # if time slices are present, the output should indicate them (i.e., be larger)
#         self.assertNotEqual(notimemsg['details'], timemsg['details'])
#         
#         # set back to None, should be caught
#         self.op.BadObjects.setValue(None)
#         
#     def test_output_format(self):
#         self.op.BadObjects.setValue({'objects':{1: {0: [1,2]}}, 'feats': set()})
#         messagedict = self.op.WarningMessage.value
#         print(messagedict)
#         self.assertTrue('title' in messagedict.keys())
#         self.assertTrue('text' in messagedict.keys())
# 
# 
# class TestMaxLabel(object):
#     def setUp(self):
#         g = Graph()
#         rawimg = np.random.randint(0, 255, (2, 10, 10, 10, 1))
#         binimg = rawimg>100
#         cc0 = vigra.analysis.labelVolumeWithBackground(binimg[0,:, :, :, 0].astype(np.uint8))
#         cc1 = vigra.analysis.labelVolumeWithBackground(binimg[1,:, :, :, 0].astype(np.uint8))
#         nobj = np.max(cc0)+1+np.max(cc1)+1
#         segmimg = np.zeros(rawimg.shape)
#         segmimg[0,:, : , :, 0] = cc0[:]
#         segmimg[1,:, :, :,0] = cc1[:]
#         rawimg = vigra.taggedView(rawimg, 'txyzc')
#         binimg = vigra.taggedView(rawimg, 'txyzc')
#         segmimg = vigra.taggedView(segmimg, 'txyzc')
#         
#         self.features = {"Bad Plugin": {"bad_feature_1": {}, "bad_feature_2":{}}}
#         self.featureArrays = {0: {"Bad Plugin":{"bad_feature_1": np.array(range(nobj)), \
#                                                "bad_feature_2": np.array(range(nobj))}},
#                               1: {"Bad Plugin":{"bad_feature_1": np.array(range(nobj)), \
#                                                "bad_feature_2": np.array(range(nobj))}}}
#         
#         self.op = OpObjectClassification(graph = g)
#         self.op.RawImages.setValues([rawimg])
#         self.op.BinaryImages.setValues([binimg])
#         self.op.SegmentationImages.setValues([segmimg])
#         self.op.ObjectFeatures.setValues([self.featureArrays])
#         self.op.ComputedFeatureNames.setValue(self.features)
#         self.op.SelectedFeatures.setValue(self.features)
#         
#     def testNumLabels(self):
#         labelArray1 =  np.zeros((7,))
#         labelArray1[1] = 1
#         labelArray1[3] = 2
#         labelArray2 = np.zeros((5,))
#         labelArray2[1] = 1
#         labelArray2[2] = 2
#         labelArray2[3] = 3
#         labelArray2[4] = 4
#         self.op.LabelInputs.setValues([{0: labelArray1, 1: labelArray2}])
#         
#         nl = self.op.NumLabels[:].wait()
#         assert nl[0]==4
#    
# 
# class TestFullOperator(unittest.TestCase):
#     def setUp(self):
#         segimg = segImage()
#         binimg = (segimg>0).astype(np.uint8)
#         labels = {0 : np.array([0, 1, 2]),
#                   1 : np.array([0, 1, 1, 2])}
# 
#         rawimg = np.indices(segimg.shape).sum(0).astype(np.float32)
#         rawimg = rawimg.view(vigra.VigraArray)
#         rawimg.axistags = vigra.defaultAxistags('txyzc')
# 
#         g = Graph()
# 
#         features = {"Standard Object Features": {"Count":{}, "RegionCenter":{}, "Coord<Principal<Kurtosis>>":{}, \
#                                       "Coord<Minimum>":{}, "Coord<Maximum>":{}, "Mean":{}, \
#                                       "Mean in neighborhood":{"margin":(30, 30, 1)}}}
#         
#         sel_features = {"Standard Object Features": {"Count":{}, "Mean":{}, "Mean in neighborhood":{"margin":(30, 30, 1)}, "Variance":{}}}
#         
#         self.extrOp = OpObjectExtraction(graph=g)
#         self.extrOp.BinaryImage.setValue(binimg)
#         self.extrOp.RawImage.setValue(rawimg)
#         self.extrOp.Features.setValue(features)
#         assert self.extrOp.RegionFeatures.ready()
#         
#         self.classOp = OpObjectClassification(graph=g)
#         self.classOp.BinaryImages.setValues([binimg])
#         self.classOp.SegmentationImages.setValues([segimg])
#         self.classOp.RawImages.setValues([rawimg])
#         self.classOp.LabelInputs.setValues([labels])
#         self.classOp.ObjectFeatures.connect(self.extrOp.RegionFeatures)
#         self.classOp.ComputedFeatureNames.connect(self.extrOp.ComputedFeatureNames)
#         self.classOp.SelectedFeatures.setValue(sel_features)
#         
#         
#     def test(self):
#         self.assertTrue(self.classOp.Predictions.ready(), "Prediction slot of OpObjectClassification wasn't ready.")
#         probs = self.classOp.PredictionImages[0][:].wait()
#         
#     def test_unfavorable_conditions(self):
#         #TODO write test with not so nice input
#         pass
