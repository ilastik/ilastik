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
import os
import numpy
from lazyflow.roi import sliceToRoi
from lazyflow.graph import Graph, OperatorWrapper
from lazyflow.operators.ioOperators import OpInputDataReader
from ilastik.applets.featureSelection.opFeatureSelection import OpFeatureSelection
import vigra

import ilastik.ilastik_logging
ilastik.ilastik_logging.default_config.init()

import unittest
import tempfile


class TestOpFeatureSelection(unittest.TestCase):
    def setUp(self):
        data = numpy.random.random((2,100,100,100,3))

        self.filePath = tempfile.mkdtemp() + '/featureSelectionTestData.npy'
        numpy.save(self.filePath, data)
    
        graph = Graph()

        # Define operators
        opFeatures = OperatorWrapper(OpFeatureSelection, graph=graph)
        opReader = OpInputDataReader(graph=graph)

        # Set input data
        opReader.FilePath.setValue( self.filePath )
        
        # Connect input
        opFeatures.InputImage.resize(1)
        opFeatures.InputImage[0].connect( opReader.Output )
        
        # Configure scales        
        scales = [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0]
        opFeatures.Scales.setValue(scales)
        
        # Configure feature types
        featureIds = [ 'GaussianSmoothing',
                       'LaplacianOfGaussian',
                       'StructureTensorEigenvalues',
                       'HessianOfGaussianEigenvalues',
                       'GaussianGradientMagnitude',
                       'DifferenceOfGaussians' ]
        opFeatures.FeatureIds.setValue(featureIds)

        # Configure matrix
        #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
        selections = numpy.array( [[True,  False, False, False, False, False, False],   # Gaussian
                                   [False,  True, False, False, False, False, False],   # L of G
                                   [False, False,  True, False, False, False, False],   # ST EVs
                                   [False, False, False, False, False, False, False],   # H of G EVs
                                   [False, False, False, False, False, False, False],   # GGM
                                   [False, False, False, False, False, False, False]] ) # Diff of G
        opFeatures.SelectionMatrix.setValue(selections)

        self.opFeatures = opFeatures
        self.opReader = opReader
        
    def tearDown(self):
        self.opFeatures.cleanUp()
        self.opReader.cleanUp()
        try:
            os.remove(self.filePath)
        except:
            pass
    
    def test_basicFunctionality(self):
        opFeatures = self.opFeatures
                
        # Compute results for the top slice only
        topSlice = [0, slice(None), slice(None), 0, slice(None)]
        result = opFeatures.OutputImage[0][topSlice].wait()
        
        numFeatures = numpy.sum(opFeatures.SelectionMatrix.value)
        outputChannels = result.shape[-1]

        # Input has 3 channels, and one of our features outputs a 3D vector
        assert outputChannels == 15 # (3 + 3 + 9)
        
        # Debug only -- Inspect the resulting images
        if False:
            # Export the first slice of each channel of the results as a separate image for display purposes.
            import vigra
            numFeatures = result.shape[-1]
            for featureIndex in range(0, numFeatures):
                featureSlice = list(topSlice)
                featureSlice[-1] = featureIndex
                vigra.impex.writeImage(result[featureSlice], "test_feature" + str(featureIndex) + ".bmp")
    
    def test_2d(self):
        graph = Graph()
        data2d = numpy.random.random((2,100,100,1,3))
        data2d = vigra.taggedView(data2d, axistags='txyzc')
        # Define operators
        opFeatures = OpFeatureSelection(graph=graph)
        opFeatures.Scales.connect(self.opFeatures.Scales[0])
        opFeatures.FeatureIds.connect(self.opFeatures.FeatureIds[0])
        opFeatures.SelectionMatrix.connect(self.opFeatures.SelectionMatrix[0])

        # Set input data
        opFeatures.InputImage.setValue(data2d)

        # Compute results for the top slice only
        topSlice = [0, slice(None), slice(None), 0, slice(None)]
        result = opFeatures.OutputImage[topSlice].wait()

    def testDirtyPropagation(self):
        opFeatures = self.opFeatures

        dirtyRois = []
        def handleDirty( slot, roi ):
            dirtyRois.append( roi )
        opFeatures.OutputImage[0].notifyDirty( handleDirty )

        # Change the matrix        
        selections = numpy.array( [[True,  False, False, False, False, False, False],   # Gaussian
                                   [False,  True, False, False, False, False, False],   # L of G
                                   [False, False,  True, False, False, False, False],   # ST EVs
                                   [False, False, False, True, False, False, False],   # H of G EVs
                                   [False, False, False, False, False, False, False],   # GGM
                                   [False, False, False, False, False, False, False]] ) # Diff of G
        opFeatures.SelectionMatrix.setValue(selections)
        
        assert len(dirtyRois) == 1
        assert (dirtyRois[0].start, dirtyRois[0].stop) == sliceToRoi( slice(None), self.opFeatures.OutputImage[0].meta.shape )
