Lazyflow is a python library for multithreaded computations.
Data dependencies are expressed as a data flow graph which is evaluated
in a lazy manner.
I.e. when the user requests a result or a small part of a result only the computations neccessary to 
produce the requested part of the result are carried out.

Installation
============
lazyflow requires python 2.7, numpy, vigra, greenlet and psutil packages:
  
```
sudo easy_install numpy greenlet psutil
```

Vigra can be obtained from  https://github.com/ukoethe/vigra
Optional requirements for lazyflow are the h5py library

```
sudo easy_install h5py
```

After installing the prerequisites lazyflow can be installed:

```
python setup.py config
python setup.py build
sudo python setup.py install
```

Overview
========
In Lazyflow computations are encapsulated by so called **operators**, the inputs and results of a computation
are provided through named **slots**. A computation that works on two input arrays and provides one result array
could be represented like this:
  
``` python
from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import ArrayLike

class SumOperator(Operator):
  inputA = InputSlot(stype=ArrayLike)  # define an inputslot
  inputB = InputSlot(stype=ArrayLike)  # define an inputslot 

  output = OutputSlot(stype=ArrayLike) # define an outputslot
```

The above operator justs specifies its inputs and outputs, the actual definition
of the **computation** is still missing. When another operator or the user requests
the result of a computation from the operator, its **execute** method is called.
The methods receives as arguments the outputs slot that was queried and the requested
region of interest:
  
``` python
class SumOperator(Operator):
  inputA = InputSlot(stype=ArrayLike)
  inputB = InputSlot(stype=ArrayLike)

  output = OutputSlot(stype=ArrayLike)

  def execute(self, slot, roi, result):
    # the following two lines query the inputs of the
    # operator for the specififed region of interest

    a = self.inputA.get(roi).wait()
    b = self.inputA.get(roi).wait()

    # the result of the computation is written into the 
    # pre-allocated result array

    result[roi.toSlice()] = a+b
    
    #  the toSlice() method of the roi object converts
    #  region of interest into a standard python slicing
```

Connecting operators and providing input
----------------------------------------
To chain multiple calculations the input and output slots of operators can be **connected**:

``` python
op1 = SumOperator()
op2 = SumOperator()

op2.inputA.connect(op1.output)
```

The **input** of an operator can either be the output of another operator, or
the input can be specified directly via the **setValue** method of an input slot:

``` python
op1.inputA.setValue(numpy.zeros((10,20)))
op1.inputb.setValue(numpy.ones((10,20)))
```


Performing calculations
-----------------------
The **result** of a computation from an operator can be requested from the **output** slot by calling
one of the following methods:

1. __getitem__(slicing) : the usual [] array access operator is also provided and supports normal python slicing syntax (no strides!):

  ``` python
  request1 = op1.output[:]
  request2 = op1.output[0:10,0:20]
  ```

2. __call__( start, stop ) : the call method of the outputslot expects two keyword arguments,
   namely the start and the stop of the region of interest window
   of a multidimensional numpy array:
  
  ``` python
  # request result via the __call__ method:
  request2 = op1.output(start = (0,0), stop = (10,20))
  ```

3. get(roi) : the get method of an outputslot requires as argument an existing 
   roi object (as in the "execute" method of the example operator):
  
  ``` python
  # request result via the get method and an existing roi object
  request3 = op1.output.get(some_roi_object)
  ```

It should be noted that a query to an outputslot does **not** return
the final calculation result. Instead a handle for the running calculation is returned, a so called
**Request** object.

Request objects
--------------
All queries to output slots return **Request** objects. These requests are
processed in parallel by a set of worker threads.
``` python
request1 = op1.output[:]
request2 = op2.output[:]
request3 = op3.output[:]
request4 = op4.output[:]
```

these request objects provide several methods to obtain the final result of the computation
or to get a notification of a finished computation.

* Synchronous **waiting** for a calculation
  ```python
  request = op1.output[:]
  result = request.wait()
  ```
  after the wait method returns, the result objects contains the actual array that was requested.
* Asynchronous **notification** of finished calculations
  ```python
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
  ```
* Specification of **destination** result area
  ```python
  # create a request
  request = op1.output[:]
  a = numpy.ndarray(op1.output.meta.shape, dtype = op1.output.meta.dtype)
  # specify a destination array for the request
  result = request.writeInto(a)

  # when the request.wait() method returns, a will 
  # hold the result of the calculation
  request.wait()
  ```
  Note: writeInto can also be combined with notify() instead of wait()

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

```python
op1.output.meta.shape    # the shape of the result array
op1.output.meta.dtype    # the dtype of the result array
op1.output.meta.axistags # the axistags of the result array
                         # for more information on axistags, consult the vigra manual
```

When writing an **operator** the programmer must implement the **setupOutputs** method of the
Operator. This method is called once all neccessary inputs for the operator have been connected
(or have been provided directly via **setValue**).

A simple example for the SumOperator is given below:
``` python
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


  def execute(self, slot, roi, result):
    pass
```


  



