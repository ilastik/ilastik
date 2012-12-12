**ilastik - interactive learning and segmentation toolkit**
=============================================

[![Build Status](https://travis-ci.org/ilastik/ilastik.png?branch=master)](https://travis-ci.org/ilastik/ilastik)

General Dependencies
====================
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


Python Dependencies
===================
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

Ilastik Sub-project Dependencies
================================
* lazyflow (with drtile)
* volumina

Development Dependencies
========================
* CMake
* python-distribute

Testing Dependencies
====================
* nosetests

Calling the tests
=================
Unit tests are executed by nosetests:

    $ python setup.py nosetests

There are some special GUI tests that can't be executed by nose.
Call them manually:

    $ python tests/test_applets/pixelClassification/testPixelClassificationGui.py
    $ python tests/test_applets/pixelClassification/testPixelClassificationMultiImageGui.py

