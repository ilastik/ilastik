================================================================================
Building your own applet: appletExample
================================================================================

Basic Structure
========================================

A good example of a basic applet could watershedSegmentation, that is based on the wsdti applet.

Then create a folder in 
ilastik/applets/
with the name appletExample:
In this directory there are 5 files:
#. __init__.py

.. literalinclude:: ../ilastik/applets/appletExample/__init__.py
   :linenos:
   :language: python

#. appletExampleApplet.py
   * for initialization
   * for communication with workflow (e.g. with slotbroadcasting)
#. appletExampleGui.py
   * handles the graphical user interface and the slots, that are 
   * handles the views of the layer
#. appletExampleSerializer.py
   include here all the slots used in before, that can be used in the applet
#. opAppletExample.py
   * The algorithms are executed here

   * more Information, how you can implement or use operators can be looked up in the lazyflow 
     documentation under the point of 'operator overview' and 'advanced concepts' 
     which is worth reading for a better understanding
   




The lines marked with TODO should be replaced for a new applet.
There you can include the desired applets.

For an additional widget that shall be seen for this specific applet, 
you can use the following files in volumina/volumina/widgets:

TODO create these two files

#. appletExampleWidget.py
#. ui/appletExampleWidget.ui

