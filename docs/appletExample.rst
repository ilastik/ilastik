================================================================================
Building your own applet using the watershedSegmentation applet
================================================================================

Basic File Structure
========================================

#. __init__.py

        .. literalinclude:: ../ilastik/applets/watershedSegmentation/__init__.py
           :linenos:
           :language: python

#. opWatershedSegmentation.py

   * This file includes the InputSlots and OutputSlots and how they are used internally. 

   * The main calculations can be found here as well.

   * more Information, how you can implement or use operators can be looked up in the lazyflow 
     documentation under the point of 'operator overview' and 'advanced concepts' 
     which is worth reading for a better understanding

#. watershedSegmentationApplet.py

   * Handles what happens when the applet is created. 

   * Mainly only the function broadcastingSlots should be changed, in particular only the return value. 
     Look at the function description for more information.

     .. currentmodule:: ilastik.applets.watershedSegmentation.watershedSegmentationApplet
     .. autoattribute:: WatershedSegmentationApplet.broadcastingSlots


#. watershedSegmentationSerializer.py

   * Handles which OutputSlots shall be serialized. This means, that these slots have the same content
     after project restart. 
   
   * For more information see the following documentation and the code and the comments in its __init__ function.

     .. currentmodule:: ilastik.applets.watershedSegmentation.watershedSegmentationSerializer
     .. autoclass:: WatershedSegmentationSerializer
             :members: __init__


#. watersehdSegmentationGui.py

   * handles the graphical user interface and the slots, that are 

   * handles the views of the layer

   * this file is discussed in more detail in :ref:`the Gui <applet_gui>`.


#. addtional files:
   Normally these files above are sufficient. Sometimes classes or cached versions of operators are 
   excluded into addtional files. This is only for a better overview and maintenance.


.. _applet_gui:

Basic Structure in watershedSegmentationGui
====================================================

.. currentmodule:: ilastik.applets.watershedSegmentation.watershedSegmentationGui

The Gui uses mainly these functions:

#. setupLayers

     .. automethod:: WatershedSegmentationGui.setupLayers
     .. automethod:: WatershedSegmentationGui._initLayer





Basic Structure
========================================
.. TODO



For an additional widget that shall be seen for this specific applet, 
you can use the following files in volumina/volumina/widgets:

TODO create these two files

#. appletExampleWidget.py
#. ui/appletExampleWidget.ui

