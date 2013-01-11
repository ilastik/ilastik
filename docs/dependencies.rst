==================================
Appendix: Development Dependencies
==================================

.. note:: The `buildem <http://github.com/janelia-flyem/buildem>`_ project uses ilastik as one of its sub-projects.  
          If you're having trouble building any of these dependencies, you might try checking buildem's `ilastik-gui.cmake <https://github.com/janelia-flyem/buildem/blob/master/ilastik-gui.cmake>`_
          script (and it's include files) for hints on the correct build configuration settings.

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

Ilastik Sub-projects
====================

* lazyflow (with drtile)
* volumina

Development
===========

* CMake
* python-distribute

Testing
=======

* nosetests
