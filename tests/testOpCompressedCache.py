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
import sys
import logging
import threading
import functools
import time

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpCompressedCache, OpArrayPiper
from lazyflow.utility.slicingtools import slicing2shape
from lazyflow.operators.arrayCacheMemoryMgr import MemInfoNode

logger = logging.getLogger("tests.testOpCompressedCache")
cacheLogger = logging.getLogger("lazyflow.operators.opCompressedCache")

class TestOpCompressedCache( object ):
    
    def testBasic5d(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 100, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyzc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [1, 100, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:2, 0:100, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasic3d(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((100, 200, 150), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('xyz')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [100, 75, 50] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:100, 50:150, 75:150 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasic4d_txyc(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [1, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 1:3, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasic2d(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((200, 150), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [75, 50] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 50:150, 75:150 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testBasicOneBlock(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 100, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyzc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        # NO Block shape for this test.
        #op.BlockShape.setValue( [1, 100, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:2, 0:100, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testMultiThread(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((3, 100, 200, 150, 2), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('txyzc')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [1, 100, 75, 50, 2] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:2, 0:100, 50:150, 75:150, 0:1 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)

        results = {}
        def readData(resultIndex):        
            results[resultIndex] = op.Output[slicing].wait()

        threads = []
        for i in range( 10 ):
            threads.append( threading.Thread( target=functools.partial( readData, i ) ) )

        for th in threads:
            th.start()

        for th in threads:
            th.join()
        
        assert len( results ) == len( threads ), "Didn't get all results."
        
        #logger.debug("Checking data...")
        for i, data in results.items():
            assert (data == expectedData).all(), "Incorrect output for index {}".format( i )

    def testSetInSlot(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((100, 200, 150), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('xyz')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [100, 75, 50] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:100, 0:75, 0:50 ]
        expectedData = numpy.ones( slicing2shape(slicing), dtype=int )

        # This is what we're testing.
        #logger.debug("Forcing external data...")
        op.Input[slicing] = expectedData
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testReconnectWithoutRequest(self):
        vol = numpy.zeros((200, 100, 50), dtype=numpy.float32)
        vol1 = vigra.taggedView(vol, axistags='xyz')
        vol2 = vigra.taggedView(vol, axistags='zyx').withAxes(*'xyz')
        graph = Graph()

        opData1 = OpArrayPiper(graph=graph)
        opData1.Input.setValue(vol1)

        op = OpCompressedCache(graph=graph)
        op.Input.connect(opData1.Output)
        op.BlockShape.setValue((200, 100, 10))
        out = op.Output[...].wait()

        op.BlockShape.setValue((50, 100, 10))

        # Older versions of OpCompressedCache threw an exception here because 
        #  we tried to access the cache after changing the blockshape.
        # But in the current version, we claim that's okay.
        out = op.Output[...].wait()

    def testChangeBlockshape(self):
        logger.info("Generating sample data...")
        sampleData = numpy.indices((100, 200, 150), dtype=numpy.float32).sum(0)
        sampleData = sampleData.view( vigra.VigraArray )
        sampleData.axistags = vigra.defaultAxistags('xyz')
        
        graph = Graph()
        opData = OpArrayPiper( graph=graph )
        opData.Input.setValue( sampleData )
        
        op = OpCompressedCache( parent=None, graph=graph )
        #logger.debug("Setting block shape...")
        op.BlockShape.setValue( [100, 75, 50] )
        op.Input.connect( opData.Output )
        
        assert op.Output.ready()
        
        slicing = numpy.s_[ 0:100, 50:150, 75:150 ]
        expectedData = sampleData[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

        # Now change the blockshape and the input and try again...
        sampleDataWithChannel = sampleData.withAxes(*'xyzc')
        opData.Input.setValue( sampleDataWithChannel )
        op.BlockShape.setValue( [45, 33, 40, 1] )

        assert op.Output.ready()

        slicing = numpy.s_[ 60:70, 50:110, 60:120, 0:1 ]
        expectedData = sampleDataWithChannel[slicing].view(numpy.ndarray)
        
        #logger.debug("Requesting data...")
        readData = op.Output[slicing].wait()
        
        #logger.debug("Checking data...")    
        assert (readData == expectedData).all(), "Incorrect output!"

    def testReportGeneration(self):
        graph = Graph()
        sampleData = numpy.random.randint(0, 256, size=(50, 50, 50))
        sampleData = sampleData.astype(numpy.uint8)
        sampleData = vigra.taggedView(sampleData, axistags='xyz')
        
        opData = OpArrayPiper(graph=graph)
        opData.Input.setValue(sampleData)
        
        op = OpCompressedCache(parent=None, graph=graph)
        op.BlockShape.setValue((25, 25, 25))
        op.Input.connect(opData.Output)
        
        before = time.time()
        assert op.Output.ready()
        assert op.usedMemory() == 0.0,\
            "cache must not be filled at this point"
        op.Output[...].wait()
        assert op.usedMemory() > 0.0,\
            "cache must contain data at this point"
        after = time.time()

        r = MemInfoNode()
        op.generateReport(r)
        # not sure how good this can be compressed, but the cache
        # should hold memory by now
        assert r.usedMemory > 0
        # check sanity of last access time
        assert r.lastAccessTime >= before, str(r.lastAccessTime)
        assert r.lastAccessTime <= after, str(r.lastAccessTime)
        assert r.fractionOfUsedMemoryDirty == 0.0

        opData.Input.setDirty(
            (slice(0, 25), slice(0, 25), slice(0, 25)))
        assert op.fractionOfUsedMemoryDirty() < 1.0
        assert op.fractionOfUsedMemoryDirty() > 0

        opData.Input.setDirty(slice(None))
        assert op.fractionOfUsedMemoryDirty() == 1.0


if __name__ == "__main__":
    # Set up logging for debug
    logHandler = logging.StreamHandler( sys.stdout )
    logger.addHandler( logHandler )
    cacheLogger.addHandler( logHandler )

    logger.setLevel( logging.DEBUG )
    cacheLogger.setLevel( logging.DEBUG )

    # Run nose
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
