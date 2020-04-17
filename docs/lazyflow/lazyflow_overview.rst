=================
Lazyflow Overview
=================

The lazyflow framework consists of four main modules, shown in this dependency diagram:

.. figure:: images/lazyflow_structure.svg
   :scale: 100  %
   :alt: lazyflow component modules
  
Operator Library
================

Lazyflow comes with a set of reusable operators for performing general image processing computations.
Before writing your own operator for a given task, check to see if one already exists in the library.

Graph Framework
===============

All lazyflow operators are implemented using a special API, defined by the graph framework.
The graph framework implements the "plumbing" that manages interactions between operator inputs and outputs ("slots").
This includes dirty region propagation, "ready" state, request forwarding, resource cleanup, and so on.
When data is requested from an operator slot, the graph framework generates a request for that data.

Request Framework
=================

The request framework is a general-purpose, coroutine-based task scheduling system based on the `greenlet <http://pypi.python.org/pypi/greenlet>`_ python library.
It does not depend in any way on the graph framework, so it could be used to schedule the execution of generic python callables.
It is similar in spirit to other greenlet-based frameworks like `eventlet <http://eventlet.net>`_ and `gevent <http://www.gevent.org>`_, which provide a similar interface for 
highly concurrent IO applications.

Using the lazyflow request framework, it is easy to perform concurrent, asynchronous workloads, without requiring the developer
to write complicated state-machines or messy callback handlers.  The request framework hides this complexity from the developer,
allowing you to write in a clean, blocking *style* without the performance drag of actually blocking the OS thread(s) your workload is executing on.
Internally, requests are scheduled for execution in a fixed-size threadpool.  When a request has to wait for subcomputations to 
complete in other requests, it is temporarily suspended so that its OS thread can be used to perform other work.
See the :ref:`request-framework` documentation for details.

Utility Library
===============

Any functionality not directly related to requests or graph operations is part of the utility module.
See the :ref:`lazyflow-utilities` module documentation for details.
