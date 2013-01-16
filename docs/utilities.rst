=================
General Utilities
=================

.. contents:: Contents
   :depth: 3

.. currentmodule:: lazyflow.utility

OrderedSignal
-------------

.. autoclass:: OrderedSignal
   :members:
	
   .. automethod:: __call__

Trace Logging
-------------

.. autoclass:: Tracer

.. autofunction:: traceLogged

Path Manipulation
-----------------

.. autoclass:: PathComponents
   :members:

   .. automethod:: __init__

.. autofunction:: getPathVariants

FileLock
--------

.. automodule:: lazyflow.utility.fileLock

.. autoclass:: FileLock
   :members:

   .. automethod:: __init__

============
IO Utilities
============

These utilities provide access to special data formats supported by lazyflow.

.. currentmodule:: lazyflow.utility.io

BlockwiseFileset
----------------

.. autoclass:: BlockwiseFileset
   :members:
   
   .. automethod:: __init__

Remote Volumes
--------------

.. autoclass:: RESTfulVolume
   :members:
   
   .. automethod:: __init__

.. autoclass:: RESTfulBlockwiseFileset
   :members:
   
   .. automethod:: __init__

