=========
Utilities
=========

.. contents::
   :depth: 3

General Utilities
=================

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

JSON Config Parsing
-------------------

.. currentmodule:: lazyflow.utility.jsonConfig

Some lazyflow components rely on a special JSON config file format.  The `JsonConfigParser` class handles parsing such files.

.. autoclass:: JsonConfigParser
   :members:

   .. automethod:: __init__

.. autoclass:: Namespace

IO Utilities
============

These utilities provide access to special data formats supported by lazyflow.

.. currentmodule:: lazyflow.utility.io

Blockwise Data Format
---------------------

For big datasets, lazyflow supports a special input/output format that is based on blocks 
of data stored as hdf5 files in a special directory tree structure.  The dataset is described by a special json file.

A small example explains the basics.  Consider a dataset with axes x-y-z and 
shape 300x100x100.  Suppose it is stored on disk in blocks of size 100x50x50.
Let's start by inspecting the dataset description file:

.. code-block:: bash

	$ ls
	data_description_params.json  my_dataset_blocks
	$
	$ cat data_description_params.json 
	{
	    "_schema_name" : "blockwise-fileset-description",
	    "_schema_version" : 1.0,
	    
	    "name" : "example_data",
	    "format" : "hdf5",
	    "axes" : "xyz",
	    "shape" : [300,100,100],
	    "dtype" : "numpy.uint8",
	    "block_shape" : [100, 50, 50],
	    "dataset_root_dir" : "./my_dataset_blocks",
	    "block_file_name_format" : "blockFile-{roiString}.h5/volume/data"
	}

This listing shows how the directory tree is structured:

.. code-block:: bash

	$ ls my_dataset_blocks/*/*/*/*.h5
	my_dataset_blocks/x_00000000/y_00000000/z_00000000/blockFile-([0, 0, 0], [100, 50, 50]).h5
	my_dataset_blocks/x_00000000/y_00000000/z_00000050/blockFile-([0, 0, 50], [100, 50, 100]).h5
	my_dataset_blocks/x_00000000/y_00000050/z_00000000/blockFile-([0, 50, 0], [100, 100, 50]).h5
	my_dataset_blocks/x_00000000/y_00000050/z_00000050/blockFile-([0, 50, 50], [100, 100, 100]).h5
	my_dataset_blocks/x_00000100/y_00000000/z_00000000/blockFile-([100, 0, 0], [200, 50, 50]).h5
	my_dataset_blocks/x_00000100/y_00000000/z_00000050/blockFile-([100, 0, 50], [200, 50, 100]).h5
	my_dataset_blocks/x_00000100/y_00000050/z_00000000/blockFile-([100, 50, 0], [200, 100, 50]).h5
	my_dataset_blocks/x_00000100/y_00000050/z_00000050/blockFile-([100, 50, 50], [200, 100, 100]).h5
	my_dataset_blocks/x_00000200/y_00000000/z_00000000/blockFile-([200, 0, 0], [300, 50, 50]).h5
	my_dataset_blocks/x_00000200/y_00000000/z_00000050/blockFile-([200, 0, 50], [300, 50, 100]).h5
	my_dataset_blocks/x_00000200/y_00000050/z_00000000/blockFile-([200, 50, 0], [300, 100, 50]).h5
	my_dataset_blocks/x_00000200/y_00000050/z_00000050/blockFile-([200, 50, 50], [300, 100, 100]).h5

But you shouldn't really have to worry too much about how the data is stored.
The :py:class:`BlockwiseFileset` and :py:class:`RESTfulBlockwiseFileset` classes 
provide a high-level API for reading and writing such datasets.
See the documentation of those classes for details.

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

