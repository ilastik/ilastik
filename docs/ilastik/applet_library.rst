==============
Applet Library
==============

Example Applets
===============

These applets aren't very useful, but they have simple, clean implementations.
Their source files are the right place to look if you're just getting started.

Threshold Masking
-----------------

.. figure:: images/ThresholdMasking-Top-Level-Operator.svg
   :scale: 100  %
   :alt: Threshold Masking Top-Level Operator

.. currentmodule:: ilastik.applets.thresholdMasking.thresholdMaskingApplet
.. autoclass:: ThresholdMaskingApplet
   :members:

Deviation From Mean
-------------------

.. figure:: images/DeviationFromMean-Top-Level-Operator.svg
   :scale: 100  %
   :alt: Deviation-From-Mean Top-Level Operator

.. currentmodule:: ilastik.applets.deviationFromMean.deviationFromMeanApplet
.. autoclass:: DeviationFromMeanApplet
   :members:

Useful Base Classes
===================

Many applets or applet GUIs are based on these classes.

.. _layer-viewer:

Layer Viewer
------------

.. figure:: images/LayerViewer-Top-Level-Operator.svg
   :scale: 100  %
   :alt: LayerViewer Top-Level Operator

.. currentmodule:: ilastik.applets.layerViewer.layerViewerApplet
.. autoclass:: LayerViewerApplet
   :members:

.. currentmodule:: ilastik.applets.layerViewer.opLayerViewer
.. autoclass:: OpLayerViewer
   :members:
   
.. currentmodule:: ilastik.applets.layerViewer.layerViewerGui
.. autoclass:: LayerViewerGui
   :members:
   
   .. automethod:: __init__

Labeling
--------

.. figure:: images/Labeling-Top-Level-Operator.svg
   :scale: 100  %
   :alt: Labeling Top-Level Operator

.. currentmodule:: ilastik.applets.labeling.labelingApplet
.. autoclass:: LabelingApplet
   :members:

.. currentmodule:: ilastik.applets.labeling.opLabeling

.. autoclass:: OpLabelingSingleLane
   :members:

.. autoclass:: OpLabelingTopLevel
   :members:

.. currentmodule:: ilastik.applets.labeling.labelingGui
.. autoclass:: LabelingGui
   :members:
   
   .. automethod:: __init__

Standard Applets
================

These applets are likely to be re-used in many, if not most, worklows.

Data Selection
--------------

.. figure:: images/DataSelection-Top-level-Operator.svg
   :scale: 100  %
   :alt: DataSelection Top-Level Operator

.. currentmodule:: ilastik.applets.dataSelection.dataSelectionApplet
.. autoclass:: DataSelectionApplet
   :members:

.. currentmodule:: ilastik.applets.dataSelection.opDataSelection
.. autoclass:: OpDataSelection
   :members:

Batch Output
------------

.. figure:: images/BatchOutput-Top-Level-Operator.svg
   :scale: 100  %
   :alt: Batch Output Top-Level Operator

.. currentmodule:: ilastik.applets.batchIo.batchIoApplet
.. autoclass:: BatchIoApplet
   :members:


Workflow-specific Applets
=========================

These applets were designed with particular workflows in mind, but they could be used with future workflows, too.

Feature Selection
-----------------

.. figure:: images/Wrapped-OpFeatureSelection.svg
   :scale: 100  %
   :alt: Feature Selection Top-Level Operator

.. currentmodule:: ilastik.applets.featureSelection.featureSelectionApplet
.. autoclass:: FeatureSelectionApplet
   :members:

Pixel Classification
--------------------

.. figure:: images/opPixelClassification.svg
   :scale: 100  %
   :alt: Pixel Classification Top-Level Operator

.. figure:: images/OpPixelClassification_detailed.png
   :scale: 20 %
   :alt: Pixel Classification Top-Level Operator

.. currentmodule:: ilastik.applets.pixelClassification.pixelClassificationApplet
.. autoclass:: PixelClassificationApplet
   :members:

Object Extraction
-----------------

The object extraction applet takes as input a data image and an object
mask. It then computes object features on the objects and makes them
available to downstream applets.

The available features are provided by a plugin system. Each plugin
reports the names of the features it supports, and handles the actual
calculation. The GUI queries all plugins for the features they provide
and present them to the user. The user selects some features, and the
selection is sent to the operator, which calls the appropriate plugins
and aggregates the results. A detailed example of a user-defined plugin 
with object features can be found in the $ILASTIK/examples directory. 
To get your plugins discovered by ilastik, you have to add their path 
to the .ilastikrc file in your home directory. The file should look
as follows:
    [ilastik]
    
    plugin_directories: /path/to/cool_features

The cool_features directory in this case should contain the .py and the .yapsy-plugin files.

.. currentmodule:: ilastik.applets.objectExtraction.objectExtractionApplet
.. autoclass:: ObjectExtractionApplet
   :members:

.. currentmodule:: ilastik.plugins
.. autoclass:: ObjectFeaturesPlugin
   :members:

.. currentmodule:: ilastik.applets.objectExtraction.opObjectExtraction
.. autoclass:: OpObjectExtraction
   :members:

.. autoclass:: OpAdaptTimeListRoi
   :members:

.. autoclass:: OpCachedRegionFeatures
   :members:

.. autoclass:: OpRegionFeatures
   :members:

.. autoclass:: OpRegionFeatures3d
   :members:

.. autoclass:: OpObjectCenterImage
   :members:


Object Classification
---------------------

The object classification applet provides functionality for labeling
objects, training a classifier, and visualizing the prediction
results. The top-level operator receives connected component images
and object features from upstream operators, and it receives object
labels from the object classification GUI. In addition to providing
the usual output slots for classification, such as probabilities and
predictions for each object, it also provides warnings for bad objects
(i.e., those with missing or mangled features).

.. currentmodule:: ilastik.applets.objectClassification.objectClassificationApplet
.. autoclass:: ObjectClassificationApplet
   :members:

.. currentmodule:: ilastik.applets.objectClassification.opObjectClassification
.. autoclass:: OpObjectClassification
   :members:

.. autoclass:: OpObjectTrain
   :members:

.. autoclass:: OpObjectPredict
   :members:

.. autoclass:: OpRelabelSegmentation
   :members:

.. autoclass:: OpMultiRelabelSegmentation
   :members:

.. autoclass:: OpMaxLabel
   :members:

.. currentmodule:: ilastik.applets.objectClassification.objectClassificationGui
.. autoclass:: ObjectClassificationGui
   :members:


