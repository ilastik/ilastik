Operator Overview
=================

In Lazyflow computations are encapsulated by so called **operators**, the inputs and results of a computation
are provided through named **slots**. A computation that works on two input arrays and provides one result array
could be represented like this:
  
.. code-block:: python

    from lazyflow.graph import Operator, InputSlot, OutputSlot
    from lazyflow.stype import ArrayLike
    
    class SumOperator(Operator):
      inputA = InputSlot(stype=ArrayLike)  # define an inputslot
      inputB = InputSlot(stype=ArrayLike)  # define an inputslot 
    
      output = OutputSlot(stype=ArrayLike) # define an outputslot

The above operator just specifies its inputs and outputs, the actual definition
of the **computation** is still missing. When another operator or the user requests
the result of a computation from the operator, its **execute** method is called.
The method receives as arguments the outputs slot that was queried and the requested
region of interest:
  
  
.. code-block:: python

    class SumOperator(Operator):
      inputA = InputSlot(stype=ArrayLike)
      inputB = InputSlot(stype=ArrayLike)
    
      output = OutputSlot(stype=ArrayLike)
    
      def execute(self, slot, subindex, roi, result):
        # the following two lines query the inputs of the
        # operator for the specified region of interest
    
        a = self.inputA.get(roi).wait()
        b = self.inputB.get(roi).wait()
    
        # the result of the computation is written into the 
        # pre-allocated result array
    
        result[...] = a+b


Connecting operators and providing input
----------------------------------------

To chain multiple calculations the input and output slots of operators can be **connected**:

.. code-block:: python

    op1 = SumOperator()
    op2 = SumOperator()
    
    op2.inputA.connect(op1.output)


The **input** of an operator can either be the output of another operator, or
the input can be specified directly via the **setValue** method of an input slot:

.. code-block:: python

    op1.inputA.setValue(numpy.zeros((10,20)))
    op1.inputB.setValue(numpy.ones((10,20)))


Performing calculations
-----------------------

The **result** of a computation from an operator can be requested from the **output** slot by calling
one of the following methods:

1. ``__getitem__(slicing)`` : the usual [] array access operator is also provided and supports normal python slicing syntax (no strides!):

.. code-block:: python

    request1 = op1.output[:]
    request2 = op1.output[0:10,0:20]

2. ``__call__( start, stop )`` : the call method of the outputslot expects two keyword arguments,
   namely the start and the stop of the region of interest window
   of a multidimensional numpy array:
  
.. code-block:: python

    # request result via the __call__ method:
    request2 = op1.output(start = (0,0), stop = (10,20))

3. ``get(roi)`` : the get method of an outputslot requires as argument an existing 
   roi object (as in the "execute" method of the example operator):
  
.. code-block:: python

    # request result via the get method and an existing roi object
    request3 = op1.output.get(some_roi_object)

It should be noted that a query to an outputslot does **not** return
the final calculation result. Instead a handle for the running calculation is returned, a so called
**Request** object.

Request objects
---------------

All queries to output slots return **Request** objects. These requests are
processed in parallel by a set of worker threads.

.. code-block:: python

    request1 = op1.output[:]
    request2 = op2.output[:]
    request3 = op3.output[:]
    request4 = op4.output[:]

These request objects provide several methods to obtain the final result of the computation
or to get a notification of a finished computation.

* Synchronous **waiting** for a calculation

    .. code-block:: python
    
        request = op1.output[:]
        result = request.wait()

    after the wait method returns, the result objects contains the actual array that was requested.

* Asynchronous **notification** of finished calculations

    .. code-block:: python
    
        request = op1.output[:]
    
        def callback(request):
            result = request.wait()
            # request.wait() will return immediately 
            # and just provide the result
            # do something useful with the result..
      
        # register the callback function
        # it is called once the calculation is finished
        # or immediately if the calculation is already done.
        request.notify(callback)

* Specification of **destination** result area. Sometimes it is useful
  to tell an operator where to put the results of its computation, when handling
  large numpy arrays this may save copying the array around in memory.

    .. code-block:: python
    
        # create a request
        request = op1.output[:]
        a = numpy.ndarray(op1.output.meta.shape, dtype = op1.output.meta.dtype)
        # specify a destination array for the request
        result = request.writeInto(a)
    
        # when the request.wait() method returns, a will 
        # hold the result of the calculation
        request.wait()

    .. note:: ``writeInto()`` can also be combined with ``notify()`` instead of ``wait()``

When writing operators the execute method obtains 
its input for the calculation from the **input slots** in the same manner.

Meta data
---------

The **input** and **output** slots of operators have associated meta data which
is held in a .meta dictionary.

The content of the dictionary depends on the operator, since the operator is responsible
to provide meaningful meta information on its output slots.

Examples of often available meta information are the shape, dtype and axistags in the
case of ndarray slots.

.. code-block:: python

    op1.output.meta.shape    # the shape of the result array
    op1.output.meta.dtype    # the dtype of the result array
    op1.output.meta.axistags # the axistags of the result array
                             # for more information on axistags, consult the vigra manual


When writing an **operator** the programmer must implement the **setupOutputs** method of the
Operator. This method is called once all necessary inputs for the operator have been connected
(or have been provided directly via **setValue**).

A simple example for the SumOperator is given below:

.. code-block:: python

    class SumOperator(Operator):
      inputA = InputSlot(stype=ArrayLike)
      inputB = InputSlot(stype=ArrayLike)
    
      output = OutputSlot(stype=ArrayLike)
    
      def setupOutputs(self):
        # query the shape of the operator inputs
        # by reading the input slots meta dictionary
        shapeA = self.inputA.meta.shape
        shapeB = self.inputB.meta.shape
    
        # check that the inputs are compatible
        assert shapeA == shapeB
    
        # setup the meta dictionary of the output slot
        self.output.meta.shape = shapeA
    
        # setup the dtype of the output slot
        self.output.meta.dtype = self.inputA.meta.dtype
    
    
      def execute(self, slot, subindex, roi, result):
        pass


Propagating changes in the inputs
---------------------------------

lazyflow operators should propagate changes in its inputs to their outputs.
Since the exact mapping from inputs to outputs depends on the computation the operator
implements, only the operator knows how the state of its outputs changes when an inputslot is modified.

To support the efficient propagation of information about changes operators should implement
the **propagateDirty** method.
This method is called from the outside whenever one of the inputs (or only part of an input) of an operator is changed.

Depending on the calculation which the operator computes the programmer should implement the correct mapping from changes 
in the inputs to changes in the outputs - which is fairly easy for the simple sum operator:

.. code-block:: python

    class SumOperator(Operator):
      inputA = InputSlot(stype=ArrayLike)
      inputB = InputSlot(stype=ArrayLike)
    
      output = OutputSlot(stype=ArrayLike)
    
      def propagateDirty(self, slot, subindex, roi):
        # the method receives as argument the slot
        # which was changed, and the region of interest (roi)
        # that was changed in the slot
        
        # in this case the mapping of the dirty
        # region is fairly simple, it corresponds exactly
        # to the region of interest that was changed in
        # one of the input slots
        self.output.setDirty(roi)
    
      def setupOutputs(self):
        pass
    
      def execute(self, slot, subindex, roi, result):
        pass


Exception propagation through connected Operators
-------------------------------------------------

Exceptions along multiple connected operators are propagated through the graph using exception chaining via the ``Request`` system.

A simple chain like the following

.. code-block:: python
    # exception-test.py
    from lazyflow.graph import InputSlot, OutputSlot, Graph, Operator

    class OpBroken(Operator):
        Out = OutputSlot()

        def setupOutputs(self):
            self.Out.meta.shape = (1,)
            self.Out.meta.dtype = object

        def execute(self, *args, **kwargs):
            raise Exception("OpBroken 👿")

        def propagateDirty(self, *args, **kwargs):
            pass


    class OpPassThrough(Operator):
        In = InputSlot()
        Out = OutputSlot()

        def setupOutputs(self):
            self.Out.meta.shape = (1,)
            self.Out.meta.dtype = object

        def execute(self, *args, **kwargs):
            self.In[:].wait()

        def propagateDirty(self, *args, **kwargs):
            pass

    g = Graph()
    opA = OpBroken(graph=g)
    opB = OpPassThrough(graph=g)
    opB.name = "OpPT_1"
    opC = OpPassThrough(graph=g)
    opC.name = "OpPT_2"
    opB.In.connect(opA.Out)
    opC.In.connect(opB.Out)

    opC.Out[:].wait()

will result in the following traceback chain:

.. code-block:: python
    Traceback (most recent call last):
      File "ilastik/lazyflow/request/request.py", line 384, in _execute
        self._result = self.fn()
      File "ilastik/lazyflow/slot.py", line 869, in __call__
        result_op = self.operator.call_execute(self.slot.top_level_slot, self.slot.subindex, self.roi, destination)
      File "ilastik/lazyflow/operator.py", line 602, in call_execute
        return self.execute(slot, subindex, roi, result, **kwargs)
      File "exception-test.py", line 15, in execute
        raise Exception("OpBroken 👿")
    Exception: OpBroken 👿

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
      File "ilastik/lazyflow/request/request.py", line 384, in _execute
        self._result = self.fn()
      File "ilastik/lazyflow/slot.py", line 869, in __call__
        result_op = self.operator.call_execute(self.slot.top_level_slot, self.slot.subindex, self.roi, destination)
      File "ilastik/lazyflow/operator.py", line 602, in call_execute
        return self.execute(slot, subindex, roi, result, **kwargs)
      File "exception-test.py", line 30, in execute
        self.In[:].wait()
      File "ilastik/lazyflow/request/request.py", line 565, in wait
        return self._wait(timeout)
      File "ilastik/lazyflow/request/request.py", line 588, in _wait
        self._wait_within_foreign_thread(timeout)
      File "ilastik/lazyflow/request/request.py", line 648, in _wait_within_foreign_thread
        raise RequestError(self.fn) from exc_value
    lazyflow.request.request.RequestError: Failed to request data from `OpBroken.Out`

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
      File "ilastik/lazyflow/request/request.py", line 384, in _execute
        self._result = self.fn()
      File "ilastik/lazyflow/slot.py", line 869, in __call__
        result_op = self.operator.call_execute(self.slot.top_level_slot, self.slot.subindex, self.roi, destination)
      File "ilastik/lazyflow/operator.py", line 602, in call_execute
        return self.execute(slot, subindex, roi, result, **kwargs)
      File "exception-test.py", line 30, in execute
        self.In[:].wait()
      File "ilastik/lazyflow/request/request.py", line 565, in wait
        return self._wait(timeout)
      File "ilastik/lazyflow/request/request.py", line 588, in _wait
        self._wait_within_foreign_thread(timeout)
      File "ilastik/lazyflow/request/request.py", line 648, in _wait_within_foreign_thread
        raise RequestError(self.fn) from exc_value
    lazyflow.request.request.RequestError: Failed to request data from `OpPT_1.Out`

    The above exception was the direct cause of the following exception:

    Traceback (most recent call last):
      File "exception-test.py", line 44, in <module>
        opC.Out[:].wait()
      File "ilastik/lazyflow/request/request.py", line 565, in wait
        return self._wait(timeout)
      File "ilastik/lazyflow/request/request.py", line 588, in _wait
        self._wait_within_foreign_thread(timeout)
      File "ilastik/lazyflow/request/request.py", line 648, in _wait_within_foreign_thread
        raise RequestError(self.fn) from exc_value
    lazyflow.request.request.RequestError: Failed to request data from `OpPT_2.Out`


Wrapup: Writing an Operator
---------------------------

To implement a lazyflow operator one should:

* create a subclass of the **Operator** base class

* define the **InputSlots** and **OutputSlots** of the computation

* implement the **setupOutputs** methods to set up the meta information of the 
  output slots depending on the meta information which is available on the input
  slots.

* implement the **execute** method, that is called when an outputslot is queried
  for results.

* implement the **propagateDirty** method, which is called when a region of interest
  of an input slot is changed.

.. code-block:: python

    class SumOperator(Operator):
        inputA = InputSlot(stype=ArrayLike)
        inputB = InputSlot(stype=ArrayLike)
    
        output = OutputSlot(stype=ArrayLike)
    
        def setupOutputs(self):
            pass
    
        def execute(self, slot, subindex, roi, result):
            pass
      
        def propagateDirty(self, slot, subindex, roi):
            pass


