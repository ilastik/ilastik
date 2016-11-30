.. _workflow-design:

========================
Advanced Workflow Design
========================

The most important component of a GUI based on the ilastik framework is the workflow of operators that pass data between applets.  
To design advanced multi-image workflows, you need to have a solid grasp of lazyflow operators and connections.

Before we begin, make sure you know how to write lazyflow operators, and how to combine them into composite operators with OperatorWrapper.
Details can be found in the lazyflow documentation.

Visualizing Multi-Image-Workflows
=================================

In the ilastik framework, each applet has a single 'top-level' operator.  Any changes to the computation parameters (e.g. from user input) must be propagated exclusively via operator slots.  
The applet GUI should be a thin layer of code that simply configures the applet's top-level operator and displays the operator's current state.

The ilastik-shell is designed to handle computation pipelines that handle multiple *image lanes* at once.  For that reason, it is always expected that applets pass their results via multi-slots (i.e. slots of level >= 1).
The multi-slot is always indexed by the image lane index.  As an example, here's the diagram for the ThresholdMasking example workflow, shown with two image lanes loaded:

.. figure:: images/ThresholdMaskingWorkflow_low_detail.svg
   :scale: 100  %
   :alt: Wrapped OpThreshold with shared ThresholdLevel

There are two applets in this workflow: DataSelection and ThresholdMasking.  Notice that the top-level operator for 
the DataSelection applet passes its output as a list of images (i.e. a slot of level=1) to the next applet in the workflow.

Notice that these operators were implemented as simple single-image operators, which simplifies their implementation.  Under the hood, ``StandardApplet`` uses an ``OperatorWrapper`` to achieve the multi-image functionality.
The figure above omits the internal operators.  Here's a more detailed figure:

.. figure:: images/ThresholdMaskingWorkflow_with_internal_ops.svg
   :scale: 100  %
   :alt: Wrapped OpThreshold with shared ThresholdLevel




