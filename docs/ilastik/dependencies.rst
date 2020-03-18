==================================
Appendix: Development Dependencies
==================================

.. note::
   
   The easiest way to build the ilastik development environment on any platform is to use conda.
   The necessary steps are explained in the `ilastik-build-conda <https://github.com/ilastik/ilastik-build-conda>`_ repo. 

General
=======

* boost-python
* libjpeg
* libtiff
* libpng
* fftw3
* hdf5
* Qt4
* Vigra
* VTK, compiled with the following options:
    * VTK_WRAP_PYTHON
    * VTK_WRAP_PYTHON_SIP
    * VTK_USE_QT
    * VTK_USE_QVTK_QTOPENGL

Python
======

* Python 2.7
* PyQt4
* argparse
* numpy
* h5py 2.1
* psutil
* greenlet
* blist
* wsgiref
* qimage2ndarray
* vigranumpy
* Yapsy

Ilastik Sub-projects
====================

* lazyflow
* volumina

Development
===========

* CMake
* python-distribute

Testing
=======

* pytest
