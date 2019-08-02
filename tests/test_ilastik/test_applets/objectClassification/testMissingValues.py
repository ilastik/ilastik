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
import unittest

from ilastik.applets.objectClassification.opObjectClassification import OpObjectClassification, \
                                                                        OpObjectTrain, OpObjectPredict

import numpy
import vigra
from lazyflow.graph import Graph

class TestMissingValueHandling(unittest.TestCase):
    def setUp(self):
        self.rawimg = numpy.random.randint(0, 256, (1, 200, 200, 1, 1))
        self.binimg = self.rawimg>100
        cc = vigra.analysis.labelImageWithBackground(self.binimg.squeeze().astype(numpy.uint8))
        nobj = numpy.max(cc)
        if nobj<7:
            #somehow, we randomly didn't get enough objects.
            #generate some bright points instead
            self.rawimg[3, 3] = 255
            self.rawimg[6, 6] = 255
            self.rawimg[10, 10] = 255
            self.rawimg[20, 20] = 255
            self.rawimg[30, 30] = 255
            self.rawimg[50, 50] = 255
            self.rawimg[100, 100] = 255
            self.rawimg[150, 150] = 255
            self.binimg = self.rawimg>100
            cc = vigra.analysis.labelImageWithBackground(self.binimg.squeeze())
            
        self.segmimg = cc.reshape((1, )+cc.shape+(1,)+(1,))
        
        self.rawimg = vigra.taggedView(self.rawimg, 'txyzc')
        self.binimg = vigra.taggedView(self.binimg, 'txyzc')
        self.segmimg = vigra.taggedView(self.segmimg, 'txyzc')
        
        self.features = {"Bad Plugin": {"bad_feature_1": {}, "bad_feature_2":{}}}
        featureArray1 = numpy.zeros((nobj+1,1))
        featureArray1[2][0] = numpy.Inf
        featureArray1[4][0] = numpy.inf
        featureArray2 = numpy.zeros((nobj+1,1))
        featureArray2[1][0] = numpy.NaN
        featureArray2[3][0] = numpy.nan
        
        
        self.featureArrays = {0: {"Bad Plugin":{"bad_feature_1": featureArray1, \
                                               "bad_feature_2": featureArray2}}}
        
        g = Graph()
        self.op = OpObjectClassification(graph = g)
        self.op.RawImages.setValues([self.rawimg])
        self.op.BinaryImages.setValues([self.binimg])
        self.op.SegmentationImages.setValues([self.segmimg])
        self.op.ObjectFeatures.setValues([self.featureArrays])
        self.op.ComputedFeatureNames.setValue(self.features)
        self.op.SelectedFeatures.setValue(self.features)
        
    def testTrain(self):
        
        #label the objects with bad features
        labelArray = numpy.zeros((7,))
        labelArray[1] = 1
        labelArray[3] = 2
        self.op.LabelInputs.setValues([{0: labelArray}])
        
        cl = self.op.Classifier[:].wait()
        warnings = self.op.Warnings[:].wait()
        details = warnings["details"]
        assert "Objects 1, 3" in details
        
    def testPredict(self):
        #label 2 good objects
        labelArray = numpy.zeros((7,))
        labelArray[5]=1
        labelArray[6]=1
        self.op.LabelInputs.setValues([{0: labelArray}])
        
        ambigs = self.op.BadObjects[0][0].wait()
        assert numpy.all(ambigs[0][1:5]==1)
        assert ambigs[0][0]==0
        assert numpy.all(ambigs[0][5:]==0)
        
        ambig_images = self.op.BadObjectImages[0][:].wait()
        #print ambig_images[self.segmimg==1]
        assert numpy.all(ambig_images[self.segmimg==1]==1)
        assert numpy.all(ambig_images[self.segmimg==2]==1)
        assert numpy.all(ambig_images[self.segmimg==3]==1)
        assert numpy.all(ambig_images[self.segmimg==4]==1)
