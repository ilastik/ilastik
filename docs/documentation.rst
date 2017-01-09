.. role:: bash(code)
   :language: bash

========================================
Documentation Expansion
========================================

If you want to expand this installation, the following guide may help you with some
beginners problems.



Installation
=================

install sphinx (with python 2) and check:
in Makefile:
Whether the SPHINXBUILD is sphinx-build or sphinx-build2 and with which settings you can run the 
documentation properly by e.g. by

.. code::

        $ make html



If no code in the html files can be seen, then see :ref:`Troubleshooting <docu_troubleshooting>`.
Some errors are not good but ok, if they make no optical difference or if they come from python-code you shouldn't change.

Usage
===============

Add any new file to the index.rst file into the table of contents.





.. _docu_troubleshooting:

Troubleshooting:
=================

* folder _static does not exist 
  .. code::
        
        copying static files... WARNING: html_static_path entry u'/*/ilastik/docs/_static' does not exist

  Can be omitted with:
  
  .. code::
        
        mkdir _static

* At first, check if you are working in the ilastik-devel environment, 

  Otherwise change to the environment like this:

  .. code::

        $ CONDA_ROOT=`conda info --root`
        $ source ${CONDA_ROOT}/bin/activate ilastik-devel

  and that the installation worked fine.
  Then try again and try on branch master before trying other things.

* No mudule h5py
  see whether pip has installed this module in the given environment. 
  If it isn't, then install it with pip. 
  If it is, then reinstall ilastik with conda, because you 
  The one ilastik uses is 1.8.15-patch1 and it has problems with higher headers. 

* No module lazyflow.graph

  Add the path of the lazyflow git repo to the documentary paths:
  ilastik/ilastik/docs/conf.py
  Add the path to the lazyflow git-repo folder:

  .. code::

          sys.path.append(os.path.abspath('../../lazyflow'))
  
  
  If this doesn't help:

  .. code::

          $ ln -s /path/to/lazyflow/lazyflow /path/to/ilastik/
  
  so that you have the intern directory lazyflow/lazyflow as a link together with 
  ilastik/ilastik 
  ilastik/lazyflow (link)

* ImportError:
        Add a path to the sys.path in the conf.py file in the docs directory. 
        The path should be adapted to your needs and a directory with the module name must 
        be found in the added path. 

        * ImportError: No module named ilastik_feature_selection
          
          .. code::
          
                sys.path.append('/home/USER/miniconda2/envs/ilastik-devel/lib/python2.7/site-packages')


        * ImportError: No module named qimage2ndarray

          Download the repository for qimage2ndarray from https://github.com/hmeine/qimage2ndarray
          and unzip it. 

          .. code::
          
                sys.path.append('/home/USER/qimage2ndarray/qimage2ndarray-master')


* the PyQt4.QtCore and PyQt5.QtCore modules both wrap the QObject class

  That means, that e.g. matplotlib uses PyQt5 and ilastik uses PyQt4, 
  therefore there is a conflict.

  As a workaround, add the following lines at the top of the conf.py in your documentaion
  
  .. code::

          from PyQt4 import QtGui, QtCore
          import matplotlib #new line
          matplotlib.use("Qt4Agg") #new line


* No module vigra found

  Then vigranumpy is compiled for python3.x which can be found in 
  /usr/lib/vigranumpy/VigranumpyConfig.cmake
  
  Then you have to clone the vigra git-repo and install it as mentioned there. 
  http://ukoethe.github.io/vigra/doc-release/vigra/Installation.html



  It is important to check the pythonversion displayed in 
  cmake .
  The /usr/bin/python2.7 should be used
  If the version from miniconda2/ilastik etc is used, then copy the vigra-repo to a place where the conda folder
  can't be found directly
  
  Here once more, what to do:

  .. code::

          $ cmake .
          $ make          # build (Linux/Unix and MinGW only)
          $ make check    # compile and run tests (optional, Linux/Unix and MinGW only)
          $ make doc      # generate documentation (Linux/Unix and MinGW only)
          $ make install  # install (Linux/Unix and MinGW only) root rights needed
          $ make examples # build examples (optional, Linux/Unix and MinGW only)
  
  
  if afterwards there is the following import error while 'import vigra':
  .. code::

      import vigra.vigranumpycore as vigranumpycore

  ImportError: libvigraimpex.so.11: cannot open shared object file: No such file or directory
  
  Search for this library:
  sudo find / -name "libvigraimpex.so.11"
  In my case, it lies in:
  /usr/local/lib/libvigraimpex.so.11
  
  test if /usr/local/lib is included in the python paths by:
  $ python -c "import sys; print sys.path"
  
  
  
  `echo $LD_LIBRARY_PATH`
  
  .. code:: bash
  
          if it is empty:
          $ export LD_LIBRARY_PATH=/usr/local/lib
          if it isn't:
          $ export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
  
  to fix this permanently, add this export to your .bashrc file
  
  then try again:
  
  .. code:: bash
  
          $ python
          import vigra
  
  
  

