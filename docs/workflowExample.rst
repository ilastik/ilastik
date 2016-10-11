================================================================================
Building your own workflow: workflowExample
================================================================================
Define the variables, python and so on for this particular terminal, 
so that ilastik has everything it wants to have:

.. code::

        $ source activate ilastik-devel


Show workflow in ilastik
========================================

.. code::

        $ ilastik/workflows/__init__.py

add the following lines (adjusted to your project) at the disired position, 
between which other workflows it should lie:

.. code::

        try:
            import workflowExample
            WORKFLOW_CLASSES += [workflowExample.workflowExampleWorkflow.WorkflowExampleWorkflow]
        except ImportError as e:
            logger.warn("Failed to import 'workflowExample' workflow; check dependencies: " + str(e))


Basic Structure
========================================

Then create a folder in 
ilastik/workflows/
with the name workflowExample:
In this directory there are 2 files:
#. __init__.py
.. literalinclude:: ../ilastik/workflows/workflowExample/__init__.py
    :linenos:
    :language: python

#. workflowExampleWorkflow.py
   * Includes all the applets for this workflow and how they are connected with each other
   * Includes all the exposing to the shell and the update handling for applets

The lines marked with TODO should be replaced for a new workflow.
There you can include the desired applets.


.. currentmodule:: ilastik.workflows.workflowExample
.. currentmodule:: ilastik.workflows.workflowExample.workflowExampleWorkflow
.. autoclass:: WorkflowExampleWorkflow
   :members:
   





Image Lanes
-----------
