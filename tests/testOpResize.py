from __future__ import division
from builtins import zip
from builtins import object
from past.utils import old_div
import numpy
import vigra

from lazyflow.graph import Graph
from lazyflow.operators import OpResize

class TestOpResize(object):
    
    def testBasic(self):
        graph = Graph()
        op = OpResize( graph=graph )
        
        data = numpy.zeros( (128, 256), dtype=numpy.float32 )
        data[32, 96] = 0.5
        data[48, 48] = 1.0
        data = vigra.filters.gaussianSmoothing(data, sigma=5.0)
        data *= old_div(1.0,data.max())
        data = vigra.taggedView( data, 'xy' )

        op.Input.setValue( data )
        op.ResizedShape.setValue( (64, 128) )
        resized_data = op.Output[:].wait()

        #print data.mean(), resized_data.mean()
        assert abs( 1.0 - old_div(data.mean(),resized_data.mean()) ) < 0.03
        
        # Suppress rounding noise
        resized_data = numpy.where( resized_data > 0.1, resized_data, 0.0 )        

        # Find the max points in the resized image
        local_max = vigra.analysis.extendedLocalMaxima(resized_data)
        max_coords = list(zip ( *numpy.nonzero(local_max) ))

        # Did our two high points remain?
        assert (16, 48) in max_coords
        assert (24, 24) in max_coords

    def testPropagateDirty(self):
        graph = Graph()
        op = OpResize( graph=graph )
        
        data = numpy.zeros( (128, 128), dtype=numpy.float32 )
        data = vigra.taggedView( data, 'xy' )
        
        op.Input.setValue( data )
        op.ResizedShape.setValue( (64, 64) )
        
        dirty_roi = [None]
        def handle_dirty(slot, roi):
            dirty_roi[0] = roi
        op.Output.notifyDirty( handle_dirty )

        # Note rounding behavior: start rounds down, stop rounds up.        
        op.Input.setDirty( (10,5), (20, 21) )
        assert tuple(dirty_roi[0].start) == (5,2)
        assert tuple(dirty_roi[0].stop) == (10,11)

    def testFastPath(self):
        graph = Graph()
        op = OpResize( graph=graph )

        # If the output size is identical to the input size, then no resizing is necessary.
        # Even random data should be exactly identical (no interpolation)...        
        data = numpy.random.random( (128, 128) ).astype( numpy.float32 )
        data = vigra.taggedView( data, 'xy' )

        op.Input.setValue( data )
        op.ResizedShape.setValue( (128, 128) )
        resized_data = op.Output[:].wait()
        resized_data = vigra.taggedView( resized_data, 'xy' )
        assert (resized_data == data).all(), "data was interpolated unnecessarily"


    def testUint8(self):
        graph = Graph()
        op = OpResize( graph=graph )
        
        data = numpy.zeros( (128, 128), dtype=numpy.float32 )
        data[32, 96] = 0.5
        data[48, 48] = 1.0
        data = vigra.filters.gaussianSmoothing(data, sigma=5.0)
        data *= old_div(1.0,data.max())
        data *= 255
        data = vigra.taggedView( data, 'xy' ).astype( numpy.uint8 )

        op.Input.setValue( data )
        op.ResizedShape.setValue( (64, 64) )
        resized_data = op.Output[:].wait()

        #print data.mean(), resized_data.mean()

        # Must tolerate a larger error due to dtype conversion...
        # The tolerance here is somewhat arbitrary.
        assert abs( 1.0 - old_div(data.mean(),resized_data.mean()) ) < 1.0

    def test5D(self):
        graph = Graph()
        op = OpResize( graph=graph )
        
        data = numpy.zeros( (5, 32, 128, 128, 3), dtype=numpy.float32 )
        data[0, 0, 32, 96, 1] = 0.5
        data[1, 16, 48, 48, 2] = 1.0
        data = vigra.taggedView( data, 'tyzxc' ) # deliberately strange order...
        data[0] = vigra.filters.gaussianSmoothing(data[0], sigma=5.0)
        data[1] = vigra.filters.gaussianSmoothing(data[1], sigma=5.0)
        data *= old_div(1.0,data.max())

        op.Input.setValue( data )
        op.ResizedShape.setValue( (5, 32, 128, 64, 3) )
        resized_data = op.Output[:].wait()

        #print data.mean(), resized_data.mean()
        #assert abs( 1.0 - data.mean()/resized_data.mean() ) < 0.03
        
        # Suppress rounding noise
        resized_data = numpy.where( resized_data > 0.1, resized_data, 0.0 )

        # Did our two high points remain?
        assert abs(resized_data[0, 0, 32, 48, 1] - 0.5) < 0.1
        assert abs(resized_data[1, 16, 48, 24, 2] - 1.0) < 0.1


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
