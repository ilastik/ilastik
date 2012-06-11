from lazyflow.graph import Graph, Operator, InputSlot, OutputSlot, MultiInputSlot, MultiOutputSlot, OperatorWrapper
from lazyflow.operators import Op5ToMulti, OpArrayPiper
import numpy

class OpSimple(Operator):
    InputA = InputSlot()
    InputB = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.meta.shape = self.InputA.meta.shape
        self.Output.meta.dtype = self.InputA.meta.dtype

    def execute(self, slot, roi, result):
        assert slot == self.Output

        result[...] = self.InputA(roi.start, roi.stop).wait() * self.InputB[0:1].wait()

class OpExplicitMulti(Operator):
    Output = MultiOutputSlot()

class OpCopyInput(Operator):
    Input = InputSlot()
    Output = OutputSlot()

    def setupOutputs(self):
        self.Output.setValue(self.Input.value)



class TestBasic(object):

    @classmethod
    def setupClass(cls):
        cls.graph = Graph()

    @classmethod
    def teardownClass(cls):
        pass

    def test_fullWrapping(self):
        """
        Test basic wrapping functionality (all slots are promoted)
        """
        orig = OpSimple(graph=self.graph)
        wrapped = OperatorWrapper( orig )
        assert type(wrapped.InputA) == MultiInputSlot
        assert type(wrapped.InputB) == MultiInputSlot
        assert type(wrapped.Output) == MultiOutputSlot

        assert len(wrapped.InputA) == 0
        assert len(wrapped.InputB) == 0
        assert len(wrapped.Output) == 0

        wrapped.InputA.resize(2)
        assert len(wrapped.InputB) == 2
        assert len(wrapped.Output) == 2

        a = numpy.array([[1,2],[3,4]])
        b = numpy.array([2])
        wrapped.InputA[0].setValue(a)
        wrapped.InputB[0].setValue(b)
        wrapped.InputA[1].setValue(2*a)
        wrapped.InputB[1].setValue(3*b)

        result0 = wrapped.Output[0][0:2,0:2].wait()
        result1 = wrapped.Output[1][0:2,0:2].wait()
        assert ( result0 == a * b[0] ).all()
        assert ( result1 == 2*a * 3*b[0] ).all()

    def test_partialWrapping(self):
        """
        By default, OperatorWrapper promotes all slots.
        This function tests what happens when only a subset of the inputs are promoted.
        """
        orig = OpSimple(graph=self.graph)
        wrapped = OperatorWrapper( orig, promotedSlotNames=set(['InputA']) )
        assert type(wrapped.InputA) == MultiInputSlot  # Promoted because it was listed in the constructor call
        assert type(wrapped.InputB) == InputSlot       # NOT promoted
        assert type(wrapped.Output) == MultiOutputSlot # Promoted because it's an output

        assert len(wrapped.InputA) == 0
        assert len(wrapped.InputB) == 0
        assert len(wrapped.Output) == 0

        wrapped.InputA.resize(2)
        assert len(wrapped.InputB) == 0 # Not promoted
        assert len(wrapped.Output) == 2

        a = numpy.array([[1,2],[3,4]])
        b = numpy.array([2])
        wrapped.InputA[0].setValue(a)
        wrapped.InputB.setValue(b)
        wrapped.InputA[1].setValue(2*a)

        result0 = wrapped.Output[0][0:2,0:2].wait()
        result1 = wrapped.Output[1][0:2,0:2].wait()
        assert ( result0 == a * b[0] ).all()
        assert ( result1 == 2*a * b[0] ).all()

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

class TestMultiOutputToWrapped(object):

    @classmethod
    def setupClass(cls):
        cls.graph = Graph()

    @classmethod
    def teardownClass(cls):
        cls.graph.stopGraph()

    def test_input_output_resize(self):
        simple = OpSimple(graph=self.graph)
        exMulti = OpExplicitMulti(graph=self.graph)

        wrappedSimple = OperatorWrapper( simple )
        assert len(wrappedSimple.InputA) == 0

        wrappedSimple.InputA.connect( exMulti.Output )
        assert len(wrappedSimple.InputA) == 0

        exMulti.Output.resize( 1 )
        assert len(wrappedSimple.InputA) == 1
        assert len(wrappedSimple.InputB) == 1
        assert len(wrappedSimple.Output) == 1

    def test_setValues(self):
        opCopier = OpCopyInput(graph=self.graph)

        wrappedCopier = OperatorWrapper( opCopier )

        values = ["Subslot One", "Subslot Two"]
        wrappedCopier.Input.setValues( values )

        assert wrappedCopier.Output[0].value == values[0]
        assert wrappedCopier.Output[1].value == values[1]

if __name__ == "__main__":
    import nose
    nose.run(defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1})
