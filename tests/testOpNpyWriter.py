import os
import tempfile
import shutil

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader, OpNpyWriter

class TestOpNpyWriter(object):
    
    @classmethod
    def setupClass(cls):
        cls._tmpdir = tempfile.mkdtemp()

    @classmethod
    def teardownClass(cls):
        shutil.rmtree(cls._tmpdir) 
    
    def testBasic(self):
        data = numpy.random.random( (100,100) ).astype( numpy.float32 )
        data = vigra.taggedView( data, vigra.defaultAxistags('xy') )
        
        graph = Graph()
        opWriter = OpNpyWriter(graph=graph)
        opWriter.Input.setValue(data)
        opWriter.Filepath.setValue( self._tmpdir + '/npy_writer_test_output.npy' )

        # Write it...
        opWriter.write()
        
        opRead = OpInputDataReader( graph=graph )
        opRead.FilePath.setValue( opWriter.Filepath.value )
        expected_data = data.view(numpy.ndarray)
        read_data = opRead.Output[:].wait()
        assert (read_data == expected_data).all(), "Read data didn't match exported data!"

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)

