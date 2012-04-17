import nose
from lazyflow import graph
from lazyflow import stype
from lazyflow import operators
import numpy

class OpS(graph.Operator):
  name = "OpA"

  Output1 = graph.OutputSlot()
  Output2 = graph.OutputSlot()
  Output3 = graph.OutputSlot()
  Output4 = graph.MultiOutputSlot(level = 1)

  def __init__(self, parent):
    graph.Operator.__init__(self,parent)

  def setupOutputs(self):
    self._configured = True
    self.Output1.meta.shape = (1,)
    self.Output1.meta.dtype = numpy.float32
    self.Output2.meta.shape = (2,)
    self.Output2.meta.dtype = numpy.uint8
    self.Output3.meta.shape = (3,)
    self.Output3.meta.dtype = numpy.uint32

  def execute(self, slot, roi, result):
    pass

class OpA(graph.Operator):
  name = "OpA"

  Input1 = graph.InputSlot()                # required slot
  Input2 = graph.InputSlot(optional = True) # optional slot
  Input3 = graph.InputSlot(value = 3)       # required slot with default value, i.e. already connected
  Input4 = graph.MultiInputSlot(level = 1)

  Output1 = graph.OutputSlot()
  Output2 = graph.OutputSlot()
  Output3 = graph.OutputSlot()
  Output4 = graph.MultiOutputSlot(level =1)


  def __init__(self, parent):
    graph.Operator.__init__(self,parent)
    self._configured = False

  def setupOutputs(self):
    self._configured = True
    self.Output1.meta.shape = self.Input1.meta.shape
    self.Output1.meta.dtype = self.Input1.meta.dtype
    self.Output2.meta.shape = self.Input2.meta.shape
    self.Output2.meta.dtype = self.Input2.meta.dtype
    self.Output3.meta.shape = self.Input3.meta.shape
    self.Output3.meta.dtype = self.Input3.meta.dtype
    self.Output4.meta.shape = self.Input4.meta.shape
    self.Output4.meta.dtype = self.Input4.meta.dtype

  def execute(self, slot, roi, result):
    pass



class TestSlot_notifyConnect(object):

  def setUp(self):
    self.g = graph.Graph()

  def tearDown(self):
    self.g.stopGraph()

  def test_connect(self):
    # test that the notifyConnect callback is called
    # when the slot is connected
    ops = OpS(self.g)
    opa = OpA(self.g)
    opa.Input2.connect(ops.Output2)

    upval = [False]

    def callBack(slot):
      upval[0] = True
    
    # check the connect callback is called
    opa.Input1.notifyConnect(callBack)
    opa.Input1.connect(ops.Output1)
    assert upval[0] == True


    # check the connect callback is called for a slot with default value
    upval[0] = False
    opa.Input3.notifyConnect(callBack)
    opa.Input3.connect(ops.Output3)
    assert upval[0] == True


    # check the connect callback is called for a multi inputslot
    upval[0] = False
    opa.Input4.notifyConnect(callBack)
    opa.Input4.connect(ops.Output4)
    assert upval[0] == True


  def test_no_connect(self):
    ops = OpS(self.g)
    opa = OpA(self.g)

    upval = [False]

    def callBack(slot):
      upval[0] = True

    opa.Input1.notifyConnect(callBack)

    # check the connect callback is not called when reconnecting to the same slot
    opa.Input1.connect(ops.Output1)
    upval[0] = False
    opa.Input1.connect(ops.Output1)
    assert upval[0] == False
    
    # check the connect callback is not called when setting the same value again
    opa.Input1.setValue(10)
    upval[0] = False
    opa.Input1.setValue(10)
    assert upval[0] == False

  def test_unregister_connect(self):
    # check that unregistering a connect callback works
    ops = OpS(self.g)
    opa = OpA(self.g)

    upval = [False]

    def callBack(slot):
      upval[0] = True

    opa.Input1.notifyConnect(callBack)
    opa.Input1.unregisterConnect(callBack)

    opa.Input1.connect(ops.Output1)
    assert upval[0] == False


class TestSlot_notifyDisconnect(object):

  def setUp(self):
    self.g = graph.Graph()

  def tearDown(self):
    self.g.stopGraph()

  def test_disconnect(self):
    # test that the notifyConnect callback is called
    # when the slot is connected
    ops = OpS(self.g)
    opa = OpA(self.g)

    upval = [False]

    def callBack(slot):
      upval[0] = True
    
    # check the disconnect callback is called upon disconnect
    opa.Input1.connect(ops.Output1)
    opa.Input1.notifyDisconnect(callBack)
    opa.Input1.disconnect()
    assert upval[0] == True
    
    # check the disconnect callback is called upon reconnect 
    opa.Input1.connect(ops.Output1)
    upval[0] = False
    opa.Input1.connect(ops.Output2)
    assert upval[0] == True
    
    # check the disconnect callback is called upon setValue when being already connected
    opa.Input1.connect(ops.Output1)
    upval[0] = False
    opa.Input1.setValue(19)
    assert upval[0] == True

  def test_no_disconnect(self):
    ops = OpS(self.g)
    opa = OpA(self.g)

    upval = [False]

    def callBack(slot):
      upval[0] = True

    opa.Input1.notifyDisconnect(callBack)

    # check the disconnect callback is not called when reconnecting to the same slot
    opa.Input1.connect(ops.Output1)
    upval[0] = False
    opa.Input1.connect(ops.Output1)
    assert upval[0] == False
    
    # check the disconnect callback is not called when setting the same value again
    opa.Input1.setValue(10)
    upval[0] = False
    opa.Input1.setValue(10)
    assert upval[0] == False
  
  def test_unregister_disconnect(self):
    # check that unregistering a disconnect callback works
    ops = OpS(self.g)
    opa = OpA(self.g)

    upval = [False]

    def callBack(slot):
      upval[0] = True

    opa.Input1.connect(ops.Output1)

    opa.Input1.notifyDisconnect(callBack)
    opa.Input1.unregisterDisconnect(callBack)

    opa.Input1.disconnect()

    assert upval[0] == False





class TestSlot_notifyMetaChanged(object):

  def setUp(self):
    self.g = graph.Graph()

  def tearDown(self):
    self.g.stopGraph()

  def test_inputslot_changed(self):
    # test that the changed callback is called
    # when the slot meta information changes
    ops = OpS(self.g)
    opa = OpA(self.g)

    upval = [False]

    def callBack(slot):
      upval[0] = True

    # test normal InputSlot
    opa.Input1.notifyMetaChanged(callBack)
    opa.Input1.connect(ops.Output1)
    assert upval[0] == True

    upval[0] = False
    opa.Input1.connect(ops.Output2)
    assert upval[0] == True


    # test InputSlot with default value
    upval[0] = False
    opa.Input3.notifyMetaChanged(callBack)
    opa.Input3.connect(ops.Output1)
    assert upval[0] == True


    # test MultiInputSlot
    upval[0] = False


