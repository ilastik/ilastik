from lazyflow import graph
from lazyflow import stype
from lazyflow import operators
import numpy

class Test_GraphStateTag(object):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test(self):
        g = graph.Graph()
        op = operators.OpArrayPiper(graph=g)
        
        originalStateTag = g.stateTag
        gotReady = []
        def handleReady(slot):
            gotReady.append(True)
            print "stateTag", g.stateTag
            assert g.stateTag != originalStateTag
            print "calldepth:", g.callDepthCounter
            assert g.callDepthCounter > 0

        assert g.callDepthCounter == 0
        
        op.Output.notifyReady( handleReady )
        
        op.Input.setValue( "TEST" )

        assert g.callDepthCounter == 0

        assert gotReady[0]

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
