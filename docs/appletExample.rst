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
   .. currentmodule:: ilastik.applets.layerViewer.layerViewerGui
   .. automethod:: LayerViewerGui._initLayer
   .. currentmodule:: ilastik.applets.watershedSegmentation.watershedSegmentationGui

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

The labeling gui is an applet itself, so it has a serializer, an operator and so on. 
But most of the things can be used from the superclass. 


WatershedLabelingGui inherits from LabelingGui. First of all it is sufficient to understand what happens in the LabelingGui. 


LabelingGui 
----------------------------------------------------


.. currentmodule:: ilastik.applets.labeling.labelingGui

#. In the beginning, there are lots of properties and setters. 


#.     
       .. automethod:: LabelingGui.__init__
                :noindex:
       .. automethod:: LabelingGui._initLabelUic

#. the rest is more or less the structure and methods that make this class work well, but it is not 
   so essential for the main understanding of this class.

   .. TODO maybe comment more functions and explain more about this here, 


Changes in WatershedLabelingGui compared to the LabelingGui
--------------------------------------------------------------------

All changes in the WatershedLabelingGui compared to the LabelingGui:

.. currentmodule:: ilastik.applets.watershedLabeling.watershedLabelingGui
.. autoclass:: WatershedLabelingGui
        :members: _defineModel, _changeInteractionMode, _onLabelSelected, _defineLabel, _beforeLabelRemoved, _onLabelRemoved, getNextLabelName, getNextLabelColor, getNextLabelNumber



To supply the WatershedLabelingGui with a LabelListModel that displays the value of the labels, a new class was necessary. 

.. TODO explain more about the classes of LabelModelList 

..    #TODO in doku fuer nutzung aufnehmen
        # in ws applet
    #seeds muessen 1, 2, 3 sein, also kann man auch 120 180, etc verwenden, 
    #rest aussen rum muss schwarz=0 sein
    #bei den membranen: die membrane selbst muessen 255 sein und der rest 0=schwarz
    #help(vigra.analysis.watershedsNew)
