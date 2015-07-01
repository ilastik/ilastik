###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
#		   http://ilastik.org/license/
###############################################################################
from lazyflow.operators.opArrayPiper import OpArrayPiper
from lazyflow.operators.ioOperators import OpH5WriterBigDataset
import numpy
import vigra
import h5py
import os
import sys
import lazyflow.graph

import logging
#logger = logging.getLogger(__name__)
#logger.addHandler(logging.StreamHandler(sys.stdout))
#logger.setLevel(logging.DEBUG)

logger = logging.getLogger("tests.testOpH5WriterBigDataset")
cacheLogger = logging.getLogger("lazyflow.operators.ioOperators.ioOperators.OpH5WriterBigDataset")
requesterLogger = logging.getLogger( "lazyflow.utility.bigRequestStreamer" )

class TestOpH5WriterBigDataset(object):
 
    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testDataFileName = 'bigH5TestData.h5'
        self.datasetInternalPath = 'volume/data'
 
        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray( self.dataShape, axistags=vigra.defaultAxistags('txyzc'), order='C' )
        self.testData[...] = numpy.indices(self.dataShape).sum(0)
 
    def tearDown(self):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataFileName)
        except:
            pass
 
    def test_Writer(self):
        # Create the h5 file
        hdf5File = h5py.File(self.testDataFileName)
         
        opPiper = OpArrayPiper(graph=self.graph)
        opPiper.Input.setValue( self.testData )
         
        opWriter = OpH5WriterBigDataset(graph=self.graph)
        opWriter.hdf5File.setValue( hdf5File )
        opWriter.hdf5Path.setValue( self.datasetInternalPath )
        opWriter.Image.connect( opPiper.Output )
 
        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success
 
        hdf5File.close()
 
        # Check the file.
        f = h5py.File(self.testDataFileName, 'r')
        dataset = f[self.datasetInternalPath]
        assert dataset.shape == self.dataShape
        assert numpy.all( dataset[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()
 
class TestOpH5WriterBigDataset_2(object):
 
    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testDataFileName = 'bigH5TestData.h5'
        self.datasetInternalPath = 'volume/data'
 
        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray( self.dataShape, axistags=vigra.defaultAxistags('txyzc') ) # default vigra order this time...
        self.testData[...] = numpy.indices(self.dataShape).sum(0)
 
    def tearDown(self):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataFileName)
        except:
            pass
 
    def test_Writer(self):
         
        # Create the h5 file
        hdf5File = h5py.File(self.testDataFileName)
 
        opPiper = OpArrayPiper(graph=self.graph)
        opPiper.Input.setValue( self.testData )        
         
        opWriter = OpH5WriterBigDataset(graph=self.graph)
         
        # This checks that you can give a preexisting group as the file
        g = hdf5File.create_group('volume')
        opWriter.hdf5File.setValue( g )
        opWriter.hdf5Path.setValue( "data" )
        opWriter.Image.connect( opPiper.Output )
 
        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success
 
        hdf5File.close()
 
        # Check the file.
        f = h5py.File(self.testDataFileName, 'r')
        dataset = f[self.datasetInternalPath]
        assert dataset.shape == self.dataShape
        assert numpy.all( dataset[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()

class TestOpH5WriterBigDataset_3(object):

    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self.testDataFileName = 'bigH5TestData.h5'
        self.datasetInternalPath = 'volume/data'

        # Generate some test data
        self.dataShape = (1, 10, 128, 128, 1)
        self.testData = vigra.VigraArray( self.dataShape, axistags=vigra.defaultAxistags('txyzc') ) # default vigra order this time...
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def tearDown(self):
        # Clean up: Delete the test file.
        try:
            os.remove(self.testDataFileName)
        except:
            pass

    def test_Writer(self):
        # Create the h5 file
        hdf5File = h5py.File(self.testDataFileName)

        opPiper = OpArrayPiper(graph=self.graph)
        opPiper.Input.setValue( self.testData )

        # Force extra metadata onto the output
        opPiper.Output.meta.ideal_blockshape = ( 1, 1, 0, 0, 1 )
        # Pretend the RAM usage will be really high to force lots of tiny blocks
        opPiper.Output.meta.ram_usage_per_requested_pixel = 1000000.0
        
        opWriter = OpH5WriterBigDataset(graph=self.graph)
        
        # This checks that you can give a preexisting group as the file
        g = hdf5File.create_group('volume')
        opWriter.hdf5File.setValue( g )
        opWriter.hdf5Path.setValue( "data" )
        opWriter.Image.connect( opPiper.Output )

        # Force the operator to execute by asking for the output (a bool)
        success = opWriter.WriteImage.value
        assert success

        hdf5File.close()

        # Check the file.
        f = h5py.File(self.testDataFileName, 'r')
        dataset = f[self.datasetInternalPath]
        assert dataset.shape == self.dataShape
        assert numpy.all( dataset[...] == self.testData.view(numpy.ndarray)[...] )
        f.close()

if __name__ == "__main__":
    # Set up logging for debug
    logHandler = logging.StreamHandler( sys.stdout )
    logger.addHandler( logHandler )
    cacheLogger.addHandler( logHandler )
    requesterLogger.addHandler( logHandler )

    logger.setLevel( logging.DEBUG )
    cacheLogger.setLevel( logging.DEBUG )
    requesterLogger.setLevel( logging.INFO )

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
