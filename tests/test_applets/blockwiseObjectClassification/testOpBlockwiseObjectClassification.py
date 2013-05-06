import sys
import warnings
import tempfile

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import Op5ifyer

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


class TestOpBlockwiseObjectClassification(object):
    
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

    def testSmallerBlocks(self):
        # this block and halo size combination should be large enough for our cubes
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
        
        self.testingFeatures = {"Vigra Object Features": {"Count":{}, "Mean":{}, "Mean in neighborhood":{"margin":(30, 30, 1)}}}
        
        # Big: Starting at 0,20,40, etc.
        # Small: Starting at 10,30,50, etc.
        self.bigCubes = cubes( (100,100,100), 5, cubedist=20 )
        self.smallCubes = cubes( (100,100,100), 2, cubedist=20, cubeoffset = 10 )

        self.test_volume_binary = (self.bigCubes | self.smallCubes).astype( numpy.uint8 )
        self.test_volume_binary = self.test_volume_binary.view( vigra.VigraArray )
        self.test_volume_binary.axistags = vigra.defaultAxistags('xyz')
        
        name = writeToTempFile(self.test_volume_binary, prefix='binary_')
        logger.debug("Wrote binary image to '{}'".format(name))
        
        # Gray: 0<=x<50
        # White: 50<=x<100
        self.test_volume_intensity = self.test_volume_binary * 255
        self.test_volume_intensity[ 0:50 ] /= 2
        self.test_volume_intensity = self.test_volume_intensity.view( vigra.VigraArray )
        self.test_volume_intensity.axistags = vigra.defaultAxistags('xyz')
        
        name = writeToTempFile(self.test_volume_intensity, prefix='intensity_')
        logger.debug("Wrote intensity image to '{}'".format(name))

        graph = Graph()
        self.graph = graph

        # provide 5d input 
        op5Raw = Op5ifyer( graph=graph )
        op5Raw.input.setValue( self.test_volume_intensity )
        self.rawSource = op5Raw
        
        op5Binary = Op5ifyer( graph=graph )
        op5Binary.input.setValue( self.test_volume_binary )
        self.binarySource = op5Binary
        
    def setUpObjExtraction(self):
        opObjectExtraction = OpObjectExtraction( graph=self.graph )

        opObjectExtraction.RawImage.connect( self.rawSource.output )
        opObjectExtraction.BinaryImage.connect( self.binarySource.output )
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
        opObjectClassification.RawImages[0].connect( self.rawSource.output )
        
        # threshold images, i.e. cubes with intensity 1
        opObjectClassification.BinaryImages.resize(1)
        opObjectClassification.BinaryImages.connect( self.binarySource.output )
        
        # segmentation images from object extraction
        opObjectClassification.SegmentationImages.resize(1)
        opObjectClassification.SegmentationImages[0].connect( self.objExtraction.LabelImage )

        opObjectClassification.ObjectFeatures.resize(1)
        opObjectClassification.ObjectFeatures[0].connect( self.objExtraction.RegionFeatures )
        
        opObjectClassification.SelectedFeatures.setValue(self.testingFeatures)
        opObjectClassification.ComputedFeatureNames.connect(self.objExtraction.ComputedFeatureNames)
        
        opObjectClassification.LabelsAllowedFlags.setValues( [True] )
        
        # STEP 2: simulate labeling
        
        object_volume = self.objExtraction.LabelImage[:].wait()
        raw_5d = self.rawSource.output[:].wait()

        # Big: Starting at 0,20,40, etc.
        # Small: Starting at 10,30,50, etc.
        
        # Gray: 0<=x<50
        # White: 50<=x<100

        # big & white: label 1
        big_white_coords = [(0, 60, 0, 0, 0), (0, 60, 20, 0, 0), (0, 60, 0, 20, 0)]
        for coord in big_white_coords:
            assert raw_5d[coord] == 255, "Input data error: expected this pixel to be white, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 1)
 
        # small & gray: label 1
        small_gray_coords = [(0, 10, 10, 10, 0), (0, 10, 30, 10, 0), (0, 10, 10, 30, 0)]
        for coord in small_gray_coords:
            assert raw_5d[coord] == 255/2, "Input data error: expected this pixel to be gray, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 1)

        # small & white: label 2
        small_white_coords = [(0, 70, 10, 10, 0), (0, 70, 30, 10, 0), (0, 70, 10, 30, 0)]
        for coord in small_white_coords:
            assert raw_5d[coord] == 255, "Input data error: expected this pixel to be white, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 2)
        
        # big & gray: label 2
        big_gray_coords = [(0, 0, 0, 0, 0), (0, 0, 20, 0, 0), (0, 0, 0, 20, 0)]
        for coord in big_gray_coords:
            assert raw_5d[coord] == 255/2, "Input data error: expected this pixel to be gray, but it was {}".format( raw_5d[coord] )
            opObjectClassification.assignObjectLabel( 0, coord, 2)

        assert opObjectClassification.SegmentationImages[0].ready()
        assert opObjectClassification.NumLabels.value == 2
        
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
    writes a VigraArray to a random temporary file (disabled by default)
    input: as to writeHDF5
    output: filename
    '''
    #TODO remove before pull request
    # comment to write to file
    #return '/dev/null'
    
    # we just need this to know where to place temp files, vigra needs a filename
    f = tempfile.NamedTemporaryFile(prefix=prefix,suffix='.h5')
    name = f.name
    f.close()
    vigra.impex.writeHDF5(data, name, pathInFile)
    return name   
        

if __name__ == "__main__":

    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    logging.getLogger().addHandler( handler )
    logger.setLevel(logging.DEBUG)
    traceLogger.setLevel(logging.DEBUG)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
