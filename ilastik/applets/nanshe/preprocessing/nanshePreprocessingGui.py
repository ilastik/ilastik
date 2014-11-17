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

class NanshePreprocessingGui(LayerViewerGui):
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
        super(NanshePreprocessingGui, self).__init__(parentApplet, self.topLevelOperatorView)

        self._register_notify_dirty()
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # Add handlers for different selection events

        self._drawer.Apply.clicked.connect(self.apply_gui_settings_to_operator)

        self.applyRemoveZeroedLinesEnabled(self.topLevelOperatorView.ToRemoveZeroedLines.value)
        self._drawer.RemoveZeroedLinesEnabled.clicked.connect(self.applyRemoveZeroedLinesEnabled)

        self.applyExtractF0Enabled(self.topLevelOperatorView.ToExtractF0.value)
        self._drawer.ExtractF0Enabled.clicked.connect(self.applyExtractF0Enabled)

        self.applyBiasEnabled(self.topLevelOperatorView.BiasEnabled.value)
        self._drawer.BiasEnabled.clicked.connect(self.applyBiasEnabled)

        self.applyWaveletTransformEnabled(self.topLevelOperatorView.ToWaveletTransform.value)
        self._drawer.WaveletTransformEnabled.clicked.connect(self.applyWaveletTransformEnabled)

        # Initialize the gui with the operator's current values
        self.apply_operator_settings_to_gui()

    def _register_notify_dirty(self):
        self.topLevelOperatorView.ToRemoveZeroedLines.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.ErosionShape.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.DilationShape.notifyDirty(self.apply_dirty_operator_settings_to_gui)

        self.topLevelOperatorView.ToExtractF0.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.HalfWindowSize.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.WhichQuantile.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.notifyDirty(
            self.apply_dirty_operator_settings_to_gui
        )
        self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.notifyDirty(
            self.apply_dirty_operator_settings_to_gui
        )
        self.topLevelOperatorView.BiasEnabled.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Bias.notifyDirty(self.apply_dirty_operator_settings_to_gui)

        self.topLevelOperatorView.ToWaveletTransform.notifyDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Scale.notifyDirty(self.apply_dirty_operator_settings_to_gui)

    def _unregister_notify_dirty(self):
        self.topLevelOperatorView.ToRemoveZeroedLines.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.ErosionShape.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.DilationShape.unregisterDirty(self.apply_dirty_operator_settings_to_gui)

        self.topLevelOperatorView.ToExtractF0.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.HalfWindowSize.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.WhichQuantile.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.unregisterDirty(
            self.apply_dirty_operator_settings_to_gui
        )
        self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.unregisterDirty(
            self.apply_dirty_operator_settings_to_gui
        )
        self.topLevelOperatorView.BiasEnabled.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Bias.unregisterDirty(self.apply_dirty_operator_settings_to_gui)

        self.topLevelOperatorView.ToWaveletTransform.unregisterDirty(self.apply_dirty_operator_settings_to_gui)
        self.topLevelOperatorView.Scale.unregisterDirty(self.apply_dirty_operator_settings_to_gui)

    def applyRemoveZeroedLinesEnabled(self, checked):
        self._drawer.ErosionShapeValue_Z.setEnabled(checked)
        self._drawer.ErosionShapeValue_Y.setEnabled(checked)
        self._drawer.ErosionShapeValue_X.setEnabled(checked)

        self._drawer.DilationShapeValue_Z.setEnabled(checked)
        self._drawer.DilationShapeValue_Y.setEnabled(checked)
        self._drawer.DilationShapeValue_X.setEnabled(checked)

    def applyExtractF0Enabled(self, checked):
        self._drawer.HalfWindowSizeValue.setEnabled(checked)
        self._drawer.QuantileValue.setEnabled(checked)
        self._drawer.TemporalSmoothingStdevValue.setEnabled(checked)
        self._drawer.TemporalSmoothingWindowSizeValue.setEnabled(checked)
        self._drawer.SpatialSmoothingStdevValue.setEnabled(checked)
        self._drawer.SpatialSmoothingWindowSizeValue.setEnabled(checked)
        self._drawer.BiasEnabled.setEnabled(checked)
        self._drawer.BiasValue.setEnabled(checked and self._drawer.BiasEnabled.isChecked())

    def applyBiasEnabled(self, checked):
        self._drawer.BiasValue.setEnabled(checked)

    def applyWaveletTransformEnabled(self, checked):
        self._drawer.ScaleValue_T.setEnabled(checked)
        self._drawer.ScaleValue_Z.setEnabled(checked)
        self._drawer.ScaleValue_Y.setEnabled(checked)
        self._drawer.ScaleValue_X.setEnabled(checked)

    def apply_operator_settings_to_gui(self):
        self.ndim = len(self.topLevelOperatorView.InputImage.meta.shape)

        self._unregister_notify_dirty()

        if not isinstance(self.topLevelOperatorView.Scale.value, (list, tuple)):
            self.topLevelOperatorView.Scale.setValue(self.ndim*[self.topLevelOperatorView.Scale.value])
        elif len(self.topLevelOperatorView.Scale.value) == 1:
            self.topLevelOperatorView.Scale.setValue(self.ndim*[self.topLevelOperatorView.Scale.value[0]])

        self._register_notify_dirty()

        assert(4 <= self.ndim <= 5)

        if self.ndim == 4:
            self._drawer.ErosionShapeValue_Z.hide()
            self._drawer.DilationShapeValue_Z.hide()
            self._drawer.ScaleValue_Z.hide()

            self._drawer.ErosionShapeLabel.setText(self._drawer.ErosionShapeLabel.text().replace("Z, ", ""))
            self._drawer.DilationShapeLabel.setText(self._drawer.DilationShapeLabel.text().replace("Z, ", ""))
            self._drawer.ScaleLabel.setText(self._drawer.ScaleLabel.text().replace("Z, ", ""))


            self._drawer.RemoveZeroedLinesEnabled.setChecked(self.topLevelOperatorView.ToRemoveZeroedLines.value)

            self._drawer.ErosionShapeValue_Y.setValue(self.topLevelOperatorView.ErosionShape.value[0])
            self._drawer.ErosionShapeValue_X.setValue(self.topLevelOperatorView.ErosionShape.value[1])

            self._drawer.DilationShapeValue_Y.setValue(self.topLevelOperatorView.DilationShape.value[0])
            self._drawer.DilationShapeValue_X.setValue(self.topLevelOperatorView.DilationShape.value[1])


            self._drawer.ExtractF0Enabled.setChecked(self.topLevelOperatorView.ToExtractF0.value)

            self._drawer.HalfWindowSizeValue.setValue(self.topLevelOperatorView.HalfWindowSize.value)
            self._drawer.QuantileValue.setValue(self.topLevelOperatorView.WhichQuantile.value)
            self._drawer.TemporalSmoothingStdevValue.setValue(self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.value)
            self._drawer.TemporalSmoothingWindowSizeValue.setValue(self.topLevelOperatorView.TemporalSmoothingGaussianFilterWindowSize.value)
            self._drawer.SpatialSmoothingStdevValue.setValue(self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.value)
            self._drawer.SpatialSmoothingWindowSizeValue.setValue(self.topLevelOperatorView.SpatialSmoothingGaussianFilterWindowSize.value)

            self._drawer.BiasValue.setValue(self.topLevelOperatorView.Bias.value)

            self._drawer.WaveletTransformEnabled.setChecked(self.topLevelOperatorView.ToWaveletTransform.value)
            self._drawer.ScaleValue_T.setValue(self.topLevelOperatorView.Scale.value[0])
            self._drawer.ScaleValue_Y.setValue(self.topLevelOperatorView.Scale.value[1])
            self._drawer.ScaleValue_X.setValue(self.topLevelOperatorView.Scale.value[2])

        elif self.ndim == 5:
            self._drawer.ErosionShapeValue_Z.show()
            self._drawer.DilationShapeValue_Z.show()
            self._drawer.ScaleValue_Z.show()

            if "Z, " not in self._drawer.ErosionShapeLabel.text():
                self._drawer.ErosionShapeLabel.setText(self._drawer.ErosionShapeLabel.text().replace("Y, ", "Z, Y, "))
            if "Z, " not in self._drawer.DilationShapeLabel.text():
                self._drawer.DilationShapeLabel.setText(self._drawer.DilationShapeLabel.text().replace("Y, ", "Z, Y, "))
            if "Z, " not in self._drawer.ScaleLabel.text():
                self._drawer.ScaleLabel.setText(self._drawer.ScaleLabel.text().replace("Y, ", "Z, Y, "))


            self._drawer.RemoveZeroedLinesEnabled.setChecked(self.topLevelOperatorView.ToRemoveZeroedLines.value)

            self._drawer.ErosionShapeValue_Z.setValue(self.topLevelOperatorView.ErosionShape.value[0])
            self._drawer.ErosionShapeValue_Y.setValue(self.topLevelOperatorView.ErosionShape.value[1])
            self._drawer.ErosionShapeValue_X.setValue(self.topLevelOperatorView.ErosionShape.value[2])

            self._drawer.DilationShapeValue_Z.setValue(self.topLevelOperatorView.DilationShape.value[0])
            self._drawer.DilationShapeValue_Y.setValue(self.topLevelOperatorView.DilationShape.value[1])
            self._drawer.DilationShapeValue_X.setValue(self.topLevelOperatorView.DilationShape.value[2])


            self._drawer.ExtractF0Enabled.setChecked(self.topLevelOperatorView.ToExtractF0.value)

            self._drawer.HalfWindowSizeValue.setValue(self.topLevelOperatorView.HalfWindowSize.value)
            self._drawer.QuantileValue.setValue(self.topLevelOperatorView.WhichQuantile.value)
            self._drawer.TemporalSmoothingStdevValue.setValue(self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.value)
            self._drawer.TemporalSmoothingWindowSizeValue.setValue(self.topLevelOperatorView.TemporalSmoothingGaussianFilterWindowSize.value)
            self._drawer.SpatialSmoothingStdevValue.setValue(self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.value)
            self._drawer.SpatialSmoothingWindowSizeValue.setValue(self.topLevelOperatorView.SpatialSmoothingGaussianFilterWindowSize.value)

            self._drawer.BiasValue.setValue(self.topLevelOperatorView.Bias.value)
            if self.topLevelOperatorView.BiasEnabled.value:
                self._drawer.BiasEnabled.setChecked(True)
                self._drawer.BiasValue.setEnabled(True)
            else:
                self._drawer.BiasEnabled.setChecked(False)
                self._drawer.BiasValue.setEnabled(False)


            self._drawer.WaveletTransformEnabled.setChecked(self.topLevelOperatorView.ToWaveletTransform.value)
            self._drawer.ScaleValue_T.setValue(self.topLevelOperatorView.Scale.value[0])
            self._drawer.ScaleValue_Z.setValue(self.topLevelOperatorView.Scale.value[1])
            self._drawer.ScaleValue_Y.setValue(self.topLevelOperatorView.Scale.value[2])
            self._drawer.ScaleValue_X.setValue(self.topLevelOperatorView.Scale.value[3])

    def apply_dirty_operator_settings_to_gui(self, slot, roi, **kwargs):
        self.apply_operator_settings_to_gui()

    def apply_gui_settings_to_operator(self):
        self._unregister_notify_dirty()

        if self.ndim == 4:
            self._drawer.ErosionShapeValue_Z.hide()
            self._drawer.DilationShapeValue_Z.hide()
            self._drawer.ScaleValue_Z.hide()

            self._drawer.ErosionShapeLabel.setText(self._drawer.ErosionShapeLabel.text().replace("Z, ", ""))
            self._drawer.DilationShapeLabel.setText(self._drawer.DilationShapeLabel.text().replace("Z, ", ""))
            self._drawer.ScaleLabel.setText(self._drawer.ScaleLabel.text().replace("Z, ", ""))


            self.topLevelOperatorView.ToRemoveZeroedLines.setValue(self._drawer.RemoveZeroedLinesEnabled.isChecked())

            self.topLevelOperatorView.ErosionShape.setValue([self._drawer.ErosionShapeValue_Y.value(), self._drawer.ErosionShapeValue_X.value()])
            self.topLevelOperatorView.DilationShape.setValue([self._drawer.DilationShapeValue_Y.value(), self._drawer.DilationShapeValue_X.value()])


            self.topLevelOperatorView.ToExtractF0.setValue(self._drawer.ExtractF0Enabled.isChecked())

            self.topLevelOperatorView.HalfWindowSize.setValue(self._drawer.HalfWindowSizeValue.value())
            self.topLevelOperatorView.WhichQuantile.setValue(self._drawer.QuantileValue.value())
            self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.setValue(self._drawer.TemporalSmoothingStdevValue.value())
            self.topLevelOperatorView.TemporalSmoothingGaussianFilterWindowSize.setValue(self._drawer.TemporalSmoothingWindowSizeValue.value())
            self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.setValue(self._drawer.SpatialSmoothingStdevValue.value())
            self.topLevelOperatorView.SpatialSmoothingGaussianFilterWindowSize.setValue(self._drawer.SpatialSmoothingWindowSizeValue.value())

            self.topLevelOperatorView.Bias.setValue(self._drawer.BiasValue.value())
            if self._drawer.BiasEnabled.isChecked():
                self._drawer.BiasValue.setEnabled(True)
                self.topLevelOperatorView.BiasEnabled.setValue(True)
            else:
                self._drawer.BiasValue.setEnabled(False)
                self.topLevelOperatorView.BiasEnabled.setValue(False)


            self.topLevelOperatorView.ToWaveletTransform.setValue(self._drawer.WaveletTransformEnabled.isChecked())
            self.topLevelOperatorView.Scale.setValue([self._drawer.ScaleValue_T.value(), self._drawer.ScaleValue_Y.value(), self._drawer.ScaleValue_X.value()])

        elif self.ndim == 5:
            self._drawer.ErosionShapeValue_Z.show()
            self._drawer.DilationShapeValue_Z.show()
            self._drawer.ScaleValue_Z.show()

            if "Z, " not in self._drawer.ErosionShapeLabel.text():
                self._drawer.ErosionShapeLabel.setText(self._drawer.ErosionShapeLabel.text().replace("Y, ", "Z, Y, "))
            if "Z, " not in self._drawer.DilationShapeLabel.text():
                self._drawer.DilationShapeLabel.setText(self._drawer.DilationShapeLabel.text().replace("Y, ", "Z, Y, "))
            if "Z, " not in self._drawer.ScaleLabel.text():
                self._drawer.ScaleLabel.setText(self._drawer.ScaleLabel.text().replace("Y, ", "Z, Y, "))


            self.topLevelOperatorView.ToRemoveZeroedLines.setValue(self._drawer.RemoveZeroedLinesEnabled.isChecked())

            self.topLevelOperatorView.ErosionShape.setValue([self._drawer.ErosionShapeValue_Z.value(), self._drawer.ErosionShapeValue_Y.value(), self._drawer.ErosionShapeValue_X.value()])
            self.topLevelOperatorView.DilationShape.setValue([self._drawer.DilationShapeValue_Z.value(), self._drawer.ErosionShapeValue_Y.value(), self._drawer.DilationShapeValue_X.value()])


            self.topLevelOperatorView.ToExtractF0.setValue(self._drawer.ExtractF0Enabled.isChecked())

            self.topLevelOperatorView.HalfWindowSize.setValue(self._drawer.HalfWindowSizeValue.value())
            self.topLevelOperatorView.WhichQuantile.setValue(self._drawer.QuantileValue.value())
            self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.setValue(self._drawer.TemporalSmoothingStdevValue.value())
            self.topLevelOperatorView.TemporalSmoothingGaussianFilterWindowSize.setValue(self._drawer.TemporalSmoothingWindowSizeValue.value())
            self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.setValue(self._drawer.SpatialSmoothingStdevValue.value())
            self.topLevelOperatorView.SpatialSmoothingGaussianFilterWindowSize.setValue(self._drawer.SpatialSmoothingWindowSizeValue.value())

            self.topLevelOperatorView.Bias.setValue(self._drawer.BiasValue.value())
            if self._drawer.BiasEnabled.isChecked():
                self._drawer.BiasValue.setEnabled(True)
                self.topLevelOperatorView.BiasEnabled.setValue(True)
            else:
                self._drawer.BiasValue.setEnabled(False)
                self.topLevelOperatorView.BiasEnabled.setValue(False)


            self.topLevelOperatorView.ToWaveletTransform.setValue(self._drawer.WaveletTransformEnabled.isChecked())
            self.topLevelOperatorView.Scale.setValue([self._drawer.ScaleValue_T.value(), self._drawer.ScaleValue_Z.value(), self._drawer.ScaleValue_Y.value(), self._drawer.ScaleValue_X.value()])

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

        # Show the final result
        outputImageSlot = self.topLevelOperatorView.Output
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Output"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the result after removing line registration artifact
        outputImageSlot = self.topLevelOperatorView.OpNansheRemoveZeroedLinesOutput
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Output Remove Zeroed Lines"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the result after F_0 extraction
        outputImageSlot = self.topLevelOperatorView.OpNansheExtractF0Output
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Output Extract F_0"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the result after wavelet transform
        outputImageSlot = self.topLevelOperatorView.OpNansheWaveletTransformOutput
        if outputImageSlot.ready():
            outputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            outputLayer.name = "Output Wavelet Transform"
            outputLayer.visible = False
            outputLayer.opacity = 1.0
            layers.append(outputLayer)

        # Show the raw input data
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers
