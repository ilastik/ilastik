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
import os

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
            
    def initAppletDrawerUi(self):
        # Load the ui file (find it in our own directory)
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")

        # Initialize the gui with the operator's current values
        self.apply_operator_settings_to_gui()
        self._drawer.Apply.clicked.connect(self.apply_gui_settings_to_operator)

    def apply_operator_settings_to_gui(self):
        self.ndim = len(self.topLevelOperatorView.InputImage.meta.shape)

        if not isinstance(self.topLevelOperatorView.Scale.value, (list, tuple)):
            self.topLevelOperatorView.Scale.setValue(self.ndim*[self.topLevelOperatorView.Scale.value])

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
            self._drawer.TemporalSmoothingValue.setValue(self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.value)
            self._drawer.SpatialSmoothingValue.setValue(self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.value)

            if self.topLevelOperatorView.Bias.ready():
                self._drawer.BiasEnabled.setChecked(True)
                self._drawer.BiasValue.setEnabled(True)
                self._drawer.BiasValue.setValue(self.topLevelOperatorView.Bias.value)
            else:
                self._drawer.BiasEnabled.setChecked(False)
                self._drawer.BiasValue.setEnabled(False)
                self._drawer.BiasValue.setValue(0)


            self._drawer.WaveletTransformEnabled.setChecked(self.topLevelOperatorView.ToWaveletTransform.value)
            self._drawer.ScaleValue_T.setValue(self.topLevelOperatorView.Scale.value[0])
            self._drawer.ScaleValue_Y.setValue(self.topLevelOperatorView.Scale.value[1])
            self._drawer.ScaleValue_X.setValue(self.topLevelOperatorView.Scale.value[2])


            self._drawer.NormValue.setValue(self.topLevelOperatorView.Ord.value)

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
            self._drawer.TemporalSmoothingValue.setValue(self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.value)
            self._drawer.SpatialSmoothingValue.setValue(self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.value)

            if self.topLevelOperatorView.Bias.ready():
                self._drawer.BiasEnabled.setChecked(True)
                self._drawer.BiasValue.setEnabled(True)
                self._drawer.BiasValue.setValue(self.topLevelOperatorView.Bias.value)
            else:
                self._drawer.BiasEnabled.setChecked(False)
                self._drawer.BiasValue.setEnabled(False)


            self._drawer.WaveletTransformEnabled.setChecked(self.topLevelOperatorView.ToWaveletTransform.value)
            self._drawer.ScaleValue_T.setValue(self.topLevelOperatorView.Scale.value[0])
            self._drawer.ScaleValue_Z.setValue(self.topLevelOperatorView.Scale.value[1])
            self._drawer.ScaleValue_Y.setValue(self.topLevelOperatorView.Scale.value[2])
            self._drawer.ScaleValue_X.setValue(self.topLevelOperatorView.Scale.value[3])


            self._drawer.NormValue.setValue(self.topLevelOperatorView.Ord.value)

    def apply_gui_settings_to_operator(self):
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
            self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.setValue(self._drawer.TemporalSmoothingValue.value())
            self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.setValue(self._drawer.SpatialSmoothingValue.value())

            if self._drawer.BiasEnabled.isChecked():
                self._drawer.BiasValue.setEnabled(True)
                self.topLevelOperatorView.Bias.setValue(self._drawer.BiasValue.value())
            else:
                self._drawer.BiasValue.setEnabled(False)
                self.topLevelOperatorView.Bias.setValue(None)


            self.topLevelOperatorView.ToWaveletTransform.setValue(self._drawer.WaveletTransformEnabled.isChecked())
            self.topLevelOperatorView.Scale.setValue([self._drawer.ScaleValue_T.value(), self._drawer.ScaleValue_Y.value(), self._drawer.ScaleValue_X.value()])


            self.topLevelOperatorView.Ord.setValue(self._drawer.NormValue.value())

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
            self.topLevelOperatorView.TemporalSmoothingGaussianFilterStdev.setValue(self._drawer.TemporalSmoothingValue.value())
            self.topLevelOperatorView.SpatialSmoothingGaussianFilterStdev.setValue(self._drawer.SpatialSmoothingValue.value())

            if self._drawer.BiasEnabled.isChecked():
                self._drawer.BiasValue.setEnabled(True)
                self.topLevelOperatorView.Bias.setValue(self._drawer.BiasValue.value())
            else:
                self._drawer.BiasValue.setEnabled(False)
                self.topLevelOperatorView.Bias.setValue(None)


            self.topLevelOperatorView.ToWaveletTransform.setValue(self._drawer.WaveletTransformEnabled.isChecked())
            self.topLevelOperatorView.Scale.setValue([self._drawer.ScaleValue_T.value(), self._drawer.ScaleValue_Z.value(), self._drawer.ScaleValue_Y.value(), self._drawer.ScaleValue_X.value()])


            self.topLevelOperatorView.Ord.setValue(self._drawer.NormValue.value())
    
    def setupLayers(self):
        """
        Overridden from LayerViewerGui.
        Create a list of all layer objects that should be displayed.
        """
        layers = []
        
        # Show the raw input data
        inputImageSlot = self.topLevelOperatorView.InputImage
        if inputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputImageSlot )
            inputLayer.name = "Raw Input"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        # Show the raw input data
        outputImageSlot = self.topLevelOperatorView.Output
        if outputImageSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( outputImageSlot )
            inputLayer.name = "Output"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)

        return layers
