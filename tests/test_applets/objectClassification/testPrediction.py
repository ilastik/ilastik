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
from builtins import range
import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

import unittest
import numpy
import vigra
from lazyflow.graph import Graph
from ilastik.applets.objectClassification.opObjectClassification import \
    OpRelabelSegmentation, OpObjectTrain, OpObjectPredict, OpObjectClassification
    
from ilastik.applets import objectExtraction
from ilastik.applets.objectExtraction.opObjectExtraction import \
    OpRegionFeatures, OpAdaptTimeListRoi, OpObjectExtraction

import h5py

class TestWithCube(unittest.TestCase):
    def setUp(self):
        
        self.features = {"Standard Object Features": {\
                                     "Count":{}, \
                                     "Mean":{}, \
                                     "Mean in neighborhood":{"margin":(5, 5, 2)}}}

        self.rawimg = numpy.zeros((200, 200, 20, 1), dtype=numpy.uint8)
        self.binimg = numpy.zeros((200, 200, 20, 1), dtype=numpy.uint8)
        
        self.rawimg[0:100, :, :, :] = 50
        #small white
        self.rawimg[5:10, 5:10, 9:11, :] = 255
        self.rawimg[20:25, 20:25, 9:11, :] = 255
        self.rawimg[35:40, 30:35, 9:11, :] = 255
        self.rawimg[50:55, 50:55, 9:11, :] = 255
        
        self.rawimg[105:110, 5:10, 9:11, :] = 255
        self.rawimg[120:125, 20:25, 9:11, :] = 255
        self.rawimg[135:140, 30:35, 9:11, :] = 255
        self.rawimg[150:155, 150:155, 9:11, :] = 255
        
        #small grey
        self.rawimg[145:150, 5:10, 9:11, :] = 150
        self.rawimg[160:165, 40:45, 9:11, :] = 150
        self.rawimg[175:180, 20:25, 9:11, :] = 150
        self.rawimg[175:180, 5:10, 9:11, :] = 150
        
        self.rawimg[45:50, 5:10, 9:11, :] = 150
        self.rawimg[60:65, 40:45, 9:11, :] = 150
        self.rawimg[75:80, 20:25, 9:11, :] = 150
        self.rawimg[75:80, 5:10, 9:11, :] = 150
        
        #large white
        self.rawimg[50:70, 150:170, 9:11, :] = 255
        self.rawimg[5:25, 60:80, 9:11, :] = 255
        self.rawimg[5:25, 170:190, 9:11, :] = 255
        self.rawimg[70:90, 90:110, 9:11, :] = 255
        
        self.rawimg[150:170, 150:170, 9:11, :] = 255
        self.rawimg[105:125, 60:80, 9:11, :] = 255
        self.rawimg[105:125, 170:190, 9:11, :] = 255
        self.rawimg[170:190, 90:110, 9:11, :] = 255
        
        #large grey
        self.rawimg[5:25, 90:110, 9:11, :] = 150
        self.rawimg[30:50, 90:110, 9:11, :] = 150
        self.rawimg[5:25, 120:140, 9:11, :] = 150
        self.rawimg[30:50, 120:140, 9:11, :] = 150
        
        self.rawimg[105:125, 90:110, 9:11, :] = 150
        self.rawimg[130:150, 90:110, 9:11, :] = 150
        self.rawimg[105:125, 120:140, 9:11, :] = 150
        self.rawimg[130:150, 120:140, 9:11, :] = 150
        
        self.binimg = (self.rawimg>55).astype(numpy.uint8)
        
        #make one with multiple repeating time steps
        self.rawimgt = numpy.zeros((4,)+self.rawimg.shape, dtype=self.rawimg.dtype)
        self.binimgt = numpy.zeros(self.rawimgt.shape, dtype=numpy.uint8)
        for t in range(self.rawimgt.shape[0]):
            self.rawimgt[t, :] = self.rawimg[:]
            self.binimgt[t, :] = self.binimg[:]
        self.rawimgt = vigra.taggedView(self.rawimgt, 'txyzc')
        self.binimgt = vigra.taggedView(self.binimgt, 'txyzc')
        
        #make 5d, the workflow has a make 5d in the beginning of the pipeline
        self.rawimg = self.rawimg.reshape((1,)+self.rawimg.shape)
        self.rawimg = vigra.taggedView(self.rawimg, 'txyzc')
        self.binimg = self.binimg.reshape((1,)+self.binimg.shape)
        self.binimg = vigra.taggedView(self.binimg, 'txyzc')
        
        

    def testNoTime(self):
        
        gr = Graph()
        opExtract = OpObjectExtraction(graph=gr)
        opPredict = OpObjectClassification(graph=gr)
        
        opExtract.RawImage.setValue(self.rawimg)
        opExtract.BinaryImage.setValue(self.binimg)
        opExtract.Features.setValue(self.features)
        
        opPredict.RawImages.setValues([self.rawimg])
        opPredict.BinaryImages.setValues([self.binimg])
        opPredict.SegmentationImages.resize(1)
        opPredict.SegmentationImages[0].connect(opExtract.LabelImage)
        opPredict.ObjectFeatures.resize(1)
        opPredict.ObjectFeatures[0].connect(opExtract.RegionFeatures)
        opPredict.ComputedFeatureNames.connect(opExtract.Features)
        
        #run the workflow with the test blocks in the gui, 
        #if you want to see why these labels are chosen
        #object 11 -small white square
        #object 27 -large grey square
        labelArray = numpy.zeros((28,))
        labelArray[11] = 1
        labelArray[27] = 2
        labelDict = {0: labelArray}
        opPredict.LabelInputs.setValues([labelDict])
        
        #Predict by size
        selFeatures = {"Standard Object Features": {"Count":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        
        #[0][0] - first image, first time slice
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert numpy.all(predicted_labels[1:16]==1)
        assert numpy.all(predicted_labels[16:]==2)
        
        #Predict by color
        selFeatures = {"Standard Object Features": {"Mean":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert predicted_labels[1]==1
        assert predicted_labels[11]==1
        assert predicted_labels[16]==1
        assert predicted_labels[23]==1
        assert predicted_labels[2]==2
        assert predicted_labels[18]==2
        assert predicted_labels[24]==2
        assert predicted_labels[26]==2        
        
        #Predict by neighborhood color
        selFeatures = {"Standard Object Features": {"Mean in neighborhood":{"margin": (5, 5, 2)}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert predicted_labels[1]==1
        assert predicted_labels[8]==1
        assert predicted_labels[24]==1
        assert predicted_labels[28]==1
        assert predicted_labels[9]==2
        assert predicted_labels[14]==2
        assert predicted_labels[26]==2
        assert predicted_labels[29]==2

    def testTime(self):
        # Move the labels around different time steps.
        # Assert the same results 
        
        gr = Graph()
        opExtract = OpObjectExtraction(graph=gr)
        opPredict = OpObjectClassification(graph=gr)
        
        opExtract.RawImage.setValue(self.rawimg)
        opExtract.BinaryImage.setValue(self.binimg)
        opExtract.Features.setValue(self.features)
        
        opPredict.RawImages.setValues([self.rawimg])
        opPredict.BinaryImages.setValues([self.binimg])
        opPredict.SegmentationImages.resize(1)
        opPredict.SegmentationImages[0].connect(opExtract.LabelImage)
        opPredict.ObjectFeatures.resize(1)
        opPredict.ObjectFeatures[0].connect(opExtract.RegionFeatures)
        opPredict.ComputedFeatureNames.connect(opExtract.Features)
        
        grT = Graph()
        opExtractT = OpObjectExtraction(graph=grT)
        opPredictT = OpObjectClassification(graph=grT)
        
        opExtractT.RawImage.setValue(self.rawimgt)
        opExtractT.BinaryImage.setValue(self.binimgt)
        opExtractT.Features.setValue(self.features)
        
        opPredictT.RawImages.setValues([self.rawimgt])
        opPredictT.BinaryImages.setValues([self.binimgt])
        opPredictT.SegmentationImages.resize(1)
        opPredictT.SegmentationImages[0].connect(opExtractT.LabelImage)
        opPredictT.ObjectFeatures.resize(1)
        opPredictT.ObjectFeatures[0].connect(opExtractT.RegionFeatures)
        opPredictT.ComputedFeatureNames.connect(opExtractT.Features)
        
        #run the workflow with the test blocks in the gui, 
        #if you want to see why these labels are chosen
        #object 11 -small white square
        #object 27 -large grey square
        labelArray = numpy.zeros((28,))
        labelArray[11] = 1
        labelArray[27] = 2
        labelDict = {0: labelArray}
        opPredict.LabelInputs.setValues([labelDict])
        
        labelArray11 = numpy.zeros((12,))
        labelArray11[11] = 1
        labelArray27 = numpy.zeros((28,))
        labelArray27[27] = 2
        labelArray0 = numpy.zeros((2,))
        labelDictT = {0: labelArray0, 1:labelArray11, 2:labelArray0, 3:labelArray27}
        opPredictT.LabelInputs.setValues([labelDictT])
        
        
        #Predict by size
        selFeatures = {"Standard Object Features": {"Count":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        #[0][0] - first image, first time slice
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert numpy.all(predicted_labels[1:16]==1)
        assert numpy.all(predicted_labels[16:]==2)
        
        opPredictT.SelectedFeatures.setValue(selFeatures)
        predictionsT = opPredictT.Predictions[0][1].wait()
        predicted_labels_T = predictionsT[1]
        assert predicted_labels_T[0]==0
        assert numpy.all(predicted_labels_T[1:16]==1)
        assert numpy.all(predicted_labels_T[16:]==2)
        
        #Predict by color
        selFeatures = {"Standard Object Features": {"Mean":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert predicted_labels[1]==1
        assert predicted_labels[11]==1
        assert predicted_labels[16]==1
        assert predicted_labels[23]==1
        assert predicted_labels[2]==2
        assert predicted_labels[18]==2
        assert predicted_labels[24]==2
        assert predicted_labels[26]==2        
        
        opPredictT.SelectedFeatures.setValue(selFeatures)
        predictionsT = opPredictT.Predictions[0][2].wait()
        predicted_labels_T = predictionsT[2]
        assert predicted_labels_T[0]==0
        assert predicted_labels_T[1]==1
        assert predicted_labels_T[11]==1
        assert predicted_labels_T[16]==1
        assert predicted_labels_T[23]==1
        assert predicted_labels_T[2]==2
        assert predicted_labels_T[18]==2
        assert predicted_labels_T[24]==2
        assert predicted_labels_T[26]==2        
        
        #Predict by neighborhood color
        selFeatures = {"Standard Object Features": {"Mean in neighborhood":{"margin": (5, 5, 2)}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert predicted_labels[1]==1
        assert predicted_labels[8]==1
        assert predicted_labels[24]==1
        assert predicted_labels[28]==1
        assert predicted_labels[9]==2
        assert predicted_labels[14]==2
        assert predicted_labels[26]==2
        assert predicted_labels[29]==2
        
        opPredictT.SelectedFeatures.setValue(selFeatures)
        predictionsT = opPredictT.Predictions[0][3].wait()
        predicted_labels_T = predictionsT[3]
        assert predicted_labels_T[0]==0
        assert predicted_labels_T[1]==1
        assert predicted_labels_T[8]==1
        assert predicted_labels_T[24]==1
        assert predicted_labels_T[28]==1
        assert predicted_labels_T[9]==2
        assert predicted_labels_T[14]==2
        assert predicted_labels_T[26]==2
        assert predicted_labels_T[29]==2
        
    def testMultipleImages(self):
        # Now add the images multiple times and distribute labels
        # between different copies. Assert same results
        
        gr = Graph()
        opPredict = OpObjectClassification(graph=gr)
        
        bin_orig = self.binimg.squeeze()
        segimg = vigra.analysis.labelVolumeWithBackground(bin_orig)
        
        vfeats = vigra.analysis.extractRegionFeatures(segimg.astype(numpy.float32), segimg, ["Count"])
        counts = vfeats["Count"]
        counts[0] = 0
        counts = counts.reshape(counts.shape+(1,))
        
        feats = {0: {"Standard Object Features": {"Count": counts}}}
        featnames = {'Standard Object Features': {'Count': {}}}
        
        segimg = segimg.reshape((1,)+segimg.shape+(1,))
        segimg = vigra.taggedView(segimg, 'txyzc')
        
        opPredict.RawImages.setValues([self.rawimg, self.rawimg, self.rawimg])
        opPredict.BinaryImages.setValues([self.binimg, self.binimg, self.binimg])
        opPredict.SegmentationImages.setValues([segimg, segimg, segimg])
        
        opPredict.ObjectFeatures.setValues([feats, feats, feats])
        
        opPredict.ComputedFeatureNames.setValue(featnames)
        
        #run the workflow with the test blocks in the gui, 
        #if you want to see why these labels are chosen
        #object 11 -small white square
        #object 27 -large grey square
        labelArray11 = numpy.zeros((12,))
        labelArray11[11] = 1
        labelArray27 = numpy.zeros((28,))
        labelArray27[27] = 2
        
        labelArray0 = numpy.zeros((2,))
        labelDict11 = {0: labelArray11}
        labelDict27 = {0: labelArray27}
        labelDict0 = {0: labelArray0}
        opPredict.LabelInputs.setValues([labelDict11, labelDict0, labelDict27])
        
        #Predict by size
        selFeatures = {"Standard Object Features": {"Count":{}}}
        opPredict.SelectedFeatures.setValue(selFeatures)
        #[0][0] - first image, first time slice
        predictions = opPredict.Predictions[0][0].wait()
        predicted_labels = predictions[0]
        assert predicted_labels[0]==0
        assert numpy.all(predicted_labels[1:16]==1)
        assert numpy.all(predicted_labels[16:]==2)
