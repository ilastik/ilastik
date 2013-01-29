===============
Utility Classes
===============

.. currentmodule:: ilastik.utility

.. autoclass:: bind

   .. automethod:: __init__

   .. automethod:: __call__

.. autoclass:: SimpleSignal
   :members:

.. autoclass:: PathComponents
   :members:

   .. automethod:: __init__

.. autoclass:: OperatorSubView

   .. automethod:: __init__

.. autoclass:: MultiLaneOperatorABC
	:members:

.. autoclass:: OpMultiLaneWrapper
	:members:


GUI Utilities
=============

QT can be finicky about calling certain functions from non-GUI threads.  
These two utility classes provide mechanisms for forcing code to be called from within the GUI thread.

.. currentmodule:: ilastik.utility.gui

.. autoclass:: ThunkEventHandler
   :members:

   .. automethod:: __init__


.. autofunction:: threadRouted

.. autoclass:: ThreadRouter

   .. automethod:: __init__
