Define the variables, python and so on for this particular terminal, 
so that ilastik has everything it wants to have:

source activate ilastik-devel



========================================
Building your own workflow
========================================

Show workflow in ilastik
========================================

.. currentmodule:: ilastik.workflows.NEW_WORKFLOW.NEW_WORKFLOWWorkflow
.. autoclass:: NEW_WORKFLOWWorkflow
   :members:
   
   .. automethod:: __init__





.. currentmodule:: ilastik.workflow

A :py:class:`Workflow` combines a set of applets together to form an entire computational pipeline, along with the GUI to configure it.
A workflow is created when the user loads a project, and destroyed when the project is closed.

The workflow has three main responsibilities:

* Instantiate a set of applets, and expose them as a list for the ilastik shell to display.
* Build up a complete computational pipeline, one *image lane* at a time.  This is done by connecting an individual *image lane* from each applet's :ref:`Top-Level Operator <top_level_ops>`. (More on that in a bit.) 
* Select a particular slot to serve as the "image name slot" for the shell.  The shell uses this slot as the "master list" of all image lanes present in the workflow at any time.

Image Lanes
-----------
