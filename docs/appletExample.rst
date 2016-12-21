================================================================================
Building your own applet using the watershedSegmentation applet
================================================================================

This applet gets images for RawData, Boundaries and Seeds and 
returns the calculated watershed segmentation and the used Labels. 

More information on how you can use this applet can be found in 
`Link <http://ilastik.org/documentation/>`_ under ILASTIK WORKFLOWS.


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

#. Inheritance
   
        The Gui inherits from the WatershedLabelingGui which handles all about the labels.

        Inheritance-tree:

        LayerViewerGui->LabelingGui->WatershedLabelingGui

        More information can be found in the :ref:`watershed labeling gui <applet_labeling_gui>` section.


        The Gui uses mainly these functions:

#. setupLayers

     .. automethod:: WatershedSegmentationGui.setupLayers
     .. automethod:: WatershedSegmentationGui._initLayer

#. __init__

   Includes all the functionality that you can use with the side panel within your applet. 
   Some parts can be used of existing classes, some need to be done manually.

   * The slots for the base class for the labels are initialized here.
     Only needed for LabelingGui or WatershedLabelingGui.

     Otherwise you have to supply your own userinterface and their functionality. 


   * Handling what happens when you push a button, click on a checkbox or any other action.



.. _applet_labeling_gui:

Basic Structure in watershedLabelingGui
====================================================

The whole functionality of everything that depends on labeling 
is handled within this class. 

.. TODO explain more about this here

.. TODO explain more about the classes of LabelModelList 


