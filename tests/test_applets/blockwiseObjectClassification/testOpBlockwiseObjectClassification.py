import sys
import warnings
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
        """
        Create big cubes with starting corners at multiples of 20, and small cubes offset 10 from that.
        Half of the image will be white, the other half gray.
        """
        
        self.testingFeatures = ['Count', 'Mean']
        objectExtraction.config.vigra_features = self.testingFeatures
        objectExtraction.config.other_features = []
        objectExtraction.config.selected_features = self.testingFeatures
        
        # Big: Starting at 0,20,40, etc.
        # Small: Starting at 10,30,50, etc.
        
        indexes = numpy.indices( (100,100,100) )
        indexes = numpy.rollaxis( indexes, 0, 4 )
        thick_planes_x = indexes[...,0] % 20 < 5
        thick_planes_y = indexes[...,1] % 20 < 5
        thick_planes_z = indexes[...,2] % 20 < 5

        thin_planes_x = (indexes[...,0] + 10) % 20 < 2
        thin_planes_y = (indexes[...,1] + 10) % 20 < 2
        thin_planes_z = (indexes[...,2] + 10) % 20 < 2

        big_cubes = (thick_planes_x & thick_planes_y & thick_planes_z).astype( numpy.uint8 )
        small_cubes = (thin_planes_x & thin_planes_y & thin_planes_z).astype( numpy.uint8 )
        self.test_volume_binary = (big_cubes | small_cubes).astype( numpy.uint8 )
        self.test_volume_binary = self.test_volume_binary.view( vigra.VigraArray )
        self.test_volume_binary.axistags = vigra.defaultAxistags('xyz')

        self.test_volume_binary.writeHDF5( '/tmp/debug_binary.h5', 'volume' )

        # Gray: 0<=x<50
        # White: 50<=x<100
        self.test_volume_intensity = self.test_volume_binary * 255
        self.test_volume_intensity[ 0:50 ] /= 2
        self.test_volume_intensity = self.test_volume_intensity.view( vigra.VigraArray )
        self.test_volume_intensity.axistags = vigra.defaultAxistags('xyz')
        
        self.test_volume_intensity.writeHDF5( '/tmp/debug_intensity.h5', 'volume' )
        
        self.test_volume_labeled = vigra.analysis.labelVolumeWithBackground( self.test_volume_binary )
        self.test_volume_labeled = self.test_volume_labeled.view( vigra.VigraArray )
        self.test_volume_labeled.axistags = vigra.defaultAxistags('xyz')
        
    
    def testOpObjectClassification(self):
        graph = Graph()

        op5Raw = Op5ifyer( graph=graph )
        op5Raw.input.setValue( self.test_volume_intensity )

        op5Binary = Op5ifyer( graph=graph )
        op5Binary.input.setValue( self.test_volume_binary )
        
        opObjectExtraction = OpObjectExtraction( graph=graph )

        opObjectExtraction.RawImage.connect( op5Raw.output )
        opObjectExtraction.BinaryImage.connect( op5Binary.output )
        opObjectExtraction.BackgroundLabels.setValue( [0] )
        
        # Ensure subset
        assert set(self.testingFeatures) <= set(opObjectExtraction._opRegFeats._featureNames[0]) 

        opObjectClassification = OpObjectClassification( graph=graph )
        opObjectClassification.RawImages.resize(1)
        opObjectClassification.RawImages[0].connect( op5Raw.output )
        
        opObjectClassification.BinaryImages.resize(1)
        opObjectClassification.BinaryImages.connect( op5Binary.output )
        
        opObjectClassification.SegmentationImages.resize(1)
        opObjectClassification.SegmentationImages[0].connect( opObjectExtraction.LabelImage )

        opObjectClassification.ObjectFeatures.resize(1)
        opObjectClassification.ObjectFeatures[0].connect( opObjectExtraction.RegionFeatures )

        opObjectClassification.LabelsAllowedFlags.setValues( [True] )

        object_volume = opObjectExtraction.LabelImage[:].wait()
        raw_5d = op5Raw.output[:].wait()

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

        coordE = (0, 60, 20, 20, 0)
        assert prediction_volume[coordE] == 1, "Expected object #{} to be predicted as class 1, but got prediction {}".format( object_volume[coordE], prediction_volume[coordE] )
        coordF = (0, 10, 30, 30, 0)
        assert prediction_volume[coordF] == 1, "Expected object #{} to be predicted as class 1, but got prediction {}".format( object_volume[coordF], prediction_volume[coordF] )

        coordG = (0, 70, 30, 30, 0)
        assert prediction_volume[coordG] == 2, "Expected object #{} to be predicted as class 2, but got prediction {}".format( object_volume[coordG], prediction_volume[coordG] )
        coordH = (0, 20, 20, 20, 0)
        assert prediction_volume[coordH] == 2, "Expected object #{} to be predicted as class 2, but got prediction {}".format( object_volume[coordH], prediction_volume[coordH] )

        opBlockwise = OpBlockwiseObjectClassification( graph=Graph() )
        
        # First, try with the default block/halo sizes, which will yield only one block with our test volume
        opBlockwise.RawImage.connect( opObjectClassification.RawImages[0] )
        opBlockwise.BinaryImage.connect( opObjectClassification.BinaryImages[0] )
        opBlockwise.Classifier.connect( opObjectClassification.Classifier )

        assert (opBlockwise.PredictionImage[:].wait() == prediction_volume).all(), \
            "Blockwise prediction operator did not produce the same prediction image" \
            "as the non-blockwise prediction operator!"

        # Now try with smaller blocks.
        warnings.warn("FIXME: This halo choice is sensitive to OpRegionFeatures3d.margin")
        opBlockwise.BlockShape3dDict.setValue( {'x' : 42, 'y' : 42, 'z' : 42} )
        opBlockwise.HaloPadding3dDict.setValue( {'x' : 30, 'y' : 30, 'z' : 30} )
        
        blockwise_prediction_volume = opBlockwise.PredictionImage[:].wait()
        blockwise_prediction_volume.view(vigra.VigraArray).writeHDF5('/tmp/blockwise_prediction_volume.h5', 'volume')
        assert (blockwise_prediction_volume == prediction_volume).all(), \
            "Blockwise prediction operator did not produce the same prediction image" \
            "as the non-blockwise prediction operator!"

        # If we shrink the halo down to zero, then we get different predictions...
        warnings.warn("FIXME: This halo choice is sensitive to OpRegionFeatures3d.margin")
        opBlockwise.BlockShape3dDict.setValue( {'x' : 42, 'y' : 42, 'z' : 42} )
        opBlockwise.HaloPadding3dDict.setValue( {'x' : 0, 'y' : 0, 'z' : 0} )
        
        blockwise_prediction_volume = opBlockwise.PredictionImage[:].wait()
        #blockwise_prediction_volume.view(vigra.VigraArray).writeHDF5('/tmp/blockwise_prediction_volume.h5', 'volume')
        assert not (blockwise_prediction_volume == prediction_volume).all(), \
            "Blockwise prediction operator produced the same prediction image" \
            "as the non-blockwise prediction operator, despite having a pathological block/halo combination!"


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
