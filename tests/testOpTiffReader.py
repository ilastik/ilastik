import tempfile
import shutil
import contextlib

import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpTiffReader

@contextlib.contextmanager
def tempdir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

class TestOpTiffReader(object):
    
    def test_2d(self):
        data = numpy.random.randint(0, 255, (100,200,3)).astype(numpy.uint8)
        with tempdir() as d:
            tiff_path = d + '/test-2d.tiff'
            vigra.impex.writeImage(vigra.taggedView(data, "yxc"), tiff_path, dtype='NATIVE', mode='w')
             
            op = OpTiffReader(graph=Graph())
            op.Filepath.setValue( tiff_path )
            assert op.Output.ready()
            assert (op.Output[50:100, 50:150].wait() == data[50:100, 50:150]).all()
 
    def test_3d(self):
        data = numpy.random.randint(0, 255, (50,100,200,3)).astype(numpy.uint8)
        with tempdir() as d:
            tiff_path = d + '/test-3d.tiff'
            for z_slice in data:
                vigra.impex.writeImage(vigra.taggedView(z_slice, "yxc"), tiff_path, dtype='NATIVE', mode='a')
 
            op = OpTiffReader(graph=Graph())
            op.Filepath.setValue( tiff_path )
            assert op.Output.ready()
            assert (op.Output[20:30, 50:100, 50:150].wait() == data[20:30, 50:100, 50:150]).all()            
 
    def test_3d_with_compression(self):
        """
        This tests that we can read a compressed (LZW) TIFF file.
        
        Note: It would be nice to test JPEG compression here, but strangely when vigra
        writes a JPEG-compressed TIFF, it is somehow messed up.  The image has two image
        'series' in it, so the thing seems to have twice as many planes as it should.
        Furthermore, vigra doesn't seem to read it back correctly, or maybe I'm missing something...
        """
        data = numpy.random.randint(0, 255, (50,100,200,3)).astype(numpy.uint8)
        with tempdir() as d:
            tiff_path = d + '/test-3d.tiff'
            for z_slice in data:
                vigra.impex.writeImage(vigra.taggedView(z_slice, "yxc"), tiff_path, dtype='NATIVE', compression='LZW', mode='a')
 
            op = OpTiffReader(graph=Graph())
            op.Filepath.setValue( tiff_path )
            assert op.Output.ready()
            assert (op.Output[20:30, 50:100, 50:150].wait() == data[20:30, 50:100, 50:150]).all()

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
