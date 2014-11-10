###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Oct 16, 2014 15:28:24 EDT$"



import os

import numpy

import PyQt4
from PyQt4 import uic, QtCore

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui

class NansheDictionaryLearningGui(LayerViewerGui):
    """
    Simple example of an applet tha  
    """
    
    ###########################################
    ### AppletGuiInterface Concrete Methods ###
    ###########################################

    def appletDrawer(self):
        return self._drawer

    # (Other methods already provided by our base class)

    ###########################################
    ###########################################
    
    def __init__(self, parentApplet, topLevelOperatorView):
        """
        """

        self.topLevelOperatorView = topLevelOperatorView
        self.ndim = 0
        super(NansheDictionaryLearningGui, self).__init__(parentApplet, self.topLevelOperatorView)

        self._register_notify_dirty()
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # Initialize the gui with the operator's current values
        self.apply_operator_settings_to_gui()

        # Add handlers for different selection events

        self._drawer.Apply.clicked.connect(self.apply_gui_settings_to_operator)

        self._drawer.NormValueSelection.currentIndexChanged.connect(self.applyNormValueSelection)

    def _register_notify_dirty(self):
        self.topLevelOperatorView.Ord.notifyDirty(self.apply_dirty_operator_settings_to_gui)

        self.topLevelOperatorView.K.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Gamma1.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Gamma2.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.NumThreads.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Batchsize.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.NumIter.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Lambda1.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Lambda2.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.PosAlpha.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.PosD.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Clean.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Mode.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.ModeD.notifyDirty(self.apply_dirty_operator_settings_to_gui)

    def _unregister_notify_dirty(self):
        self.topLevelOperatorView.Ord.unregisterDirty(self.apply_dirty_operator_settings_to_gui)

        self.topLevelOperatorView.K.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Gamma1.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Gamma2.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.NumThreads.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Batchsize.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.NumIter.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Lambda1.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Lambda2.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.PosAlpha.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.PosD.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Clean.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Mode.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.ModeD.unregisterDirty(self.apply_dirty_operator_settings_to_gui)

    def applyNormValueSelection(self, index):
        self._drawer.NormValue.setEnabled(index == 0)

    def apply_operator_settings_to_gui(self):
        self.ndim = len(self.topLevelOperatorView.InputImage.meta.shape)

        if self.topLevelOperatorView.Ord.value == -numpy.inf:
            self._drawer.NormValueSelection.setCurrentIndex(1)
            self._drawer.NormValue.setEnabled(False)
        elif self.topLevelOperatorView.Ord.value == numpy.inf:
            self._drawer.NormValueSelection.setCurrentIndex(2)
            self._drawer.NormValue.setEnabled(False)
        else:
            self._drawer.NormValueSelection.setCurrentIndex(0)
            self._drawer.NormValue.setEnabled(True)
            self._drawer.NormValue.setValue(self.topLevelOperatorView.Ord.value)

        self._drawer.KValue.setValue(self.topLevelOperatorView.K.value)
        self._drawer.Gamma1Value.setValue(self.topLevelOperatorView.Gamma1.value)
        self._drawer.Gamma2Value.setValue(self.topLevelOperatorView.Gamma2.value)
        self._drawer.NumThreadsValue.setValue(self.topLevelOperatorView.NumThreads.value)
        self._drawer.BatchsizeValue.setValue(self.topLevelOperatorView.Batchsize.value)
        self._drawer.NumIterValue.setValue(self.topLevelOperatorView.NumIter.value)
        self._drawer.Lambda1Value.setValue(self.topLevelOperatorView.Lambda1.value)
        self._drawer.Lambda2Value.setValue(self.topLevelOperatorView.Lambda2.value)
        self._drawer.PosAlphaValue.setChecked(self.topLevelOperatorView.PosAlpha.value)
        self._drawer.PosDValue.setChecked(self.topLevelOperatorView.PosD.value)
        self._drawer.CleanValue.setChecked(self.topLevelOperatorView.Clean.value)
        self._drawer.ModeValue.setValue(self.topLevelOperatorView.Mode.value)
        self._drawer.ModeDValue.setValue(self.topLevelOperatorView.ModeD.value)

    def apply_dirty_operator_settings_to_gui(self, slot, roi, **kwargs):
        self.apply_operator_settings_to_gui()

    def apply_gui_settings_to_operator(self):
        self._unregister_notify_dirty()

        if self._drawer.NormValueSelection.currentIndex() == 1:
            self._drawer.NormValue.setEnabled(False)
            self.topLevelOperatorView.Ord.setValue(-numpy.inf)
        elif self._drawer.NormValueSelection.currentIndex() == 2:
            self._drawer.NormValue.setEnabled(False)
            self.topLevelOperatorView.Ord.setValue(numpy.inf)
        else:
            self._drawer.NormValue.setEnabled(True)
            self.topLevelOperatorView.Ord.setValue(self._drawer.NormValue.value())

        self.topLevelOperatorView.K.setValue(self._drawer.KValue.value())
        self.topLevelOperatorView.Gamma1.setValue(self._drawer.Gamma1Value.value())
        self.topLevelOperatorView.Gamma2.setValue(self._drawer.Gamma2Value.value())
        self.topLevelOperatorView.NumThreads.setValue(self._drawer.NumThreadsValue.value())
        self.topLevelOperatorView.Batchsize.setValue(self._drawer.BatchsizeValue.value())
        self.topLevelOperatorView.NumIter.setValue(self._drawer.NumIterValue.value())
        self.topLevelOperatorView.Lambda1.setValue(self._drawer.Lambda1Value.value())
        self.topLevelOperatorView.Lambda2.setValue(self._drawer.Lambda2Value.value())
        self.topLevelOperatorView.PosAlpha.setValue(self._drawer.PosAlphaValue.isChecked())
        self.topLevelOperatorView.PosD.setValue(self._drawer.PosDValue.isChecked())
        self.topLevelOperatorView.Clean.setValue(self._drawer.CleanValue.isChecked())
        self.topLevelOperatorView.Mode.setValue(self._drawer.ModeValue.value())
        self.topLevelOperatorView.ModeD.setValue(self._drawer.ModeDValue.value())

        self._register_notify_dirty()

        for i in xrange(len(self.layerstack)):
            if self.layerstack[i].name == "Output":
                self.layerstack[i].visible = True
    
    def setupLayers(self):
        """
        Overridden from LayerViewerGui.
        Create a list of all layer objects that should be displayed.
        """
        layers = []

        # Show the output data
        outputImageSlot = self.topLevelOperatorView.Output
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Output"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the input data
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers
