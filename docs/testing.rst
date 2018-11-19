=========================
Appendix: Testing Ilastik
=========================

ilastik comes with a set of unit/regression tests.  You must have `pytest <https://docs.pytest.org/en/latest/getting-started.html>`_ installed to run the tests.

Non-gui tests
=============

To run all the non-gui tests in one go, use pytest:

.. code-block:: bash
   
   $ cd ilastik/tests
   $ pytest --capture=no
   
.. note:: ilastik and lazyflow make extensive use of the python logger.
   Unfortunately, it may result in a lot of unecessary output for failed tests.
   Use the ``--capture=no`` option to disable logger output.

Sometimes it's convenient to run the test scripts one at a time.  A convenience script for that is included in the tests directory:

.. code-block:: bash

    $ cd ilastik/tests
    $ ./testeach.sh .

.. note:: The ``testeach.sh`` script MUST be run from within the tests directory.  It takes an optional argument for the subdirectory to run.

GUI tests
=========

The ilastik GUI tests cannot be run using pytest.  You must run them directly as python scripts (they use pytest internally, but from a different thread).

.. code-block:: bash

    $ cd ilastik/tests
    $ python test_applets/pixelClassification/testPixelClassificationGui.py
    $ python test_applets/pixelClassification/testPixelClassificationMultiImageGui.py

Because of this limitation, the GUI tests are not executed using the travis-CI tool.
