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
#          http://ilastik.org/license.html
###############################################################################
import os
import logging
from functools import partial
from collections import OrderedDict

import numpy

import torch

from volumina.api import LazyflowSource, AlphaModulatedLayer
from volumina.utility import PreferencesManager

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QStackedWidget, QMessageBox, QFileDialog, QMenu, QLineEdit, QDialogButtonBox, QVBoxLayout, \
     QDialog, QCheckBox

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from ilastik.config import cfg as ilastik_config

from lazyflow.classifiers import TikTorchLazyflowClassifier


logger = logging.getLogger(__name__)


class ParameterDlg(QDialog):
    """
    simple window for setting parameters
    """
    def __init__(self, topLevelOperator, parent):
        super(QDialog, self).__init__(parent=parent)

        self.topLevelOperator = topLevelOperator

        buttonbox = QDialogButtonBox(Qt.Horizontal, parent=self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.add_Parameters)
        buttonbox.rejected.connect(self.reject)

        self.halo_edit = QLineEdit(self)
        self.halo_edit.setPlaceholderText("HaloSize")
        self.batch_edit = QLineEdit(self)
        self.batch_edit.setPlaceholderText("Batch Size")

        layout = QVBoxLayout()
        layout.addWidget(self.halo_edit)
        layout.addWidget(self.batch_edit)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        self.setWindowTitle("Set Parameters")


    def add_Parameters(self):
        """
        changning Halo Size and Batch Size Slot Values
        """

        halo_size = int(self.halo_edit.text())
        batch_size = int(self.batch_edit.text())

        self.topLevelOperator.Halo_Size.setValue(halo_size)
        self.topLevelOperator.Batch_Size.setValue(batch_size)

        #close dialog
        super(ParameterDlg, self).accept()


class SavingDlg(QDialog):
    """
    Saving Option Dialog
    """
    def __init__(self, topLevelOperator, parent):
        super(QDialog, self).__init__(parent=parent)

        self.topLevelOperator = topLevelOperator

        buttonbox = QDialogButtonBox(Qt.Horizontal, parent=self)
        buttonbox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.change_state)
        buttonbox.rejected.connect(self.reject)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.topLevelOperator.SaveFullModel.value)
        self.checkbox.setCheckable(True)
        self.checkbox.setText("Enable Model Object serialization")

        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(buttonbox)

        self.setLayout(layout)
        self.setWindowTitle("Saving Options")

    def change_state(self):

        self.topLevelOperator.SaveFullModel.setValue(self.checkbox.isChecked())

        #close dialog
        super(SavingDlg, self).accept()


class NNClassGui(LayerViewerGui):
    """
    LayerViewerGui class for Neural Network Classification
    """

    def viewerControlWidget(self):
        """
        Return the widget that controls how the content of the central widget is displayed
        """
        return self._viewerControlUi

    def centralWidget(self):
        """
        Return the widget that will be displayed in the main viewer area.
        """
        return self

    def stopAndCleanUp(self):
        """
        The gui should stop updating all data views and should clean up any resources it created
        """
        for fn in self.__cleanup_fns:
            fn()

    def menus(self):
        """
        Return a list of QMenu widgets to be shown in the menu bar when this applet is visible
        """
        menus = super(NNClassGui, self).menus()

        advanced_menu = QMenu("Advanced", parent=self)

        def settingParameter():
            """
            changing BatchSize and HaloSize
            """
            dlg = ParameterDlg(self.topLevelOperator, parent=self)
            dlg.exec_()

            # classifier_key = self.drawer.comboBox.currentText()
            self.halo_size = self.topLevelOperator.Halo_Size.value
            self.batch_size = self.topLevelOperator.Batch_Size.value
            print(self.halo_size)

        set_parameter = advanced_menu.addAction("Parameters...")
        set_parameter.triggered.connect(settingParameter)

        def serializing_options():
            """
            enable/disable serialization options
            """
            dlg = SavingDlg(self.topLevelOperator, parent=self)
            dlg.exec_()

            if self.topLevelOperator.SaveFullModel.value == True:
                obj_list = []
                # print(list(self.topLevelOperator.ModelPath.value.values())[0])
                # object_ = torch.load(list(self.topLevelOperator.ModelPath.value.values())[0])
                for key in self.topLevelOperator.ModelPath.value:
                    object_ = torch.load(self.topLevelOperator.ModelPath.value[key])
                    obj_list.append(object_)

                self.topLevelOperator.FullModel.setValue(obj_list)


        advanced_menu.addAction("Saving Options").triggered.connect(serializing_options)
        

        menus += [advanced_menu]

        return menus    

    def appletDrawer(self):
        """
        Return the drawer widget for this applet
        """
        return self.drawer

    def __init__(self, parentApplet, topLevelOperator):
        super(NNClassGui, self).__init__(parentApplet, topLevelOperator)

        self.parentApplet = parentApplet
        self.drawer = None
        self.topLevelOperator = topLevelOperator
        self.classifiers = OrderedDict()

        self.__cleanup_fns = []

        self._initAppletDrawerUic()
        self.initViewerControls()
        self.initViewerControlUi() 

        self.batch_size = self.topLevelOperator.Batch_Size.value
        self.halo_size = self.topLevelOperator.Halo_Size.value

    def _initAppletDrawerUic(self, drawerPath=None):
        """
        Load the ui file for the applet drawer, which we own.
        """
        if drawerPath is None:
            localDir = os.path.split(__file__)[0]
            drawerPath = os.path.join(localDir, "nnClassAppletUiTest.ui")
        self.drawer = uic.loadUi(drawerPath)

        self.drawer.comboBox.clear()
        self.drawer.liveUpdateButton.clicked.connect(self.pred_nn)
        self.drawer.addModel.clicked.connect(self.addModels)

        if self.topLevelOperator.ModelPath.ready():

            self.drawer.comboBox.clear()
            self.drawer.comboBox.addItems(self.topLevelOperator.ModelPath.value)

            self.classifiers = self.topLevelOperator.ModelPath.value

    def initViewerControls(self):
        """
        initializing viewerControl
        """
        self._viewerControlWidgetStack = QStackedWidget(parent=self)


    def initViewerControlUi(self):
        """
        Load the viewer controls GUI, which appears below the applet bar.
        In our case, the viewer control GUI consists mainly of a layer list.
        """
        localDir = os.path.split(__file__)[0]
        self._viewerControlUi = uic.loadUi(os.path.join(localDir, "viewerControls.ui"))

        def nextCheckState(checkbox):
            """
            sets the checkbox to the next state
            """
            checkbox.setChecked(not checkbox.isChecked())
        self._viewerControlUi.checkShowPredictions.nextCheckState = partial(nextCheckState, self._viewerControlUi.checkShowPredictions)

        self._viewerControlUi.checkShowPredictions.clicked.connect(self.handleShowPredictionsClicked)

        model = self.editor.layerStack
        self._viewerControlUi.viewerControls.setupConnections(model)



    def setupLayers(self):
        """
        which layers will be shown in the layerviewergui.
        Triggers the prediciton by setting the layer on visible
        """

        inputSlot = self.topLevelOperator.InputImage

        layers = []

        for channel, predictionSlot in enumerate(self.topLevelOperator.PredictionProbabilityChannels):
            if predictionSlot.ready():
                predictsrc = LazyflowSource(predictionSlot)
                predictionLayer = AlphaModulatedLayer(predictsrc, range=(0.0, 1.0), normalize=(0.0, 1.0))
                predictionLayer.visible = self.drawer.liveUpdateButton.isChecked()
                predictionLayer.opacity = 0.25
                predictionLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                def setPredLayerName(n, predictLayer_=predictionLayer, initializing=False):
                    """
                    function for setting the names for every Channel
                    """
                    if not initializing and predictLayer_ not in self.layerstack:
                        # This layer has been removed from the layerstack already.
                        # Don't touch it.
                        return
                    newName = "Prediction for %s" % n
                    predictLayer_.name = newName

                setPredLayerName(channel, initializing=True)

                layers.append(predictionLayer)

        # always as last layer
        if inputSlot.ready():
            rawLayer = self.createStandardLayerFromSlot(inputSlot)
            rawLayer.visible = True
            rawLayer.opacity = 1.0
            rawLayer.name = "Raw Data (display only)"
            layers.append(rawLayer)


        return layers


    def add_NN_classifiers(self, filename):
        """
        Adds the chosen FilePath to the classifierDictionary and to the ComboBox
        """

        #split path string
        modelname = os.path.basename(os.path.normpath(filename[0]))

        print(filename)
        print(filename[0])

        #Statement for importing the same classifier twice
        if modelname in self.classifiers.keys():
            print("Classifier already added")
            QMessageBox.critical(self, "Error loading file", "{} already added".format(modelname))
        else:

            #serialization problems because of group names when using the classifier function as value
            # self.classifiers[modelname] = TikTorchLazyflowClassifier(None, filename[0], halo_size, batch_size)

            #workAround
            self.classifiers[modelname] = filename[0]

            #clear first the comboBox or addItems will duplicate names
            self.drawer.comboBox.clear()
            self.drawer.comboBox.addItems(self.classifiers)

            if self.topLevelOperator.SaveFullModel.value  == True:
                object_ = torch.load(filename[0])
                self.topLevelOperator.FullModel.setValue(object_)

            else:
                self.topLevelOperator.ModelPath.setValue(self.classifiers)


    def pred_nn(self):
        """
        When LivePredictionButton is clicked.
        Sets the ClassifierSlotValue for Prediction.
        Updates the SetupLayers function
        """
        classifier_key = self.drawer.comboBox.currentText()
        classifier_index = self.drawer.comboBox.currentIndex()

        if len(classifier_key) == 0:
            QMessageBox.critical(self, "Error loading file", "Add a Model first")

        else:

            if self.drawer.liveUpdateButton.isChecked():

                if self.topLevelOperator.FullModel.value:
                    #if the full model object is serialized
                    model_object = self.topLevelOperator.FullModel.value[classifier_index]
                    print(classifier_index)
                    model_path = None
                else:
                    model_object = None
                    model_path = self.classifiers[classifier_key]

                self.topLevelOperator.FreezePredictions.setValue(False)

                print(self.halo_size)

                model = TikTorchLazyflowClassifier(model_object, model_path,
                 self.halo_size, self.batch_size)

                expected_input_shape = model._tiktorch_net.expected_input_shape
                input_shape = numpy.array(expected_input_shape)

                if 'output_size' in model._tiktorch_net._configuration:
                    output_shape = model._tiktorch_net.get('output_size')
                    if (output_shape != input_shape):
                        self.halo_size = int((input_shape[1] - output_shape[1])/2)
                        model.HALO_SIZE = self.halo_size
                        print(self.halo_size)


                if len(model._tiktorch_net.get('window_size')) == 2:
                    input_shape = numpy.append(input_shape, None)
                else:

                    input_shape = input_shape[1:]
                    input_shape = numpy.append(input_shape, None)

                input_shape[1:3] -= 2 * self.halo_size

                self.topLevelOperator.BlockShape.setValue(input_shape)
                self.topLevelOperator.NumClasses.setValue(model._tiktorch_net.get('num_output_channels'))

                self.topLevelOperator.Classifier.setValue(model)

                self.updateAllLayers()
                self.parentApplet.appletStateUpdateRequested()

            else:
                #when disabled, the user can scroll around without predicting
                self.topLevelOperator.FreezePredictions.setValue(True)
                self.parentApplet.appletStateUpdateRequested()


    @pyqtSlot()
    def handleShowPredictionsClicked(self):
        """
        sets the layer visibility when showPredicition is clicked
        """
        checked = self._viewerControlUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked

    @pyqtSlot()
    def updateShowPredictionCheckbox(self):
        """
        updates the showPrediction Checkbox when Predictions were added to the layers
        """
        predictLayerCount = 0
        visibleCount = 0
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                predictLayerCount += 1
                if layer.visible:
                    visibleCount += 1

        if visibleCount == 0:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Unchecked)
        elif predictLayerCount == visibleCount:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.Checked)
        else:
            self._viewerControlUi.checkShowPredictions.setCheckState(Qt.PartiallyChecked)


    def addModels(self):
        """
        When AddModels button is clicked.
        """
        mostRecentImageFile = PreferencesManager().get('DataSelection', 'recent models')
        mostRecentImageFile = str(mostRecentImageFile)
        if mostRecentImageFile is not None:
            defaultDirectory = os.path.split(mostRecentImageFile)[0]
        else:
            defaultDirectory = os.path.expanduser('~')

        fileNames = self.getImageFileNamesToOpen(self, defaultDirectory)

        if len(fileNames) > 0:
            self.add_NN_classifiers(fileNames)


    def getImageFileNamesToOpen(cls, parent_window, defaultDirectory):
        """
        opens a QFileDialog for importing files
        """
        extensions = ['nn']
        filter_strs = ["*." + x for x in extensions]
        filters = ["{filt} ({filt})".format(filt=x) for x in filter_strs]
        filt_all_str = "Image files (" + ' '.join(filter_strs) + ')'

        fileNames = []

        if ilastik_config.getboolean("ilastik", "debug"):
            # use Qt dialog in debug mode (more portable?)
            file_dialog = QFileDialog(parent_window, "Select Model")
            file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
            # do not display file types associated with a filter
            # the line for "Image files" is too long otherwise
            file_dialog.setNameFilters([filt_all_str] + filters)
            #file_dialog.setNameFilterDetailsVisible(False)
            # select multiple files
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            file_dialog.setDirectory(defaultDirectory)

            if file_dialog.exec_():
                fileNames = file_dialog.selectedFiles()
        else:
            # otherwise, use native dialog of the present platform
            fileNames, _ = QFileDialog.getOpenFileNames(parent_window, "Select Model", defaultDirectory, filt_all_str)

        return fileNames



