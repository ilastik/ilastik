================================================================================
Building your own applet: appletExample
================================================================================

Basic Structure
========================================

Example used from wsdt.

Then create a folder in 
ilastik/applets/
with the name appletExample:
In this directory there are 5 files:
#. __init__.py
#. appletExampleApplet.py
#. appletExampleGui.py
#. appletExampleSerializer.py
#. opAppletExample.py

__init__.py:

.. literalinclude:: ../ilastik/applets/appletExample/__init__.py
    :linenos:
    :language: python

The lines marked with TODO should be replaced for a new applet.
There you can include the desired applets.

For an additional widget that shall be seen for this specific applet, 
you can use the following files in volumina/volumina/widgets:

TODO create these two files

#. appletExampleWidget.py
#. ui/appletExampleWidget.ui

