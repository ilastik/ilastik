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
from __future__ import division
from builtins import range
import sys
import warnings
import tempfile
import unittest

import numpy
import vigra
import h5py

from lazyflow.graph import Graph
from lazyflow.operators.opReorderAxes import OpReorderAxes

from ilastik.applets import objectExtraction
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtraction
from ilastik.applets.objectClassification.opObjectClassification import OpObjectClassification
from ilastik.applets.blockwiseObjectClassification import OpBlockwiseObjectClassification

import logging
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s %(name)s %(message)s')
handler.setFormatter(formatter)

# Test
logger = logging.getLogger("tests.testOpBlockwiseObjectClassification")
# Test Trace
traceLogger = logging.getLogger("TRACE." + logger.name)

WRITE_DEBUG_IMAGES = False


class TestOpBlockwiseObjectClassification(unittest.TestCase):
    
    def setUp(self):
        self.setUpSources()
        self.setUpObjExtraction()
        self.setUpClassifier()
        self.connectLanes()
    
    def testStandardBlockwisePrediction(self):
        # First, try with the default block/halo sizes, which will yield only one block with our test volume
        pred = self.op.PredictionImage[:].wait()
        if not (pred == self.prediction_volume).all():
            self.logImage(pred, "standard_blocksize_prediction_")
            assert False, \
                "Blockwise prediction operator did not produce the same prediction image" \
                "as the non-blockwise prediction operator!"

    def testPredictionChannelImage(self):
        # First, try with the default block/halo sizes, which will yield only one block with our test volume
        pred = self.op.ProbabilityChannelImage[:].wait()
        assert pred.shape[:-1] == self.prediction_volume.shape[:-1]
        assert pred.shape[-1] == 2
        argmax_pred = numpy.argmax( pred, axis=-1 )[...,None] + 1
        argmax_pred[pred.sum(-1) == 0] = 0
        if not (argmax_pred == self.prediction_volume).all():
            self.logImage(pred, "standard_blocksize_prediction_channels_")
            assert False, \
                "Blockwise prediction channels did not correspond to the expected prediction image"

    def testSmallerBlocks(self):
        # this block and halo size combination should be large enough for our cubes
        # Note: To produce results that are identical to the non-blockwise classification,
        #       the halo must be large enough to accommodate the 'margin' setting (see setupSources()),
        #       or the 'margin' must be small enough that it makes no difference anyway 
        #       (e.g. in our test data, no more than 10 pixels)
        self.op.BlockShape3dDict.setValue( {'x' : 42, 'y' : 42, 'z' : 42} )
        self.op.HaloPadding3dDict.setValue( {'x' : 35, 'y' : 35, 'z' : 30} )
         
        pred = self.op.PredictionImage[:].wait()
        if not (pred == self.prediction_volume).all():
            self.logImage(pred, "smaller_blocksize_prediction_")
            assert False, \
                "Blockwise prediction operator did not produce the same prediction image" \
                "as the non-blockwise prediction operator!"
             
    def testTinyBlocks(self):
        # 5x5x5 cubes should fit into a 10x10x10 halo
        # Note: To produce results that are identical to the non-blockwise classification,
        #       the halo must be large enough to accommodate the 'margin' setting (see setupSources()),
        #       or the 'margin' must be small enough that it makes no difference anyway 
        #       (e.g. in our test data, no more than 10 pixels)
        self.op.BlockShape3dDict.setValue( {'x' : 40, 'y' : 40, 'z' : 40} )
        self.op.HaloPadding3dDict.setValue( {'x' : 10, 'y' : 10, 'z' : 10} )
         
        pred = self.op.PredictionImage[:].wait()
        if not (pred == self.prediction_volume).all():
            self.logImage(pred, "tiny_blocksize_failed_prediction_")
            assert False, \
                "Blockwise prediction operator did not produce the same prediction image" \
                "as the non-blockwise prediction operator!"
 
    def testZeroHalo(self):
        # If we shrink the halo down to zero, then we get different predictions...
        # This block shape/halo combination will slice through some of the big blocks, causing mis-classification.
        # That's what we expect.
        self.op.BlockShape3dDict.setValue( {'x' : 42, 'y' : 42, 'z' : 42} )
        self.op.HaloPadding3dDict.setValue( {'x' : 0, 'y' : 0, 'z' : 0} )
         
        blockwise_prediction_volume = self.op.PredictionImage[:].wait()
        assert not (blockwise_prediction_volume == self.prediction_volume).all(), \
            "Blockwise prediction operator produced the same prediction image" \
            "as the non-blockwise prediction operator, despite having a pathological block/halo combination!"
             
                 
    def setUpSources(self):
        """
        Create big cubes with starting corners at multiples of 20, and small cubes offset 10 from that.
        Half of the image will be white, the other half gray.
        """

        self.testingFeatures = {"Standard Object Features": {"Count":{}, "Mean":{}, "Mean in neighborhood":{"margin":(10, 10, 1)}}}
        
        # Big: Starting at 0,20,40, etc.
        # Small: Starting at 10,30,50, etc.
        self.bigCubes = cubes( (100,100,100), 5, cubedist=20 )
        self.smallCubes = cubes( (100,100,100), 2, cubedist=20, cubeoffset = 10 )

        self.test_volume_binary = (self.bigCubes | self.smallCubes).astype( numpy.uint8 )
        self.test_volume_binary = self.test_volume_binary.view( vigra.VigraArray )
        self.test_volume_binary.axistags = vigra.defaultAxistags('xyz')
        
        name = writeToTempFile(self.test_volume_binary, prefix='binary_')
        if name:
            logger.debug("Wrote binary image to '{}'".format(name))
        
        # Gray: 0<=x<50
        # White: 50<=x<100
        self.test_volume_intensity = self.test_volume_binary * 255
        self.test_volume_intensity[ 0:50 ] //= 2
        self.test_volume_intensity = self.test_volume_intensity.view( vigra.VigraArray )
        self.test_volume_intensity.axistags = vigra.defaultAxistags('xyz')
        
        name = writeToTempFile(self.test_volume_intensity, prefix='intensity_')
        if name:
            logger.debug("Wrote intensity image to '{}'".format(name))

        graph = Graph()
        self.graph = graph

        # provide 5d input 
        op5Raw = OpReorderAxes( graph=graph )
        op5Raw.Input.setValue( self.test_volume_intensity )
        op5Raw.AxisOrder.setValue( 'txyzc' )
        self.rawSource = op5Raw
        
        op5Binary = OpReorderAxes( graph=graph )
        op5Binary.Input.setValue( self.test_volume_binary )
        op5Binary.AxisOrder.setValue( 'txyzc' )
        self.binarySource = op5Binary
        
    def setUpObjExtraction(self):
        opObjectExtraction = OpObjectExtraction( graph=self.graph )

        opObjectExtraction.RawImage.connect( self.rawSource.Output )
        opObjectExtraction.BinaryImage.connect( self.binarySource.Output )
        opObjectExtraction.BackgroundLabels.setValue( [0] )
        opObjectExtraction.Features.setValue(self.testingFeatures)
        
        self.objExtraction = opObjectExtraction
        

    def setUpClassifier(self):
        ''' 
        Prepare the classifier that will be used in blockwise prediction.
        Errors that occur here are real errors (as opposed to test failures).
        '''
        
        opObjectClassification = OpObjectClassification( graph=self.graph )
        
        # STEP 1: connect the operator
        
        # raw image data, i.e. cubes with intensity 1 or 1/2
        opObjectClassification.RawImages.resize(1)
        opObjectClassification.RawImages[0].connect( self.rawSource.Output )
        
        # threshold images, i.e. cubes with intensity 1
        opObjectClassification.BinaryImages.resize(1)
        opObjectClassification.BinaryImages.connect( self.binarySource.Output )
        
        # segmentation images from object extraction
        opObjectClassification.SegmentationImages.resize(1)
        opObjectClassification.SegmentationImages[0].connect( self.objExtraction.LabelImage )

        opObjectClassification.ObjectFeatures.resize(1)
        opObjectClassification.ObjectFeatures[0].connect( self.objExtraction.RegionFeatures )
        
        opObjectClassification.SelectedFeatures.setValue(self.testingFeatures)
        opObjectClassification.ComputedFeatureNames.connect(self.objExtraction.Features)
        
        # STEP 2: simulate labeling
        
        object_volume = self.objExtraction.LabelImage[:].wait()
        raw_5d = self.rawSource.Output[:].wait()

        # Big: Starting at 0,20,40, etc.
        # Small: Starting at 10,30,50, etc.
        
        # Gray: 0<=x<50
        # White: 50<=x<100

        # Must provide label names, since that determines the number of classes the operator knows about.
        opObjectClassification.LabelNames.setValue( ["BigWhite and SmallGray", "SmallWhite and Big Gray"] )

        # big & white: label 1
        big_white_coords = [(0, 60, 0, 0, 0), (0, 60, 20, 0, 0), (0, 60, 0, 20, 0)]
        for coord in big_white_coords:
            assert raw_5d[coord] == 255, "Input data error: expected this pixel to be white, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 1)
 
        # small & gray: label 1
        small_gray_coords = [(0, 10, 10, 10, 0), (0, 10, 30, 10, 0), (0, 10, 10, 30, 0)]
        for coord in small_gray_coords:
            assert raw_5d[coord] == 255//2, "Input data error: expected this pixel to be gray, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 1)

        # small & white: label 2
        small_white_coords = [(0, 70, 10, 10, 0), (0, 70, 30, 10, 0), (0, 70, 10, 30, 0)]
        for coord in small_white_coords:
            assert raw_5d[coord] == 255, "Input data error: expected this pixel to be white, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 2)
        
        # big & gray: label 2
        big_gray_coords = [(0, 0, 0, 0, 0), (0, 0, 20, 0, 0), (0, 0, 0, 20, 0)]
        for coord in big_gray_coords:
            assert raw_5d[coord] == 255//2, "Input data error: expected this pixel to be gray, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 2)

        assert opObjectClassification.SegmentationImages[0].ready()
        assert opObjectClassification.NumLabels.value == 2, "Wrong number of labels: {}".format( opObjectClassification.NumLabels.value )
        
        prediction_volume = opObjectClassification.PredictionImages[0][:].wait()
        self.prediction_volume = prediction_volume
        
        coordE = (0, 60, 20, 20, 0)
        assert prediction_volume[coordE] == 1, "Expected object #{} to be predicted as class 1, but got prediction {}".format( object_volume[coordE], prediction_volume[coordE] )
        coordF = (0, 10, 30, 30, 0)
        assert prediction_volume[coordF] == 1, "Expected object #{} to be predicted as class 1, but got prediction {}".format( object_volume[coordF], prediction_volume[coordF] )

        coordG = (0, 70, 30, 30, 0)
        assert prediction_volume[coordG] == 2, "Expected object #{} to be predicted as class 2, but got prediction {}".format( object_volume[coordG], prediction_volume[coordG] )
        coordH = (0, 20, 20, 20, 0)
        assert prediction_volume[coordH] == 2, "Expected object #{} to be predicted as class 2, but got prediction {}".format( object_volume[coordH], prediction_volume[coordH] )
        
        self.classifier = opObjectClassification
        
    def connectLanes(self):
        opBlockwise = OpBlockwiseObjectClassification( graph=self.graph )

        opBlockwise.RawImage.connect( self.classifier.RawImages[0] )
        opBlockwise.BinaryImage.connect( self.classifier.BinaryImages[0] )
        opBlockwise.Classifier.connect( self.classifier.Classifier )
        opBlockwise.LabelsCount.connect( self.classifier.NumLabels )
        opBlockwise.SelectedFeatures.connect( self.classifier.SelectedFeatures )
        self.op = opBlockwise
        
    def logImage(self,data,prefix='logged_image'):
        name = writeToTempFile(data.view(vigra.VigraArray), prefix=prefix)
        if name:
            logger.debug("Wrote an image to {}".format(name))
 
def getlist(a, n=3):
    try:
        len(a)
    except TypeError:
        a = [a]*n
    
    assert len(a)==n
    return a

def cubes(dimblock, dimcube, cubedist=20, cubeoffset=0):
    n = len(dimblock)
    dimcube = getlist(dimcube, n=n)
    cubedist = getlist(cubedist, n=n)
    cubeoffset = getlist(cubeoffset, n=n)
    
    indices = numpy.indices(dimblock)
    indices = numpy.rollaxis( indices, 0, len(dimblock)+1 )
    
    out = numpy.ones(dimblock, dtype=numpy.bool)
    
    for i in range(len(dimblock)):
        out = numpy.bitwise_and(out,(indices[...,i] + cubeoffset[i]) % cubedist[i] < dimcube[i])
    out = out.astype(numpy.uint8)
    return out

def writeToTempFile(data,pathInFile='volume',prefix='test_image_'):
    '''
    Writes the given 
    '''
    global WRITE_DEBUG_IMAGES
    if not WRITE_DEBUG_IMAGES:
        return None
    
    # we just need this to know where to place temp files, vigra needs a filename
    name = tempfile.mkdtemp()
    with h5py.File(name, 'w') as f:
        f.create_dataset(pathInFile, data=data)
    return name   
