import threading
import numpy
import vigra
from lazyflow.graph import Graph
from lazyflow.roi import sliceToRoi, roiToSlice
from lazyflow.operators import OpArrayPiper, OpSubRegion

class KeyMaker():
    def __getitem__(self, *args):
        return list(*args)
make_key = KeyMaker()

class TestOpSubRegion(object):
    
    def testOutput(self):
        graph = Graph()
        data = numpy.random.random( (1,100,100,10,1) )
        opProvider = OpArrayPiper(graph=graph)
        opProvider.Input.setValue(data)
        
        opSubRegion = OpSubRegion( graph=graph )
        opSubRegion.Input.connect( opProvider.Output )
        
        opSubRegion.Start.setValue( (0,20,30,5,0) )
        opSubRegion.Stop.setValue( (1,30,50,8,1) )
        
        subData = opSubRegion.Output( start=( 0,5,10,1,0 ), stop=( 1,10,20,3,1 ) ).wait()
        assert (subData == data[0:1, 25:30, 40:50, 6:8, 0:1]).all()

    def testDirtyPropagation(self):
        graph = Graph()
        data = numpy.random.random( (1,100,100,10,1) )
        opProvider = OpArrayPiper(graph=graph)
        opProvider.Input.setValue(data)
        
        opSubRegion = OpSubRegion( graph=graph )
        opSubRegion.Input.connect( opProvider.Output )
        
        opSubRegion.Start.setValue( (0,20,30,5,0) )
        opSubRegion.Stop.setValue( (1,30,50,8,1) )
        
        gotDirtyRois = []
        def handleDirty(slot, roi):
            gotDirtyRois.append(roi)
        opSubRegion.Output.notifyDirty(handleDirty)

        # Set an input dirty region that overlaps with the subregion
        key = make_key[0:1, 15:35, 32:33, 0:10, 0:1 ]
        opProvider.Input.setDirty( key )

        assert len(gotDirtyRois) == 1
        assert gotDirtyRois[0].start == [0,0,2,0,0]
        assert gotDirtyRois[0].stop == [1,10,3,3,1]

        # Now mark a region that DOESN'T overlap with the subregion
        key = make_key[0:1, 70:80, 32:33, 0:10, 0:1 ]
        opProvider.Input.setDirty( key )

        # Should have gotten no extra dirty notifications
        assert len(gotDirtyRois) == 1


if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)











