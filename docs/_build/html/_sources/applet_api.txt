==========
Applet API
==========

Workflows
=========

A workflow represents a list of applets to display in the shell.  It is created when a project is loaded, 
and destroyed when the project is closed.
If the user opens more than one image in a workflow, then the workflow is said to have multiple *image lanes*.
Each *image lane* is named according to the name of the input image it processes.  
The workflow provides the list of currently loaded image lanes to the shell 
via a special slot known as the "image name list".  The shell GUI presents this list of image names to the user, 
allowing him to select which image lane he wants to view.

When the user opens a new image in the workflow, the workflow creates a new image lane to process it.  This is done by calling 
``addLane`` on every applet's topLevelOperator, and then calling ``connectLane`` to connect together the lanes from each applet.
See :py:class:`MultiLaneOperatorABC<ilastik.applets.base.multiLaneOperator.MultiLaneOperatorABC>` for more details. 

A workflow is instantiated when a project is loaded, and it is destroyed (it's ``cleanUp`` method is called)
when the project is closed.  The cleanUp function is responsible for freeing all resources owned by the 
applets, including GUI resources.

.. currentmodule:: ilastik.workflow
.. autoclass:: Workflow
   :members:
   
   .. automethod:: __init__

Applets
=======

Applet classes do not have much functionality, but instead serve as a container for the main components of an applet:

* Top-level Operator
* GUI
* Serializer(s)

Applets must inherit from the Applet abstract base class.  Subclasses should override the appropriate properties.  
The base class provides a few signals, which applets can use to communicate with the shell. 

.. currentmodule:: ilastik.applets.base.applet
.. autoclass:: Applet
   :members:
   
   .. automethod:: __init__

.. autoclass:: ControlCommand
   :members:

.. autoclass:: ShellRequest
   :members:

.. currentmodule:: ilastik.applets.base.standardApplet
.. autoclass:: StandardApplet
   :members:
   
   .. automethod:: __init__


Top-level Operators
===================

Everything an applet does is centered around the applet's top-level operator.  
It is typically the keeper of all state associated with the applet.
The top-level operators that the workflow and shell see must be capbable of handling multiple image lanes.
That is, they must adhere to the :py:class:`MultiLaneOperatorABC<ilastik.applets.base.multiLaneOperator.MultiLaneOperatorABC>`.
If your applet inherits from ``StandardApplet``, then your single-lane top-level operator can be automatically adapted to the multi-lane interface.

The applet GUI and the applet serializers both make changes to the top-level operator and listen for changes made to the top-level operator.
Here's an example timeline, showing a typical sequence of interactions.

1) The shell is launched with a blank workflow
    * All slots are connected, but none have any data
2) The shell loads a project file
    * Calls each serializer to read settings from the project file and apply them to the appropriate slots of the top-level operator
3) The GUI responds to the changes made to the top-level operator by updating the GUI appearance.
    * Widgets in the applet drawer for the applet are updated with the current operator slot values.
4) The user changes a setting in the GUI, which in turn changes a slot value on the applet's top-level operator.
    * The changes are propagated downstream from the top-level operator, possibly resulting in an update in the central widget.
    * The applet serializer also notices the change, and makes a note that the serializer is "dirty".
5) Step 4 is repeated as the user experiments with the workflow options.
6) The user selects "Save Project"
    * The shell determines which serializers have work to do by calling isDirty()
    * The shell calls serializeToHdf5 on the dirty serializers, causing them to save the current state of the corresponding top-level operators to the project file.
7) Repeat step 4 as the user experiments with more workflow options.
8) The user attempts to close the project.
    * The shell determines if any serializers have work to do by calling isDirty().  If any declare themselves dirty, the user is asked to confirm his decision to close the project.

.. currentmodule:: ilastik.applets.base.multiLaneOperator
.. autoclass:: MultiLaneOperatorABC
   :members:

Applet GUIs
===========

An applet's GUI object is responsible for providing the widgets that the shell displays when this applet is selected by the user.

Here's a screenshot of the ilastik-shell gui:

.. figure:: images/ilastik-shell.png
   :scale: 100  %
   :alt: ilastik-shell screenshot

In the following figure, the areas of the GUI are labeled according to the terminology used in the ilastik code base:

.. figure:: images/ilastik-shell-gui-areas.png
   :scale: 100  %
   :alt: ilastik-shell screenshot

An applet GUI is responsible for providing the widgets for each of the areas labeled above except for the "Current Image Menu", which is 
created by the shell.  Additionally, Applet GUIs provide any menu items that should be shown when an applet is being viewed by the user.

.. currentmodule:: ilastik.applets.base.appletGuiInterface
.. autoclass:: AppletGuiInterface
   :members:

Applet Serializers
==================

.. currentmodule:: ilastik.applets.base.appletSerializer
.. autoclass:: AppletSerializer
   :members:
   
   .. automethod:: _serializeToHdf5
   .. automethod:: _deserializeFromHdf5

Serializable Slots
==================

.. currentmodule:: ilastik.applets.base.appletSerializer
.. autoclass:: SerialSlot
   :members:

   .. automethod:: __init__
   .. automethod:: _serialize
   .. automethod:: _deserialize

.. autoclass:: SerialListSlot
   :members:

   .. automethod:: __init__

.. autoclass:: SerialBlockSlot
   :members:

   .. automethod:: __init__

.. autoclass:: SerialClassifierSlot
   :members:

   .. automethod:: __init__
   .. automethod:: _serialize
   .. automethod:: _deserialize


Applet Library
==============

Finally, the ilastik project serves as a library of applets that are useful for many workflows.
In particular, the :ref:`layer-viewer` applet is a base class that implements simple display of arbitrary slots from your top-level operator.  
It is intended to be used as a base class for almost all user-defined applets.

.. toctree::
   :maxdepth: 2

   applet_library
