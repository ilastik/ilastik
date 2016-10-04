.. role:: bash(code)
   :language: bash

========================================
Expanding the documentation
========================================

Installation
=================

install sphinx (with python 2) and check:
in Makefile:
Whether the SPHINXBUILD is sphinx-build or sphinx-build2 and with which settings you can run the 
documentation properly by e.g.
make html



If no code in the html files can be seen, then see Troubleshooting. 
Some errors are not good but ok, if they make no optical difference.




Troubleshooting:
=================

* No module lazyflow.graph

  Add the path of the lazyflow git repo to the documentary paths:
  ilastik/ilastik/docs/conf.py
  Add the path to the lazyflow git-repo folder:

  .. code::

          sys.path.append(os.path.abspath('../../lazyflow'))
  
  
  If this doesn't help:

  .. code::

          ln -s /path/to/lazyflow/lazyflow /path/to/ilastik/
  
  so that you have the intern directory lazyflow/lazyflow as a link together with 
  ilastik/ilastik 
  ilastik/lazyflow (link)




* No module vigra found


  Then vigranumpy is compiled for python3.x which can be found in 
  /usr/lib/vigranumpy/VigranumpyConfig.cmake
  
  Then you have to clone the vigra git-repo and install it as mentioned there. 
  http://ukoethe.github.io/vigra/doc-release/vigra/Installation.html


  * Make sure you have the right hdf5 version:
    The one ilastik uses is 1.8.15-patch1 and it has problems with higher headers. Therefore 
    download the git repo from https://github.com/h5py/h5py/blob/master/docs/build.rst
    and do a manually setup with 

    .. code::

        python setup.py configure --hdf5-version=1.8.15
        python setup.py install

  *
  It is important to check the pythonversion displayed in 
  cmake .
  The /usr/bin/python2.7 should be used
  If the version from miniconda2/ilastik etc is used, then copy the vigra-repo to a place where the conda folder
  can't be found directly
  
  Here once more, what to do:

  .. code::

          cmake .
          make          # build (Linux/Unix and MinGW only)
          make check    # compile and run tests (optional, Linux/Unix and MinGW only)
          make doc      # generate documentation (Linux/Unix and MinGW only)
          make install  # install (Linux/Unix and MinGW only) root rights needed
          make examples # build examples (optional, Linux/Unix and MinGW only)
  
  
  if afterwards there is the following import error while 'import vigra':
      import vigra.vigranumpycore as vigranumpycore
  ImportError: libvigraimpex.so.11: cannot open shared object file: No such file or directory
  
  Search for this library:
  sudo find / -name "libvigraimpex.so.11"
  In my case, it lies in:
  /usr/local/lib/libvigraimpex.so.11
  
  test if /usr/local/lib is included in the python paths by:
  python -c "import sys; print sys.path"
  
  
  
  `echo $LD_LIBRARY_PATH`
  
  .. code:: bash
  
          if it is empty:
          export LD_LIBRARY_PATH=/usr/local/lib
          if it isn't:
          export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
  
  to fix this permanently, add this export to your .bashrc file
  
  then try again:
  
  .. code:: bash
  
          python
          import vigra
  
  
  
  testing reST blocks
  
  
  .. code-block::
  
    @a = "using code-block"
    puts @a
  
  
  .. code-block:: ruby
  
    @a = "using code-block ruby"
    puts @a
  
  
  .. code::
  
    @a = "using code"
    puts @a
  
  
  .. code:: ruby
  
    @a = "using code ruby"
    puts @a
  
  
  ::
  
    @a = "using literal block (no syntax sugar)"
    puts @a
