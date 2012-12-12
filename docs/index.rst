.. lazyflow documentation master file, created by
   sphinx-quickstart on Wed Dec 12 09:39:51 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

lazyflow developer documentation
====================================

Lazyflow is a python library for multithreaded computations.
Data dependencies are expressed as a data flow graph which is evaluated
in a lazy manner.
I.e. when the user requests a result or a small part of a result only the computations neccessary to 
produce the requested part of the result are carried out.

Contents:

.. toctree::
   :maxdepth: 2
   
   installation
   overview
   advanced



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

