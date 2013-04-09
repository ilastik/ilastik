import lazyflow
from lazyflow.operators import OpTransposeSlots

class TestOpTransposeSlots(object):
    
    def test(self):
        g = lazyflow.graph.Graph()
        op = OpTransposeSlots( graph=g )
        
        counter = 0
        
        op.Inputs.resize( 5 )
        for i, mslot in enumerate(op.Inputs):
            mslot.resize( 4 )
            for j, islot in enumerate(mslot):
                islot.setValue( counter )
                counter += 1
        
        for i in range(5):
            for j in range(4):
                assert op.Outputs[j][i].value == op.Inputs[i][j].value
        
        # Now let's see what happens when we insert some slots after the fact...
        op.Inputs.insertSlot( 3, 6 )
        op.Inputs.insertSlot( 3, 7 )
        for i, mslot in enumerate(op.Inputs):
            mslot.resize( 4 )
            for j, islot in enumerate(mslot):
                islot.setValue( counter )
                counter += 1
        
        for i in range(7):
            for j in range(4):
                assert op.Outputs[j][i].value == op.Inputs[i][j].value


if __name__ == "__main__":
    import nose
    ret = nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
    if not ret: sys.exit(1)
