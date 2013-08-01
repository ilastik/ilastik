import os
import glob
import shutil
import tempfile

import numpy
import vigra
import h5py

import lazyflow.graph
from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.operators import OpArrayCache
from lazyflow.operators.ioOperators import OpExportMultipageTiffSequence, OpStackLoader

import sys
import logging
logger = logging.getLogger('tests.testOpExportMultipageTiffSequence')

class TestOpExportMultipageTiffSequence(object):

    def setUp(self):
        self.graph = lazyflow.graph.Graph()
        self._tmpdir = tempfile.mkdtemp()
        self._name_pattern = 'test_stack_slice_{slice_index}.tiff'
        self._stack_filepattern = os.path.join( self._tmpdir, self._name_pattern )

        # Generate some test data
        self.dataShape = (5, 10, 64, 128, 2)
        self._axisorder = 'tzyxc'
        self.testData = vigra.VigraArray( self.dataShape,
                                         axistags=vigra.defaultAxistags(self._axisorder),
                                         order='C' ).astype(numpy.uint8)
        self.testData[...] = numpy.indices(self.dataShape).sum(0)

    def tearDown(self):
        # Clean up
        shutil.rmtree(self._tmpdir)
        
    def test_Writer(self):
        opData = OpArrayCache( graph=self.graph )
        opData.blockShape.setValue( self.testData.shape )
        opData.Input.setValue( self.testData )
        
        opExport = OpExportMultipageTiffSequence(graph=self.graph)
        opExport.FilepathPattern.setValue( self._stack_filepattern )
        opExport.Input.connect( opData.Output )
        opExport.SliceIndexOffset.setValue(22)

        # Run the export
        opExport.run_export()

        globstring = self._stack_filepattern.format( slice_index=999 )
        globstring = globstring.replace('999', '*')

        opReader = OpStackLoader( graph=self.graph )
        opReader.globstring.setValue( globstring )

        # (The OpStackLoader produces txyzc order.)
        opReorderAxes = OpReorderAxes( graph=self.graph )
        opReorderAxes.AxisOrder.setValue( self._axisorder )
        opReorderAxes.Input.connect( opReader.stack )
        
        readData = opReorderAxes.Output[:].wait()
        logger.debug("Expected shape={}".format( self.testData.shape ) )
        logger.debug("Read shape={}".format( readData.shape ) )
        
        assert opReorderAxes.Output.meta.shape == self.testData.shape, "Exported files were of the wrong shape or number."
        assert (opReorderAxes.Output[:].wait() == self.testData.view( numpy.ndarray )).all(), "Exported data was not correct"

if __name__ == "__main__":
    # Run this file independently to see debug output.
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    ioOpLogger = logging.getLogger('lazyflow.operators.ioOperators')
    ioOpLogger.addHandler( logging.StreamHandler(sys.stdout) )
    ioOpLogger.setLevel(logging.DEBUG)

    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
