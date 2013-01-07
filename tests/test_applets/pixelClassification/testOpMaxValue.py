from lazyflow.graph import Graph
from ilastik.applets.pixelClassification.opPixelClassification import OpMaxValue

class TestOpMaxValue(object):
    def test(self):
    
        op = OpMaxValue(graph=Graph())

        op.Inputs.setValues([0,1,2,3,4])
        assert op.Output.value == 4
    
        got_dirty = [False]
        def handleDirty(slot, roi):
            got_dirty[0] = True
        op.Output.notifyDirty(handleDirty)
    
        # Not dirty yet because max is still the same
        op.Inputs[1].setValue(4)
        assert not got_dirty[0]
    
        # Max has changed.  Check dirty.    
        op.Inputs[0].setValue(5)
        assert got_dirty[0]
        assert op.Output.value == 5

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
