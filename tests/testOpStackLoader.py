import os
import sys
import shutil
import tempfile

import numpy
import vigra

from lazyflow.utility import PathComponents
from lazyflow.graph import Graph
from lazyflow.operators.ioOperators import OpInputDataReader, OpStackLoader
from lazyflow.operators.opReorderAxes import OpReorderAxes

class TestOpStackLoader(object):
    
    # TODO: Test with multiple channels.
    
    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self._tmp_dir)
    
    def _prepare_data_zyx(self):
        file_base = self._tmp_dir + "/rand_3d"
        
        X,Y = (100,100)
        Z = 10
        rand_data_3d = numpy.random.random((Z, Y, X))
        rand_data_3d *= 256
        rand_data_3d = rand_data_3d.astype(numpy.uint8)
        rand_data_3d = vigra.taggedView( rand_data_3d, 'zyx' )
        
        for z in range(Z):
            file_name = file_base + "_z{}.tiff".format(z)
            vigra.impex.writeImage( rand_data_3d[z,:,:], file_name )
        
        return ( rand_data_3d, file_base + "*.tiff" )
        
    def test_xyz(self):
        expected_volume_zyx, globstring = self._prepare_data_zyx()
        
        graph = Graph()
        op = OpStackLoader( graph=graph )
        op.globstring.setValue( globstring )
        
        assert len(op.stack.meta.axistags) == 4
        assert op.stack.meta.getAxisKeys() == list('xyzc')
        assert op.stack.meta.dtype == expected_volume_zyx.dtype
        
        vol_from_stack_xyzc = op.stack[:].wait()
        vol_from_stack_xyzc = vigra.taggedView( vol_from_stack_xyzc, 'xyzc' )
        vol_from_stack_zyx = vol_from_stack_xyzc.withAxes( *'zyx' )
        
        assert ( vol_from_stack_zyx == expected_volume_zyx ).all(), "3D Volume from stack did not match expected data."

    def _prepare_data_tzyx(self):
        file_base = self._tmp_dir + "/rand_4d"
        
        X,Y = (100,100)
        Z = 10
        T = 5
        rand_data_4d = numpy.random.random((T, Z, Y, X))
        rand_data_4d *= 256
        rand_data_4d = rand_data_4d.astype(numpy.uint8)
        rand_data_4d = vigra.taggedView( rand_data_4d, 'tzyx' )

        for t in range(T):        
            file_name = file_base + "_t{}.tiff".format(t)
            for z in range(Z):
                vigra.impex.writeImage( rand_data_4d[t, z,:,:], file_name, mode='a' )
        
        return ( rand_data_4d, file_base + "*.tiff" )

    def test_txyz(self):
        expected_volume_tzyx, globstring = self._prepare_data_tzyx()
        
        graph = Graph()
        op = OpStackLoader( graph=graph )
        op.globstring.setValue( globstring )
        
        assert len(op.stack.meta.axistags) == 5
        assert op.stack.meta.getAxisKeys() == list('txyzc')
        assert op.stack.meta.dtype == expected_volume_tzyx.dtype
        
        vol_from_stack_txyzc = op.stack[:].wait()
        vol_from_stack_txyzc = vigra.taggedView( vol_from_stack_txyzc, 'txyzc' )
        vol_from_stack_tzyx = vol_from_stack_txyzc.withAxes( *'tzyx' )
        
        assert ( vol_from_stack_tzyx == expected_volume_tzyx ).all(), "4D Volume from stack did not match expected data."
        

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
        
            