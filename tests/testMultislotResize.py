from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, OperatorWrapper
from lazyflow.operators import OpPixelOperator, OpTransposeSlots


class OpA(Operator):
    
    Inputs = InputSlot(level=2, optional=True)
    Outputs = OutputSlot(level=2)
    
    def setupOutputs(self):
        self.Outputs.resize( len(self.Inputs) )
        for imslot, omslot in zip(self.Inputs, self.Outputs):
            omslot.resize( len(imslot) )
            for islot, oslot in zip(imslot, omslot):
                oslot.meta.assignFrom( islot.meta )
    
    def execute(self, slot, subindex, roi, result):
        result[:] = self.Inputs[subindex](roi)
                
    def propagateDirty(self, slot, subindex, roi):
        self.Outputs[subindex].setDirty(roi)



class TestMultiSlotResize(object):
    
    def testMulitSlotResize(self):
        graph = Graph()
        opA = OpA(graph=graph)
        opB = OpA(graph=graph)
        opC = OpA(graph=graph)
        
        opP = OperatorWrapper(OpPixelOperator, graph=graph)

        opB.Inputs.connect( opA.Inputs )
        opC.Inputs.connect( opB.Inputs )
        
        opT = OpTransposeSlots(graph=graph)
        opT.Inputs.connect( opA.Outputs )
        opT.OutputLength.setValue( 2 )

        assert len(opT.Outputs) == 2

        opA.Inputs.resize(3)
        assert len(opT.Outputs[0]) == 3
        assert len(opT.Outputs[1]) == 3

        opP.Input.connect( opT.Outputs[0] )
        assert len(opP.Input) == 3
        
    def testMultiSlotPartners(self):
        graph = Graph()
        opA = OpA(graph=graph)
        opB = OpA(graph=graph)
        
        opB.Inputs.connect( opA.Inputs )
        opA.Inputs.resize(2)
        assert len(opB.Inputs) == 2
        assert opB.Inputs[0].partner == opA.Inputs[0]
        assert opB.Inputs[1].partner == opA.Inputs[1]
                

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
