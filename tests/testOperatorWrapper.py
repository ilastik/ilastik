from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot, OperatorWrapper
from lazyflow.operators import Op5ToMulti, OpArrayPiper
import numpy

class OpSimple(Operator):
    InputA = InputSlot()
    InputB = InputSlot()

class TestMultiOutputToWrapped(object):

    def setUp(self):
        self.graph = Graph()
        self.simple = OpSimple(graph=self.graph)
        self.opMultiA = Op5ToMulti(graph=self.graph)
        self.opMultiB = Op5ToMulti(graph=self.graph)
        
        # Connect the multi-output to the simple operator,
        #  which causes it to be wrapped
        self.simple.InputA.connect( self.opMultiA.Outputs )
        self.simple.InputB.connect( self.opMultiB.Outputs )

        # Give an input
        self.opMultiA.Input0.setValue(numpy.zeros((10,10)))
        self.opMultiB.Input0.setValue(numpy.zeros((10,10)))        

    def tearDown(self):
        self.graph.stopGraph()
        
    def test_all_slots_have_operators(self):
        # Get the wrapper object
        wrapper = list(self.opMultiA.Outputs.partners)[0].operator
        assert type(wrapper) == OperatorWrapper
        
        assert len(wrapper.innerOperators) == 1
        assert type(wrapper.innerOperators[0]) == OpSimple
        assert type(wrapper.innerOperators[0].InputA) == InputSlot
        assert wrapper.innerOperators[0].InputA.partner is not None
        assert type(wrapper.innerOperators[0].InputA.partner) == InputSlot
        assert type(wrapper.innerOperators[0].InputA.partner.operator) == MultiInputSlot
        assert type(wrapper.innerOperators[0].InputA.partner.operator.partner) == MultiOutputSlot
        assert wrapper.innerOperators[0].InputA.partner.operator.partner.name == 'Outputs'

        assert len(wrapper.innerOperators) == 1
        assert type(wrapper.innerOperators[0]) == OpSimple
        assert type(wrapper.innerOperators[0].InputB) == InputSlot
        assert wrapper.innerOperators[0].InputB.partner is not None
        assert type(wrapper.innerOperators[0].InputB.partner) == InputSlot
        assert type(wrapper.innerOperators[0].InputB.partner.operator) == MultiInputSlot
        assert type(wrapper.innerOperators[0].InputB.partner.operator.partner) == MultiOutputSlot
        assert wrapper.innerOperators[0].InputB.partner.operator.partner.name == 'Outputs'

if __name__ == "__main__":
    test = TestMultiOutputToWrapped()
    test.setUp()
    test.test_all_slots_have_operators()
    test.tearDown()

