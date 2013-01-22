
.. _request-framework:

==========================
Lazyflow Request Framework
==========================

.. contents::
   :depth: 3

Introduction
============

See the Lazyflow Overview section for a brief introduction to the Request Framework and its role within lazyflow.

The request framework is a general-purpose, coroutine-based task scheduling system based on the `greenlet <http://pypi.python.org/pypi/greenlet>`_ python library.
It does not depend in any way on the graph framework, so it could be used to schedule the execution of generic python callables.
It is similar in spirit to other greenlet-based frameworks like `eventlet <http://eventlet.net>`_ and `gevent <http://www.gevent.org>`_, which provide a similar interface for 
highly concurrent IO applications.

Using the lazyflow request framework, it is easy to perform concurrent, asynchronous workloads, without requiring the developer
to write complicated state-machines or messy callback handlers.  The request framework hides this complexity from the developer,
allowing you to write in a clean, blocking *style* without the performance drag of actually blocking the OS thread(s) your workload is executing on.
Internally, requests are scheduled for execution in a fixed-size threadpool.  When a request has to wait for subcomputations to 
complete in other requests, it is temporarily suspended so that its OS thread can be used to perform other work.
See the Request Framework documentation for details.

This dependency diagram shows how user-defined workloads depend on the parts of the request system.

.. figure:: images/request_framework_structure.svg
   :scale: 100  %
   :alt: request framework dependencies

.. note:: The request framework is written to allow easy parallelization of computations.
          In Python, the *Global Interpreter Lock* (GIL) prevents the interpreter from executing two python statements at once.
          This restriction does not apply to C or C++ extensions (as long as they release the GIL).
          Therefore, the Request framework is most useful for workloads that do most of their "heavy lifting" within C/C++ extensions.
          For pure Python workloads, the Request Framework doesn't provide performance benefits, but may still be useful for the abstractions it provides.

.. _quick-start:

Quick Start
===========

Let's start with an example computation.  Suppose you want to smooth an image at two different scales, then subtract the two resulting images.
A naive implementation of this computation might look like this:

.. code-block:: python

    from some_img_lib import smooth

    def f(image, sigmaA, sigmaB):
        smoothedA = smooth(image, sigmaA)
        smoothedB = smooth(image, sigmaB)
        
        result = smoothedA - smoothedB
        return result

    diff_of_smoothed = f(my_image, 1.0, 3.0)

The above single-threaded approach leaves much room for improvement.  Using the request framework, we can parallelize the workload:

.. code-block:: python

    from some_img_lib import smooth
    from functools import partial
    from lazyflow.request import Request
    
    def f(image, sigmaA, sigmaB):
        r2 = Request( partial(smooth, image, sigmaA) )
        r3 = Request( partial(smooth, image, sigmaB) )

        # Start executing r3
        r3.submit()

        # Wait until both requests are complete
        smoothedA = r2.wait() # (Auto-submits)
        smoothedB = r3.wait()
        
        result = smoothedA - smoothedB
        return result

    r1 = Request( partial(f, my_image, 1.0, 3.0) )
    diff_of_smoothed = r1.wait()

To understand the example, we make a few key observations:

- Request objects are constructed with a single callable object, which it executes
- Requests do not execute their callable until they have been submitted via ``Request.submit()``.
- ``Request.wait()`` automatically calls ``submit()`` if the request hasn't been submitted yet.
- The callable's return value is given as the result of ``Request.wait()``.
- ``functools.partial`` (from the python standard library) is a convenient way of creating a new callable object from a function and a set of arguments.

In cases where we are creating multiple requests and waiting until they are all complete, we can use a RequestPool, which eliminates some boilerplate.

.. code-block:: python

    from some_img_lib import smooth
    from functools import partial
    from lazyflow.request import Request, RequestPool
    
    def f(image, sigmaA, sigmaB):
        r2 = Request( partial(smooth, image, sigmaA) )
        r3 = Request( partial(smooth, image, sigmaB) )

        pool = RequestPool()
        pool.add( r2 )
        pool.add( r3 )        
        pool.wait()

        return r2.result - r3.result

    r1 = Request( partial(f, my_image, 1.0, 3.0) )
    diff_of_smoothed = r1.wait()

Okay, in our example, only two of the requests can execute in parallel, so the RequestPool didn't save any code in this case.
Anyway, we have more observations to make note of:

- ``RequestPool.wait()`` will block until all requests in the pool have completed.
- All Request objects save their callable's return value as an attribute: ``Request.result``

Dependencies
============

Here's a visualization of the dependencies between the requests from the quickstart example:

.. figure:: images/request_dependency.svg
   :scale: 100  %
   :alt: request dependency diagram

As you can see, r1 depends on BOTH r2 and r3.  In a typical use case, request dependencies form a tree, but this isn't always true.
Let's tweak our example even further.  In the new version, we don't already have the input image.  Instead, we compute it in a separate request.

.. code-block:: python

    from some_img_lib import smooth, compute_sample_image
    from functools import partial
    from lazyflow.request import Request, RequestPool
    
    def waitAndSmooth( imageRequest, sigma ):
        image = imageRequest.wait()
        return smooth(image)
    
    def f(imageRequest, sigmaA, sigmaB):
        r2 = Request( partial(waitAndSmooth, imageRequest, sigmaA) )
        r3 = Request( partial(waitAndSmooth, imageRequest, sigmaB) )

        pool = RequestPool()
        pool.add( r2 )
        pool.add( r3 )        
        pool.wait()

        return r2.result - r3.result

    r4 = Request( compute_sample_image )
    r1 = Request( partial(f, r4, 1.0, 3.0) )
    diff_of_smoothed = r1.wait()

Now our example is getting a little contrived for such a simple computation, but bear with us.
The request dependencies are visualized in the following diagram:

.. figure:: images/request_dependency_shared.svg
   :scale: 100  %
   :alt: request dependency diagram


Cancellation
============

The request framework is designed to support interactive GUIs, in which the computational workload may need to be altered on the fly.
In such an environment, it may be necessary to *cancel* a request that has already been submitted.

To cancel a request, simply call ``Request.cancel()``

.. code-block:: python

    r1 = Request( some_work )
    r1.submit()
    
    # ...
    
    r1.cancel()

If the request was waiting for any other requests, those requests will be cancelled, too.

.. code-block:: python

    def some_work():
        r2 = Request( some_more_work )
        return r2.wait()

    r1 = Request( some_work )
    r1.submit()
    
    # ...
    
    r1.cancel() # Cancels r1 AND r2.

But a request will not be cancelled unless ALL of the requests that were waiting for it have already been cancelled.
For example, suppose the dependency graph for some group of requests looked like this:

.. figure:: images/request_cancellation_example_before.svg
   :scale: 100  %
   :alt: request dependency diagram

Now suppose that we call ``r1.cancel()``.  The following diagram shows all cancelled requests in red.

.. figure:: images/request_cancellation_example_after.svg
   :scale: 100  %
   :alt: request dependency diagram

Notice that r3 and subsequent requests were **not** cancelled because there is a non-cancelled request (r2) still waiting for it.

Handling Cancellation
---------------------

Within the context of a request, cancellation produces an exception.  When a request has been cancelled, nothing happens at first.  
As soon as the request cedes control to the Request framework by calling ``Request.wait()`` on a child request, a cancellation request is raised.
In a typical application, requests are used to execute pure functional callables.  For pure-functional requests, there's no need to handle the cancellation exception.
However, in some applications, you may want to use requests to modify some external state.
In that case, you'll need to handle the cancellation exception that might be raised any time your request calls ``wait()``.

.. code-block:: python

    global_list = [1,2,3]
    
    def add_items_to_global_list( num_items ):
        initial_size = len(global_list)
        try:
            for n in range(num_items):
                req = Request( get_next_item )
                next_item = req.wait() # Might raise
                global_list.append( next_item )
        except Request.CancellationException:
            # Restore the previous global state
            global_list = global_list[0:initial_size]
            raise

    r1 = Request( functools.partial(add_items_to_global_list, n) )
    r1.submit()
    
    # ...
    
    r1.cancel() # Cancels r1 AND r2.

In the example above, we catch the ``Request.CancellationException`` that might be raised within ``req.wait()``.
Note that we **re-raise** the exception after we clean up.  Re-raising the cancellation exception isn't strictly 
required by the current Request framework implementation, but it is considered best practice nonetheless.

.. note:: There is a special corner case that can occur if your request attempts to wait for a request that has *already been cancelled* from some other thread or request.
          If you attempt to wait for a request that is already cancelled, a ``Request.InvalidRequestException`` is raised.

Failed Requests
===============

If any exception is raised within a request (other than a cancellation exception), the request fails.  
The exception that caused the failure is propagated to the request(s) or thread(s) that are waiting for it.

.. code-block:: python

    def some_work():
        raise RuntimeError("Something went wrong.")

    r1 = Request( some_work )
    try:
        r1.wait()
    except:
        sys.stderr("Request failed.")
    
.. note:: Request failure handling and exception propagation is relatively heavy-weight.  
	      You can and should rely on it to catch occasional or unexpected failures, but do not rely 
	      on it as though it were as cheap as a simple if/else statement.  If your requests are 
	      repeatedly raising and catching exceptions, your performance may suffer.

Exception Propagation
---------------------

As mentioned above, exceptions raised in a request are propagated backwards to waiting requests.
There is an interesting consequence of this behavior: For the special case where a request is being waited on by multiple requests, 
a single exception may propagate through multiple callstacks.

Consider this request dependency graph:

.. figure:: images/request_exception_propagation_before.svg
   :scale: 100  %
   :alt: request dependency diagram

Suppose an exception is raised in r1.  The following series of diagrams highlights the requests in which the exception will be seen.

.. figure:: images/request_exception_propagation_before.svg
   :scale: 100  %
   :alt: request dependency diagram

.. figure:: images/request_exception_propagation_step1.svg
   :scale: 100  %
   :alt: request dependency diagram

.. figure:: images/request_exception_propagation_step2.svg
   :scale: 100  %
   :alt: request dependency diagram

.. figure:: images/request_exception_propagation_step3.svg
   :scale: 100  %
   :alt: request dependency diagram

.. figure:: images/request_exception_propagation_step4.svg
   :scale: 100  %
   :alt: request dependency diagram

.. figure:: images/request_exception_propagation_step5.svg
   :scale: 100  %
   :alt: request dependency diagram

Request Notifications
=====================

For some use-cases, you may want to be notified when a request completes.  Request objects allow you to subscribe callbacks to three notifications:

- Use ``Request.notify_finished()`` to be notified when a request completes **successfully**.
- Use ``Request.notify_failed()`` to be notified when a request has **failed** (due to an uncaught exception).
- Use ``Request.notify_cancelled()`` to be notified when a request has been **cancelled**.

Here's an example:

.. code-block:: python
    
    def some_work():
        """Do some work."""
    
    def handle_result(result)
        print "The result was:", result
    
    def handle_failure(ex):
        print "The request failed due a {} exception".format( type(ex) )
    
    def handle_cancelled():
        print "The request was cancelled"
        
    req = Request( some_work )
    req.notify_finished( handle_result )
    req.notify_failed( handle_failure )
    req.notify_cancelled( handle_cancelled )

    try:
        req.wait()
    finally:
        print "Request is no longer executing."

Callback Timing Guarantee
-------------------------

If you're paying very close attention, you might be thinking of a question:
  
Does ``Request.wait()`` return **before** or **after** the callbacks are notified?
In other words, after I ``wait()`` for a request, is it guaranteed that my callbacks have finished executing?

Answer:

- Callbacks that were subscribed (via ``notify_finished``, ``notify_failed``, ``notify_cancelled``)
  *before* the call to ``Request.wait()`` are *guaranteed* to be called before ``Request.wait()`` returns.  
- Callbacks that are subscribed *after* you call ``Request.wait()`` will eventually be called, 
  but the timing of the notification is **not** guaranteed to be before ``Request.wait()`` returns.

RequestLock Objects
===================

"Simultaneous" requests share the same pool of OS threads.
The usual ``Lock`` and ``RLock`` objects from the python standard threading module will **not** function as intended within the context of a Request.\*\*
The Request Framework provides an alternative lock, which **can** be used within a Request.  The ``request.RequestLock`` class has the same API as 
``threading.Lock``, and can be used as a drop-in replacement.  See the ``RequestLock`` documentation for further details.

.. note:: \*\*Actually, ``threading.Lock`` *can* be used within a Request if used carefully.
          As long as ``wait()`` is not called while the lock is held, there is no increased risk of deadlock or unexpected race conditions.
          The ``ResultLock`` class relieves the developer of this constraint.

Implementation Details
======================

This section is of interest to developers who need to maintain or experiment with the implementation of the Request Framework.

ThreadPool
----------

As indicated in the dependency diagram in the introduction, the ThreadPool class is an independent module.  
In fact, since it does not depend on the rest of the Request Framework in any way, it could be useful as a general thread pool utility for other applications.
Tasks are added to the ThreadPool via ``ThreadPool.wake_up()``.  At first, they sit in a queue of tasks that is shared by all Worker threads.
Each Worker thread keeps its own queue of tasks to execute.  When a Worker's task queue becomes empty, it pulls a task from the shared queue.

.. _thread-context-guarantee:

Thread Context Consistency Guarantee
------------------------------------

For simple tasks (e.g. plain functions), that's the end of the story.  For more complicated cases (e.g. requests, generators, etc.) that may 
be woken up multiple times, the ``ThreadPool`` provides an important guarantee: a given task will always execute on the SAME Worker thread, every time 
it is woken up.  The Worker thread chosen for a particular task is arbitrary for the first time it is woken up, but it will return to the same 
Worker thread for each subsequent call to ``wake_up()``.  This guarantee is essential for coroutine based tasks based on greenlets (e.g. all Requests).

Request Lifetime
----------------

We'll use the following diagram to track the state of a request throughout its lifetime.

.. figure:: images/request_lifetime_blank.svg
   :scale: 100  %
   :alt: empty request lifetime diagram

Let's consider the first example we used in the :ref:`quick-start` section from above:

.. code-block:: python

    from some_img_lib import smooth
    from functools import partial
    from lazyflow.request import Request
    
    def f(image, sigmaA, sigmaB):
        r2 = Request( partial(smooth, image, sigmaA) )
        r3 = Request( partial(smooth, image, sigmaB) )

        # Start executing r3
        r3.submit()

        # Wait until both requests are complete
        smoothedA = r2.wait() # (Auto-submits)
        smoothedB = r3.wait()
        
        result = smoothedA - smoothedB
        return result

    r1 = Request( partial(f, my_image, 1.0, 3.0) )
    diff_of_smoothed = r1.wait()

The first request is created on this line:

.. code-block:: python

    r1 = Request( partial(f, my_image, 1.0, 3.0) )

Since it hasn't been submitted yet, it isn't yet known to the ThreadPool:

.. figure:: images/request_lifetime_r1_not_submitted.svg
   :scale: 100  %
   :alt: r1 not yet submitted

;;;;

The next line (implicitly) submits the request and immediately blocks for it.

.. code-block:: python

    diff_of_smoothed = r1.wait()

When the request is submitted, it is given to the ThreadPool.  Since the ThreadPool hasn't seen this request previously, it ends up in the shared task queue.
    
.. figure:: images/request_lifetime_r1_unassigned.svg
   :scale: 100  %
   :alt: r1 not yet submitted

;;;;

Next, it is picked up by one of the ThreadPool's worker threads:

.. figure:: images/request_lifetime_r1_executing_A.svg
   :scale: 100  %
   :alt: r1 executing

;;;;

When r1 starts executing, it creates two new requests:

.. code-block:: python

        r2 = Request( partial(smooth, image, sigmaA) )
        r3 = Request( partial(smooth, image, sigmaB) )

.. figure:: images/request_lifetime_r2_r3_not_submitted.svg
   :scale: 100  %
   :alt: r2 and r3 not yet submitted

;;;;

First, it submits r3:

.. code-block:: python

        # Start executing r3
        r3.submit()

.. figure:: images/request_lifetime_r3_submitted.svg
   :scale: 100  %
   :alt: r1 not yet submitted

...which is eventually picked up by a ThreadPool Worker thread:

.. figure:: images/request_lifetime_r3_executing_A.svg
   :scale: 100  %
   :alt: r3 executing

;;;;

For the sake of illustration, let's suppose that some other part of our app has also just submitted some requests:

.. figure:: images/request_lifetime_extra_requests_submitted.svg
   :scale: 100  %
   :alt: r2 submitted

;;;;

Back in r1, we submit and wait for r2.

.. code-block:: python

        smoothedA = r2.wait() # (Auto-submits)

This happens in two steps.  First, r2 is submitted:

.. figure:: images/request_lifetime_r2_submitted.svg
   :scale: 100  %
   :alt: r2 submitted

Next, r1 is *suspended* (since it is now waiting for r2).

.. figure:: images/request_lifetime_r1_suspended.svg
   :scale: 100  %
   :alt: r1 suspended

;;;;

This next step exhibits the advantage of the Request Framework over a simple ThreadPool.
Since r1 has been suspended, it *no longer ties up a Thread*.
The newly available worker now picks up a request from the shared queue:

.. figure:: images/request_lifetime_r1_suspended_B.svg
   :scale: 100  %
   :alt: r1 suspended

;;;;

Eventually, each request either completes or is suspended, and r2 makes it to the front of the shared queue:

.. figure:: images/request_lifetime_r2_front_of_queue.svg
   :scale: 100  %
   :alt: r1 suspended

...and gets picked up by a free worker:

.. figure:: images/request_lifetime_r2_executing.svg
   :scale: 100  %
   :alt: r1 suspended

;;;;

Meanwhile, r3 finishes execution:

.. figure:: images/request_lifetime_r3_finished.svg
   :scale: 100  %
   :alt: r1 suspended

;;;;

After a while, suppose other requests (from other parts of the app) continue to be submitted:

.. figure:: images/request_lifetime_r2_executing_other_requests_woken.svg
   :scale: 100  %
   :alt: r2 executing, other requests woken

;;;;

Eventually, r2 finishes execution:

.. figure:: images/request_lifetime_r2_finished.svg
   :scale: 100  %
   :alt: r2 finished

;;;;

Since r2 and r3 are both complete, r1 can finally be woken up again:

.. figure:: images/request_lifetime_r1_woken_up.svg
   :scale: 100  %
   :alt: r1 woken up

The last figure shows something important.  Did you catch it?  When r1 was **initially** submitted to the ThreadPool, it didn't matter which Worker was chosen to execute it in.  
But now that it is being re-awoken, it **must** execute on the same Worker that it used previously.  
It is not added to the ThreadPool's shared queue.  
Also, it does not execute on the second worker thread, even though (in our example) that thread happens to be unoccupied at the moment.  
It is added to the first worker's queue.  This is a constraint imposed by the greenlet package, which is used to implement Request coroutines.
See also: :ref:`thread-context-guarantee`.

;;;;

When the first worker becomes free, r1 can finally resume execution:

.. figure:: images/request_lifetime_r1_executing_B.svg
   :scale: 100  %
   :alt: r1 executing again

...and eventually r1 finishes execution.

.. figure:: images/request_lifetime_r1_finished.svg
   :scale: 100  %
   :alt: r1 finished

Optimization: Direct Execution
------------------------------

From the user's perspective, calling ``req.wait()`` is equivalent to:

.. code-block:: python

    req.submit()
    req.wait()
    
But under the hood, the Request framework uses an optimization for the case where ``req.wait()`` is called on a request that hasn't been submitted yet.
Instead of submitting the request to the ThreadPool, the request is simply executed *synchronously*.
There is no need to incur the overhead of creating a new greenlet, queueing the request, and so on. 
With this optimization, we don't have to pay a significant penalty for using requests in cases where no parallelism was needed in the first place.

Foreign Thread Context vs. Request Context
------------------------------------------

Internally, the Request Framework distinguishes between two types of execution contexts: ``request.RequestGreenlet`` and "normal" a.k.a "foreign" threads.
If a Request is waited upon from within a foreign thread, we don't attempt to suspend the foreign thread.
Instead, we simply use a regular threading.Event to wait for the Request to complete.
The current context is obtained by calling the classmethod ``Request.current_request()``.  It returns ``None`` if the current context is a "foreign" thread.

Request Priority
----------------

The queue class used by the ``ThreadPool`` can be easily configured.  One of the options is a priority queue, in which tasks are ordered according to their implementation of ``__lt__``.
Requests are prioritized according to a simple rule: whichever request has the oldest ancestor (i.e. the request that spawned it) has higher priority.
If two requests have a common ancestor, then their next-oldest ancestors are compared, and so on.  This way, we hope to avoid cache and RAM thrashing that might be 
encountered if newer requests were to "cut in line" in front of older requests, preventing the old requests from finishing as quickly as possible.

.. note:: This prioritization scheme is simple, and could maybe be improved.  Fortunately, the ThreadPool class is written to allow easy experimentation with different queueing schemes.

Old API Backwards Compatibility
-------------------------------

As a temporary convenience for migration to the latest version of the Request Framework, a few methods from the old API have been provided:

- ``Request.onFinish()`` (now replaced with ``Request.notify_finished()``)
- ``Request.onCancel()`` (now replaced with ``Request.notify_cancelled()``)
- ``notify()`` (now replaced with ``Request.submit()`` followed by ``Request.notify_finished()``)
- ``Request.allocate()`` (not supported any more)
- ``Request.getResult()`` (now replaced with ``Request.result``)
- ``Request.writeInto()`` (This member is specific to the Lazyflow Graph Framework.  It will soon be implemented there, in a special subclass of ``Request``.)

Additionally, the old and new implementations of the old API can be quickly switched without even checking out a new branch in git.  Just edit lazyflow/request/__init__.py.

.. note:: Backwards-compatibility support will be removed soon.  
          If you are depending on the old API, please upgrade your code.  
          If you suspect a bug in the new implementation, verify that it does not occur under the old implementation by editing lazyflow/request/__init__.py. 

Class Reference
===============

.. currentmodule:: lazyflow.request

.. _request:

Request
-------

.. autoclass:: Request
   :members:
    
   .. automethod:: __init__

RequestLock
-----------

.. autoclass:: RequestLock
   :members:
    
RequestPool
-----------

.. autoclass:: RequestPool
   :members:
    
ThreadPool
----------

.. currentmodule:: lazyflow.request.threadPool

.. autoclass:: ThreadPool
   :members:

   .. automethod:: __init__

.. autoclass:: PriorityQueue

.. autoclass:: FifoQueue
    
.. autoclass:: LifoQueue
    
    