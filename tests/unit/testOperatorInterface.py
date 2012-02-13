
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

  Output1 = graph.OutputSlot()
  Output2 = graph.OutputSlot()
  Output3 = graph.OutputSlot()


  def __init__(self, parent):
    graph.Operator.__init__(self,parent)
    self.configured = False

  def setupOutputs(self):
    self.configured = True
    self.Output1.meta.shape = self.Input1.meta.shape
    self.Output1.meta.dtype = self.Input1.meta.dtype
    self.Output2.meta.shape = self.Input1.meta.shape
    self.Output2.meta.dtype = self.Input1.meta.dtype
    self.Output3.meta.shape = self.Input1.meta.shape
    self.Output3.meta.dtype = self.Input1.meta.dtype
    print "OpInternal shape=%r, dtype=%r" % (self.Input1.meta.shape, self.Input1.meta.dtype)

  def execute(self, slot, roi, result):
    if slot == self.Output1:
      result[0] = self.Input1[:].allocate().wait()[0]
    elif slot == self.Output2:
      result[0] = self.Input2[:].allocate().wait()[0]
    elif slot == self.Output3:
      result[0] = self.Input3[:].allocate().wait()[0]
    return result




class TestOperator_setupOutputs(object):

  def setUp(self):
    self.g = graph.Graph()

  def tearDown(self):
    self.g.stopGraph()

  def test_disconnected_connected(self):
    # check that operator is not configuerd initiallia
    # since it has a slot without default value 
    op = OpA(self.g)
    assert op.configured == False

    # check that the operator is configued
    # after connecting the slot without default value
    op.Input1.setValue(1)
    assert op.configured == True
    op.configured = False
    
    # check that the operatir is reconfigured
    # when connecting the slot with default value
    # to another value
    op.Input3.setValue(2)
    assert op.configured == True



  def test_default_value(self):
    op = OpA(self.g)
    op.Input1.setValue(1)


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
    op2 = OpA(self.g)
    op2.Input1.connect(op1.Output1)
    assert op2.configured == True


  def test_deferred_connect_propagate(self):
    # check that connecting a required slot to an
    # not yet  configured slots notifes the operator
    # of connecting after configuring the first operator
    # in the chain
    op1 = OpA(self.g)
    op2 = OpA(self.g)
    op2.Input1.connect(op1.Output1)
    assert op2.configured == False
    op1.Input1.setValue(1)
    assert op2.configured == True
  


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
    op2 = OpA(self.g)
    op2.Input1.connect(op1.Output1)
    assert op2.Output1.meta.shape == (10,)


  def test_deferred_meta_propagate(self):
    # check that connecting a required slot to an
    # not yet  configured slots notifes the operator
    # of connecting after configuring the first operator
    # and propagates the meta information correctly
    # between the slots
    op1 = OpA(self.g)
    op2 = OpA(self.g)
    op2.Input1.connect(op1.Output1)
    op1.Input1.setValue(numpy.ndarray((10,)))
    assert op2.Output1.meta.shape == (10,)
    op1.Input1.setValue(numpy.ndarray((20,)))
    assert op2.Output1.meta.shape == (20,)
