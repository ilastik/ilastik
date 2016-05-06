import tempfile
import shutil
import numpy as np
import nose
from lazyflow.graph import Graph
 
try:
    import pyklb
    _klb_available = True
except ImportError:
    _klb_available = False
 
from lazyflow.operators.ioOperators import OpKlbReader

    
def test_pyklb():
    """
    This merely tests pyklb itself, but it seems to segfault!
    """
    raise nose.SkipTest
    
    import numpy as np
    import pyklb
    # Create some simple data. Should compress well.
    shape = (1,1,30,40,50)
    data_tczyx = np.indices( shape ).sum(0).astype( np.uint8 )
    assert data_tczyx.shape == shape
    
    # Write the data as KLB
    print "writing..."
    filepath = '/tmp/test_data.klb'    
    pyklb.writefull( data_tczyx, filepath, blocksize_xyzct=np.array([1,1,10,10,10], dtype=np.uint32) )
    
    # Read it back.  This segfaults.
    print "reading..."
    readback = pyklb.readfull(filepath)
    
    # This also segfaults.
    #readback = pyklb.readroi(filepath, (0,0,0,0,0), np.array(shape)-1)
    
    assert (readback == data_tczyx).all()
    print "Done."


class TestOpKlbReader( object ):
     
    def setup(self):
        # For now, we always skip this test because of the above-mentioned segfault in pyklb.
        raise nose.SkipTest
        
        if not _klb_available:
            raise nose.SkipTest
     
    def testBasic(self):
        tmpdir = tempfile.mkdtemp()        
        try:
            filepath = tmpdir + '/random_data.klb'
            shape = (1,1,30,40,50)
            data_tczyx = np.indices( shape ).sum(0).astype( np.uint8 )
            pyklb.writefull( data_tczyx, filepath, blocksize_xyzct=np.array([1,1,10,10,10], dtype=np.uint32) )
            readback = pyklb.readroi(filepath, (0,0,0,0,0), np.array(shape)-1)
                          
            op = OpKlbReader( graph=Graph() )
            op.FilePath.setValue( filepath )
             
            assert op.Output.meta.shape == shape
            assert op.Output.meta.dtype == np.uint8
             
            read_data = op.Output[:].wait()
            assert ( read_data == data_tczyx ).all()
             
        finally:
            shutil.rmtree(tmpdir)
     
if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret: sys.exit(1)
