
import nose
from lazyflow import graph
from lazyflow import stype
from lazyflow import operators
import numpy

class OpA(graph.Operator):
    name = "OpA"

    Input1 = graph.InputSlot()                # required slot
    Input2 = graph.InputSlot(optional = True) # optional slot
    Input3 = graph.InputSlot(value = 3)       # required slot with default value, i.e. already connected
    Input4 = graph.MultiInputSlot(level = 1)       # required slot with default value, i.e. already connected

    Output1 = graph.OutputSlot()
    Output2 = graph.OutputSlot()
    Output3 = graph.OutputSlot()


    def __init__(self, *args, **kwargs):
        graph.Operator.__init__(self, *args, **kwargs)
        self._configured = False

    def setupOutputs(self):
        self._configured = True
        self.Output1.meta.shape = self.Input1.meta.shape
        self.Output1.meta.dtype = self.Input1.meta.dtype
        self.Output2.meta.shape = self.Input1.meta.shape
        self.Output2.meta.dtype = self.Input1.meta.dtype
        self.Output3.meta.shape = self.Input1.meta.shape
        self.Output3.meta.dtype = self.Input1.meta.dtype
        #print "OpInternal shape=%r, dtype=%r" % (self.Input1.meta.shape, self.Input1.meta.dtype)

    def execute(self, slot, subindex, roi, result):
        if slot == self.Output1:
            result[0] = self.Input1[:].allocate().wait()[0]
        elif slot == self.Output2:
            result[0] = self.Input2[:].allocate().wait()[0]
        elif slot == self.Output3:
            result[0] = self.Input3[:].allocate().wait()[0]
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        if inputSlot == self.Input1:
            self.Output1.setDirty(roi)
        if inputSlot == self.Input1:
            self.Output2.setDirty(roi)
        if inputSlot == self.Input3:
            self.Output3.setDirty(roi)
            
class TestOperator_setupOutputs(object):

    def setUp(self):
        self.g = graph.Graph()

    def tearDown(self):
        self.g.stopGraph()

    def test_disconnected_connected(self):
        # check that operator is not configuerd initiallia
        # since it has a slot without default value
        op = OpA(self.g)
        assert op._configured == False

        # check that operator is not configuerd initiallia
        op.Input1.setValue(1)
        assert op._configured == False

        # check that the operator is configued
        # after connecting the slot without default value
        op.Input1.setValue(1)
        op.Input4.setValues([1,2])
        assert op._configured == True
        op._configured = False

        # check that the operatir is reconfigured
        # when connecting the slot with default value
        # to another value
        op.Input3.setValue(2)
        assert op._configured == True


    def test_set_values(self):
        op = OpA(self.g)

        # check that Input4 is not connected
        assert op.Input4.connected() is False

        op.Input4.setValues([1])

        # check that the length of Input4 is 1
        assert len(op.Input4) == 1

        # check that Input4 is now connected and configured
        assert op.Input4.connected()
        assert op.Input4.configured()


        # check that the length of Input4 is 2
        op.Input4.setValues([1,2])
        assert len(op.Input4) == 2

        # check that the values of the subslots are correct
        assert op.Input4[0].value == 1
        assert op.Input4[1].value == 2

        #check that the normal setValue propagates to all subslots
        op.Input4.setValue(3)
        assert len(op.Input4) == 2
        assert op.Input4[0].value == 3
        assert op.Input4[1].value == 3

    def test_default_value(self):
        op = OpA(self.g)
        op.Input1.setValue(1)
        op.Input4.setValues([1])


        # check that the slot with default value
        # returns the correct value
        result = op.Output3[:].allocate().wait()[0]
        assert result == 3

        # check that the slot with default value
        # returns the new value when it is connected
        # to something else
        op.Input3.setValue(2)
        result = op.Output3[:].allocate().wait()[0]
        assert result == 2


    def test_connect_propagate(self):
        # check that connecting a required slot to an
        # already configured slots notifes the operator
        # of connecting
        op1 = OpA(self.g)
        op1.Input1.setValue(1)
        op1.Input4.setValues([1])
        op2 = OpA(self.g)
        op2.Input1.connect(op1.Output1)
        op2.Input4.setValues([1])
        assert op2._configured == True


    def test_deferred_connect_propagate(self):
        # check that connecting a required slot to an
        # not yet  configured slots notifes the operator
        # of connecting after configuring the first operator
        # in the chain
        op1 = OpA(self.g)
        op1.Input4.setValues([1])
        op2 = OpA(self.g)
        op2.Input1.connect(op1.Output1)
        op2.Input4.setValues([1])
        assert op2._configured == False
        op1.Input1.setValue(1)
        assert op2._configured == True

class TestOperator_meta(object):

    def setUp(self):
        self.g = graph.Graph()

    def tearDown(self):
        self.g.stopGraph()

    def test_meta_propagate(self):
        # check that connecting a required slot to an
        # already configured slots notifes the operator
        # of connecting and the meta information of
        # is correctly passed on between the slots
        op1 = OpA(self.g)
        op1.Input1.setValue(numpy.ndarray((10,)))
        op1.Input4.setValues([1])
        op2 = OpA(self.g)
        op2.Input1.connect(op1.Output1)
        op2.Input4.setValues([1])
        assert op2.Output1.meta.shape == (10,)


    def test_deferred_meta_propagate(self):
        # check that connecting a required slot to an
        # not yet  configured slots notifes the operator
        # of connecting after configuring the first operator
        # and propagates the meta information correctly
        # between the slots
        op1 = OpA(self.g)
        op2 = OpA(self.g)
        op1.Input4.setValues([1,2])
        op2.Input4.setValues([1,2])
        op2.Input1.connect(op1.Output1)
        op1.Input1.setValue(numpy.ndarray((10,)))
        assert op2.Output1.meta.shape == (10,)
        op1.Input1.setValue(numpy.ndarray((20,)))
        assert op2.Output1.meta.shape == (20,)

class OpWithMultiInputs(graph.Operator):
    Input = graph.MultiInputSlot()
    Output = graph.MultiOutputSlot()

    def setupOutputs(self):
        self.Output.resize(len(self.Input))

    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        index = subindex[0]
        if slot.name == "Output":
            result[...] = self.Input[index][key]

class TestMultiSlotResize(object):
    def setUp(self):
        self.g = graph.Graph()
        self.op1 = OpWithMultiInputs(graph=self.g)
        self.op2 = OpWithMultiInputs(graph=self.g)

        self.wrappedOp = OpA(graph=self.g)
        # Connect multi-inputs to the single inputs to induce wrapping
        self.wrappedOp.Input1.connect(self.op1.Input)
        self.wrappedOp.Input2.connect(self.op2.Input)

    def tearDown(self):
        self.g.stopGraph()

    def testResizeToSmaller(self):
        self.op1.Input.resize(5)
        self.op1.Input.resize(0)

class OpDirectConnection(graph.Operator):
    Input = graph.InputSlot()
    Output = graph.OutputSlot()
    
    def propagateDirty(self, inputSlot, subindex, roi):
        pass
    
    def setupOutputs(self):
        self.Output.connect( self.Input )

class TestSlotStates(object):

    def setup(self):
        self.g = graph.Graph()

    def teardown(self):
        pass
    
    def test_directlyConnectedOutputs(self):
        op = OpDirectConnection(graph=self.g)
        
        assert not op.Input.connected()
        assert not op.Output.connected()
        
        assert not op.Input.ready()
        assert not op.Output.ready()
        
        connectedSlots = { op.Input  : False,
                           op.Output : False }
        def handleConnect(slot):
            connectedSlots[slot] = True
        
        # Test notifyConnect
        op.Input.notifyConnect( handleConnect )
        op.Output.notifyConnect( handleConnect )
        
        readySlots = { op.Input  : False,
                       op.Output : False }
        def handleReady(slot):
            readySlots[slot] = True
        
        # Test notifyReady
        op.Input.notifyReady( handleReady )
        op.Output.notifyReady( handleReady )

        data = numpy.zeros((10,10,10,10,10))
        op.Input.setValue( data )
        
        assert op.Input.ready()
        assert op.Output.ready()
        
        assert op.Input.connected()
        assert op.Output.connected()
        
        assert connectedSlots[op.Input] == True
        assert connectedSlots[op.Output] == True

    def test_implicitlyConnectedOutputs(self):
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.OpArrayPiper(graph=self.g)
        
        assert not op.Input.connected()
        assert not op.Output.connected()
        
        assert not op.Input.ready()
        assert not op.Output.ready()
        
        connectedSlots = { op.Input  : False,
                           op.Output : False }
        def handleConnect(slot):
            connectedSlots[slot] = True
        
        # Test notifyConnect
        op.Input.notifyConnect( handleConnect )
        op.Output.notifyConnect( handleConnect )
        
        readySlots = { op.Input  : False,
                       op.Output : False }
        def handleReady(slot):
            readySlots[slot] = True
        
        # Test notifyReady
        op.Input.notifyReady( handleReady )
        op.Output.notifyReady( handleReady )

        data = numpy.zeros((10,10,10,10,10))
        op.Input.setValue( data )
        
        assert op.Input.ready()
        assert op.Output.ready()
                
        assert op.Input.connected()
        assert not op.Output.connected() # Not connected
        
        assert connectedSlots[op.Input] == True
        assert connectedSlots[op.Output] == False

        assert readySlots[op.Input] == True
        assert readySlots[op.Output] == True
        
    def test_implicitlyConnectedMultiOutputs(self):
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.Op5ToMulti(graph=self.g)
        
        assert not op.Input0.connected()
        assert not op.Outputs.connected()
        
        assert not op.Input0.ready()
        assert not op.Outputs.ready()
        
        connectedSlots = set()
        def handleConnect(slot):
            connectedSlots.add(slot)
        
        # Test notifyConnect
        op.Input0.notifyConnect( handleConnect )
        op.Outputs.notifyConnect( handleConnect )
        
        readySlots = set()
        def handleReady(slot):
            readySlots.add(slot)
        
        # Test notifyReady
        op.Input0.notifyReady( handleReady )
        op.Outputs.notifyReady( handleReady )

        def subscribeToReady(slot, index, *args):
            slot[index].notifyReady(handleReady)
        op.Outputs.notifyInserted( subscribeToReady )

        data = numpy.zeros((10,10,10,10,10))
        op.Input0.setValue( data )
        
        assert op.Input0.ready()
        assert op.Outputs.ready()
                
        assert op.Input0.connected()
        assert not op.Outputs.connected() # Not connected
        
        assert op.Input0 in connectedSlots
        assert op.Outputs not in connectedSlots # Not connected
        assert op.Outputs[0] not in connectedSlots

        assert op.Input0 in readySlots
        assert op.Outputs in readySlots
        assert op.Outputs[0] in readySlots
        
    def test_clonedSlotState(self):
        """
        Create a graph that involves "cloned" inputs and outputs,
        and verify that their states are changed correctly at the correct times, with callbacks.
        """
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.OpArrayPiper(graph=self.g)
        
        # op2 gets his input as a clone from op.Input
        op2 = operators.OpArrayPiper(graph=self.g)
        op2.Input.connect( op.Input )
        
        # op3 gets his input as a clone from op.Output
        op3 = operators.OpArrayPiper(graph=self.g)
        op3.Input.connect( op.Output )
        
        assert not op.Input.connected()
        assert not op.Output.connected()
        
        assert not op.Input.ready()
        assert not op.Output.ready()
        assert not op2.Input.ready()
        assert not op2.Output.ready()
        assert not op3.Input.ready()
        assert not op3.Output.ready()
        
        connectedSlots = { op.Input  : False,
                           op.Output : False }
        def handleConnect(slot):
            connectedSlots[slot] = True
        
        # Test notifyConnect
        op.Input.notifyConnect( handleConnect )
        op.Output.notifyConnect( handleConnect )
        
        readySlots = { op.Input  : False,
                       op.Output : False }
        def handleReady(slot):
            readySlots[slot] = True
        
        # Test notifyReady
        op.Input.notifyReady( handleReady )
        op.Output.notifyReady( handleReady )
        op2.Input.notifyReady( handleReady )
        op2.Output.notifyReady( handleReady )
        op3.Input.notifyReady( handleReady )
        op3.Output.notifyReady( handleReady )

        # This should trigger setupOutputs and everything to become ready
        data = numpy.zeros((10,10,10,10,10))
        op.Input.setValue( data )
        
        assert op.Input.ready()
        assert op.Output.ready()
        assert op2.Input.ready()
        assert op2.Output.ready()
        assert op3.Input.ready()
        assert op3.Output.ready()

        assert op.Input.connected()
        assert not op.Output.connected() # Not connected
        
        assert connectedSlots[op.Input] == True
        assert connectedSlots[op.Output] == False
        
        assert readySlots[op.Input] == True
        assert readySlots[op.Output] == True
        assert readySlots[op2.Input] == True
        assert readySlots[op2.Output] == True
        assert readySlots[op3.Input] == True
        assert readySlots[op3.Output] == True
        
    def test_unready_propagation(self):
        # The array piper copies its input to its output, creating an "implicit" connection
        op = operators.OpArrayPiper(graph=self.g)
        op.name = 'op'
        
        # op2 gets his input as a clone from op.Input
        op2 = operators.OpArrayPiper(graph=self.g)
        op2.Input.connect( op.Input )
        op2.name = 'op2'
        
        # op3 gets his input as a clone from op.Output
        op3 = operators.OpArrayPiper(graph=self.g)
        op3.Input.connect( op.Output )
        op3.name = 'op3'

        # This should trigger setupOutputs and everything to become ready
        data = numpy.zeros((10,10,10,10,10))
        op.Input.setValue( data )
        
        assert op.Input.ready()
        assert op.Output.ready()
        assert op2.Input.ready()
        assert op2.Output.ready()
        assert op3.Input.ready()
        assert op3.Output.ready()

        assert op.Input.connected()
        assert not op.Output.connected() # Not connected

        # Disonnecting the head of the chain should cause everything to become unready
        op.Input.disconnect()
        
        assert not op.Input.ready()
        assert not op.Output.ready()
        assert not op2.Input.ready()
        assert not op2.Output.ready()
        assert not op3.Input.ready()
        assert not op3.Output.ready()
        
    def test_slicing(self):
        op = operators.OpArrayPiper(graph=self.g)
        
        a = numpy.zeros( 5*(10,), dtype=int )
        op.Input.setValue( a )
        
        b = op.Output[:, :, :].wait()
        assert b.shape == a.shape

if __name__ == "__main__":
    import nose
    nose.run( defaultTest=__file__, env={'NOSE_NOCAPTURE' : 1} )

#    test = TestSlotStates()
#    test.setup()    
#    test.test_implicitlyConnectedMultiOutputs()

#    test = TestOperator_setupOutputs()
#    test.setUp()
#    test.test_disconnected_connected()    
    




