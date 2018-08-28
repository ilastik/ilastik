# -*- coding: utf-8 -*-
from __future__ import absolute_import
from builtins import range
__author__ = 'fabian'

import numpy
# import scipy
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook

from volumina.widgets import layerwidget
from volumina import volumeEditorWidget
from volumina.layer import ColortableLayer, GrayscaleLayer, RGBALayer
from volumina import colortables
from volumina.pixelpipeline.datasourcefactories import createDataSource

from ilastik.applets.pixelClassification import opPixelClassification
from lazyflow.operators import OpFeatureMatrixCache
from ilastik.utility import OpMultiLaneWrapper
from lazyflow import graph

from os import times
import re



# just a container class, nothing fancy here
class FeatureSelectionResult(object):
    def __init__(self, feature_matrix, feature_ids, segmentation, parameters, selection_method, oob_err = None, feature_calc_time = None):
        self.feature_matrix = feature_matrix
        self.segmentation = segmentation
        self.parameters = parameters
        self.selection_method = selection_method
        self.oob_err = oob_err
        self.feature_calc_time = feature_calc_time
        self.feature_ids = feature_ids


        self.name = self._create_name()
        self.long_name = self._create_long_name()

    def _create_name(self):
        """
        Returns: name for the method to be displayed in the upper right part of the dialog (layer selection)
        """

        if self.selection_method == "filter" or self.selection_method == "gini":
            if self.parameters["num_of_feat"] == 0:
                name = "%d features(auto), %s selection" % ( numpy.sum(self.feature_matrix), self.selection_method)
            else:
                name = "%d features, %s selection" % (self.parameters["num_of_feat"], self.selection_method)
        elif self.selection_method == "wrapper":
            name = "%d features, wrapper method" % numpy.sum(self.feature_matrix)
        else:
            name = self.selection_method
        return name

    def _create_long_name(self):
        """
        Returns: name for the method to be displayed in the lower left part of the dialog

        """

        if self.selection_method == "filter" or self.selection_method == "gini":
            if self.parameters["num_of_feat"] == 0:
                name = "%d features(auto), %s selection" % (numpy.sum(self.feature_matrix), self.selection_method)
            else:
                name = "%d features, %s selection" % (self.parameters["num_of_feat"], self.selection_method)
        elif self.selection_method == "wrapper":
            name = "%i features, wrapper selection, c=%1.02f" % (numpy.sum(self.feature_matrix), self.parameters["c"])
        else:
            name = self.selection_method
        if self.oob_err is not None:
            name += ", oob_error=%1.3f" % self.oob_err
        if self.feature_calc_time is not None:
            name += ", computation time=%1.3f" % self.feature_calc_time
        return name

    def change_name(self, name):
        self.name = name

    def change_long_name(self, name):
        self.long_name = name



class FeatureSelectionDialog(QtWidgets.QDialog):
    def __init__(
            self,
            current_opFeatureSelection,
            current_opPixelClassification,
            labels_list_data
        ):
        '''

        :param current_opFeatureSelection: opFeatureSelection from ilastik
        :param current_opPixelClassification: opPixelClassification form Ilastik
        '''
        super(FeatureSelectionDialog, self).__init__()

        self.opPixelClassification = current_opPixelClassification
        self.opFeatureSelection = current_opFeatureSelection

        self._init_feature_matrix = False

        # lazyflow required operator to be connected to a graph, although no interconnection takes place here
        g = graph.Graph()

        # instantiate feature selection operators
        # these operators are not connected to the ilastik lazyflow architecture.
        # Reason provided in self._run_selection()
        self.opFilterFeatureSelection = opPixelClassification.OpFilterFeatureSelection(graph=g)
        self.opWrapperFeatureSelection = opPixelClassification.OpWrapperFeatureSelection(graph=g)
        self.opGiniFeatureSelection = opPixelClassification.OpGiniFeatureSelection(graph=g)

        # retrieve the featureMatrixCaches operator from the opPixelClassification. This operator provides the features
        # and labels matrix required by the feature selection operators
        self.opFeatureMatrixCaches = self.opPixelClassification.opFeatureMatrixCaches

        '''FIXME / FixMe: the FeatureSelectionDialog will only display one slice of the dataset. This is for RAM saving
        reasons. By using only one slice, we can simple predict the segmentation of that slice for each feature set and
        store it in RAM. If we allowed to show the whole dataset, then we would have to copy the opFeatureSelection and
        opPixelClassification once for each feature set. This would result in too much feature computation time as
        well as too much RAM usage.
        However, this shortcoming could be overcome by creating something like an opFeatureSubset. Then we would enable
        all features in the opFeatureSelection and the feature sets are created by 'filtering' the output of the
        opFeatureSelection. Thereby, provided that features in the opFeatureSelection are cached (are they?) the
        features would not have to be recalculated for each feature set.'''
        self._xysliceID = -1

        self._initialized_all_features_segmentation_layer = False
        self._initialized_current_features_segmentation_layer = False
        self._initialized_feature_matrix = False

        self._selected_feature_set_id = None
        self.selected_features_matrix = self.opFeatureSelection.SelectionMatrix.value
        self.feature_channel_names = None #this gets initialized when the matrix is set to all features in _run_selection

        self._stack_dim = self.opPixelClassification.InputImages.meta.shape
        self._stack_axistags = self.opPixelClassification.InputImages.meta.axistags

        self.__selection_methods = {
            0: "gini",
            1: "filter",
            2: "wrapper"
        }

        self._selection_params = {
            "num_of_feat": 7,  #arbitrary number for the default, Ulli thinks it's good
            "c": 0.1
        }
        self._selection_method = "None"
        self._gui_initialized = False #  is set to true once gui is initialized, prevents multiple initialization
        self._feature_selection_results = []

        self.labels_list_data = labels_list_data
        self.layerstack = layerwidget.LayerStackModel()

        # this initializes the actual GUI
        self._init_gui()

        # set default parameter values
        self.number_of_feat_box.setValue(self._selection_params["num_of_feat"])
        self.spinbox_c_widget.setValue(self._selection_params["c"])

        # connect functionality
        self.cancel_button.clicked.connect(self.reject)
        self.select_set_button.clicked.connect(self.accept)
        self.select_method_cbox.currentIndexChanged.connect(self._handle_selected_method_changed)
        self.spinbox_c_widget.valueChanged.connect(self._update_parameters)
        self.number_of_feat_box.valueChanged.connect(self._update_parameters)
        self.run_button.clicked.connect(self._run_selection)
        self.all_feature_sets_combo_box.currentIndexChanged.connect(self._handle_selected_feature_set_changed)

        # make sure internal variable are in sync with gui
        self._handle_selected_method_changed()
        self._update_parameters()

        self.resize(1366, 768)

    def exec_(self):
        """
        as explained in the __init__, we only display one slice of the datastack. Here we find out which slice is

        currently being viewed in ilastik

        """
        self.colortable = [lab.pmapColor().rgba() for lab in self.labels_list_data]
        #FIXME: the editor should return the current view coordinates without such workarounds
        if self.opPixelClassification.name == "OpPixelClassification":
            ilastik_editor = self.opPixelClassification.parent.pcApplet.getMultiLaneGui().currentGui().editor
        elif self.opPixelClassification.name == "OpPixelClassification0":
            ilastik_editor = self.opPixelClassification.parent.pcApplets[0].getMultiLaneGui().currentGui().editor
        elif self.opPixelClassification.name == "OpPixelClassification1":
            ilastik_editor = self.opPixelClassification.parent.pcApplets[1].getMultiLaneGui().currentGui().editor
        else:
            raise NotImplementedError

        self._ilastik_currentslicing_5D = ilastik_editor.posModel.slicingPos5D
        #FIXME: is this always the xy scene?
        current_view = ilastik_editor.imageViews[2]
        current_viewport_rect = current_view.viewportRect().getRect()

        axistags = self.opFeatureSelection.InputImage.meta['axistags']

        x_idx = axistags.index('x')
        y_idx = axistags.index('y')
        self._xysliceID = self._ilastik_currentslicing_5D[3]  # volume editor slicings are all (t, x, y, z, c)
        self._stackdim = self.opFeatureSelection.InputImage.meta.shape

        self._bbox = {}
        if 'z' in axistags:
            self._bbox['z'] = [self._xysliceID, self._xysliceID + 1]
        if 'c' in axistags:
            self._bbox['c'] = [0, self._stackdim[axistags.index('c')]]
        if 't' in axistags:
            self._bbox['t'] = [self._ilastik_currentslicing_5D[0], self._ilastik_currentslicing_5D[0] + 1]

        self._bbox['x'] = [numpy.max([int(current_viewport_rect[0]), 0]),
                           numpy.min([int(current_viewport_rect[0] + current_viewport_rect[2]), self._stackdim[x_idx]])]
        self._bbox['y'] = [numpy.max([int(current_viewport_rect[1]), 0]),
                           numpy.min([int(current_viewport_rect[1] + current_viewport_rect[3]), self._stackdim[y_idx]])]

        self.reset_me()

        # retrieve raw data of current slice and add it to the layerstack
        total_slicing = [slice(self._bbox[ai.key][0], self._bbox[ai.key][1]) for ai in axistags]
        self.raw_xy_slice = numpy.squeeze(self.opPixelClassification.InputImages[total_slicing].wait())

        color_index = axistags.index('c')
        if self._stackdim[color_index] ==2 or self._stackdim[color_index]==3:
            #FIXME: check if the main window is displaying raw as rgba or grayscale

            # dirty workaround for swapping x/y axis (I dont know how to set axistags of new layer)
            if axistags.index('x') > axistags.index('y'):
                self.raw_xy_slice = self.raw_xy_slice.swapaxes(1, 0)
            self._add_color_layer(self.raw_xy_slice, "raw_data", True)
        else:
            # dirty workaround for swapping x/y axis (I dont know how to set axistags of new layer)
            if axistags.index('x') > axistags.index('y'):
                self.raw_xy_slice = self.raw_xy_slice.swapaxes(1, 0)
            self._add_grayscale_layer(self.raw_xy_slice, "raw_data", True)


        # now launch the dialog
        super(FeatureSelectionDialog, self).exec_()

    def reset_me(self):
        '''
        this deletes everything from the layerstack
        '''
        while(self.layerstack.removeRow(0)):
            pass
        for i in range(len(self._feature_selection_results)):
            self.all_feature_sets_combo_box.removeItem(0)
        # reset feature sets
        self._feature_selection_results = []
        self._initialized_all_features_segmentation_layer = False
        self._initialized_current_features_segmentation_layer = False
        self._initialized_feature_matrix = False
        #self.all_feature_sets_combo_box.resetInputContext()
        self._selected_feature_set_id = None

    def _init_gui(self):
        if not self._gui_initialized:
            ###################
            # Layer Widget (displays all available layers and lets the user change their visibility)
            ###################
            self.layer_widget = layerwidget.LayerWidget()
            self.layer_widget.init(self.layerstack)

            ###################
            # Instantiation of the volumeEditor (+ widget)
            ###################
            self.editor = volumeEditorWidget.VolumeEditor(self.layerstack, parent=self)
            self.volumeEditorWidget = volumeEditorWidget.VolumeEditorWidget()
            self.volumeEditorWidget.init(self.editor)

            ###################
            # This section constructs the GUI elements that are displayed on the left side of the window
            ###################
            left_side_panel = QtWidgets.QListWidget()
            left_side_layout = QtWidgets.QVBoxLayout()
            method_label = QtWidgets.QLabel("Feature Selection Method")

            # combo box for selecting desired feature selection method
            self.select_method_cbox = QtWidgets.QComboBox()
            self.select_method_cbox.addItem("Gini Importance (quick & dirty)")
            self.select_method_cbox.addItem("Filter Method (recommended)")
            self.select_method_cbox.addItem("Wrapper Method (slow but good)")
            self.select_method_cbox.setCurrentIndex(1)


            # number of selected features
            # create a widget containing 2 child widgets in a horizontal layout
            # child widgets: QLabel for text and QSpinBox for selecting an integer value for number of features
            self.number_of_features_selection_widget = QtWidgets.QWidget()

            text_number_of_feat = QtWidgets.QLabel("Number of Features (0=auto)")
            self.number_of_feat_box = QtWidgets.QSpinBox()

            number_of_features_selection_layout = QtWidgets.QHBoxLayout()
            number_of_features_selection_layout.addWidget(text_number_of_feat)
            number_of_features_selection_layout.addWidget(self.number_of_feat_box)

            self.number_of_features_selection_widget.setLayout(number_of_features_selection_layout)


            # regularization parameter for wrapper
            # create a widget containing 2 child widgets in a horizontal layout
            # child widgets: QLabel for text and QDoubleSpinBox for selecting a float value for c (parameter)
            self.c_widget = QtWidgets.QWidget()

            text_c_widget = QtWidgets.QLabel("Set Size Penalty") # not a good text
            self.spinbox_c_widget = QtWidgets.QDoubleSpinBox()
            # may have to set increment to 0.01
            self.spinbox_c_widget.setSingleStep(0.03)

            c_widget_layout = QtWidgets.QHBoxLayout()
            c_widget_layout.addWidget(text_c_widget)
            c_widget_layout.addWidget(self.spinbox_c_widget)

            self.c_widget.setLayout(c_widget_layout)

            # run button
            self.run_button = QtWidgets.QPushButton("Run Feature Selection")


            # text box with explanations
            text_box = QtWidgets.QTextEdit()
            text_box.setReadOnly(True)
            text_box.setText("<html><b>1) Choose the feature selection method</b><br>" +
                             "- Gini Importance: inaccurate but fast<br>" +
                             "- Filter Method: recommended<br>" +
                             "- Wrapper Method: slow but provides the best results<br><br>" +
                             "<b>2) Choose the parameters</b><br>" +
                             "- choose <u>number of features</u>: more features need more time and RAM, but provide better results." +
                             " To select the number of features <u>automatically</u>, set this number to 0 (selection will take a while).<br><br>" +
                             "- choose <u>Set Size Penalty (c)</u>: <br>small c (&lt; 0.1): excellent accuracy but larger feature set (=slower predictions) <br>larger c (&gt; 0.1): slightly reduced accuracy but smaller feature set (=faster predictions)<br><br>" +
                             "<b>3) Run Feature Selection</b> <br><br>"
                             "<b>4) More feature sets with other configurations</b><br>" +
                             "Change parameters above and press the Run Feature Selection button again, the new feature set will be added to the list for you to compare. <br><br>" +
                             "<b>5) Compare feature Sets</b><br>" +
                             "Use the viewer (middle) and the segmentation layers (right) to choose the best feature set<br><br>" +
                             "<b>6) Finish</b><br>" +
                             "Select the best set in the box at the bottom and hit 'Select Feature Set'<br><br>"
                             "<br>" +
                             "<b>Explanations:</b><br>" +
                             "<u>oob</u>: out of bag error (in &#37;), lower is better<br>" +
                             "feature <u>computation time</u> is shown in seconds<br><br>" +
                             "If the segmentation (shown in the viewer) differs a lot between the feature sets and the reference (usualls all features), but the oob values are similar then this is an indication that you should place more labels, especially in the regions where there were differences. Return to the feature selection once you added more labels</html>")

            # now add these widgets together to form the left_side_layout
            left_side_layout.addWidget(method_label)
            left_side_layout.addWidget(self.select_method_cbox)
            left_side_layout.addWidget(self.number_of_features_selection_widget)
            left_side_layout.addWidget(self.c_widget)
            left_side_layout.addWidget(self.run_button)
            left_side_layout.addWidget(text_box)
            left_side_layout.setStretchFactor(text_box, 1)
            # left_side_layout.addStretch(1)
            # assign that layout to the left side widget
            left_side_panel.setLayout(left_side_layout)

            ###################
            # The three widgets create above (left_side_panel, viewer, layerWidget) are now collected into one single
            # widget (centralWidget)
            ###################
            upper_widget_layout = QtWidgets.QHBoxLayout()
            upper_widget = QtWidgets.QWidget()

            upper_widget_layout.addWidget(left_side_panel)
            upper_widget_layout.addWidget(self.volumeEditorWidget)
            upper_widget_layout.addWidget(self.layer_widget)

            # make sure the volume viewer gets more space
            upper_widget_layout.setStretchFactor(self.volumeEditorWidget, 8)
            upper_widget_layout.setStretchFactor(left_side_panel, 3)
            upper_widget_layout.setStretchFactor(self.layer_widget, 3)

            upper_widget.setLayout(upper_widget_layout)

            ###################
            # Add 2 buttons and a combo box to the bottom (combo box is used to select feature set, one button for accepting
            # the new set, one for canceling)
            ###################
            self.all_feature_sets_combo_box = QtWidgets.QComboBox()
            self.all_feature_sets_combo_box.resize(500, 100)
            self.select_set_button = QtWidgets.QPushButton("Select Feature Set")
            self.cancel_button = QtWidgets.QPushButton("Cancel")
            show_features_of_selected_set = QtWidgets.QPushButton("Show Feature Names")
            show_features_of_selected_set.clicked.connect(self._show_feature_name_dialog)

            bottom_widget = QtWidgets.QWidget()
            bottom_layout = QtWidgets.QHBoxLayout()
            # bottom_layout.addWidget(self.current_status_label)
            #bottom_layout.addStretch(1)
            bottom_layout.addWidget(self.all_feature_sets_combo_box)
            bottom_layout.addWidget(show_features_of_selected_set)
            bottom_layout.addWidget(self.select_set_button)
            bottom_layout.addWidget(self.cancel_button)

            # bottom_layout.setStretchFactor(self.current_status_label, 1)
            bottom_layout.setStretchFactor(self.all_feature_sets_combo_box, 4)
            bottom_layout.setStretchFactor(show_features_of_selected_set, 1)
            bottom_layout.setStretchFactor(self.select_set_button, 2)
            bottom_layout.setStretchFactor(self.cancel_button, 2)

            bottom_widget.setLayout(bottom_layout)


            central_widget_layout = QtWidgets.QVBoxLayout()
            central_widget_layout.addWidget(upper_widget)
            central_widget_layout.addWidget(bottom_widget)

            central_widget = QtWidgets.QWidget()
            central_widget.setLayout(central_widget_layout)

            self.setLayout(central_widget_layout)
            self.setWindowTitle("Feature Selection")

            self._gui_initialized = True

    def _show_feature_name_dialog(self):
        dialog = QtWidgets.QDialog()
        dialog.resize(350, 650)

        ok_button = QtWidgets.QPushButton("ok")
        ok_button.clicked.connect(dialog.accept)

        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(text_edit)
        layout.addWidget(ok_button)

        layout.setStretchFactor(text_edit, 1)

        dialog.setLayout(layout)

        if self._selected_feature_set_id is None:
            text_edit.setText("No feature set selected!")
        else:
            #FIXME: WTF??? Why sort? They are already sorted by importance!
            selected_ids = numpy.sort(self._feature_selection_results[self._selected_feature_set_id].feature_ids)
            text = "<html>"

            for id in selected_ids:
                this_channel_name = self.feature_channel_names[id]
                this_channel_name = this_channel_name.replace("\xcf\x83", "&sigma;")
                text += this_channel_name + "<br>"
            text += "</html>"
            text_edit.setText(text)

        dialog.exec_()

    def _add_color_layer(self, data, name=None, visible=False):
        '''
        adds a color layer to the layerstack

        :param data: numpy array (2D, c) containing the data (c is color)
        :param name: name of layer
        :param visible: bool determining whether this layer should be set to visible
        :return:
        '''
        assert len(data.shape) == 3
        data_sources = []
        for i in range(data.shape[2]):
            a, data_shape = createDataSource(data[:,:,i], True)
            data_sources.append(a)
        self.editor.dataShape = list(data_shape)
        if data.shape[2] == 2:
            new_layer = RGBALayer(data_sources[0], data_sources[1])
        elif data.shape[2] == 3:
            new_layer = RGBALayer(data_sources[0], data_sources[1], data_sources[2])
        elif data.shape[2] == 4:
            new_layer = RGBALayer(data_sources[0], data_sources[1], data_sources[2], data_sources[3])
        else:
            raise Exception("Unexpected number of colors")

        new_layer.visible = visible
        if name is not None:
            new_layer.name = name
        self.layerstack.append(new_layer)

    def _handle_selected_feature_set_changed(self):
        '''
        If the user selects a specific feature set in the comboBox in the bottom row then the segmentation of this
        feature set will be displayed in the viewer
        '''

        id = self.all_feature_sets_combo_box.currentIndex()
        for i, layer in enumerate(self.layerstack):
            layer.visible = (i == id)
            layer.opacity = 1.
        self._selected_feature_set_id = id
        self.selected_features_matrix = self._feature_selection_results[id].feature_matrix

    def _add_feature_set_to_results(self, feature_set_result):
        '''
        After feature selection, the feature set (and the segmentation achieved with it) will be added to the results
        :param feature_set_result: FeatureSelectionResult instance
        '''
        self._feature_selection_results.insert(0, feature_set_result)
        self._add_segmentation_layer(feature_set_result.segmentation, name=feature_set_result.name)
        self.all_feature_sets_combo_box.insertItem(0, feature_set_result.long_name)

    def _update_parameters(self):
        self._selection_params["num_of_feat"] = self.number_of_feat_box.value()
        self._selection_params["c"] = self.spinbox_c_widget.value()
        self._update_gui()

    def _update_gui(self):
        '''
        Depending on feature selection method and the number of features in the set some GUI elements are
        enabled/disabled
        '''
        if (self.select_method_cbox.currentIndex() == 0) | (self.select_method_cbox.currentIndex() == 1):
            self.c_widget.setEnabled(False)
            self.number_of_features_selection_widget.setEnabled(True)
        else:
            self.c_widget.setEnabled(True)
            self.number_of_features_selection_widget.setEnabled(False)
        if self.number_of_feat_box.value() == 0:
            self.c_widget.setEnabled(True)

    def _add_segmentation_layer(self, data, name=None, visible=False):
        '''
        adds a segementation layer to the layerstack

        :param data: numpy array (2D) containing the data
        :param name: name of layer
        :param visible: bool determining whether this layer should be set to visible
        :return:
        '''
        assert len(data.shape) == 2
        a, data_shape = createDataSource(data, True)
        self.editor.dataShape = list(data_shape)
        new_layer = ColortableLayer(a, self.colortable)
        new_layer.visible = visible
        new_layer.opacity = 0.5
        if name is not None:
            new_layer.name = name
        self.layerstack.append(new_layer)

    def _add_grayscale_layer(self, data, name=None, visible=False):
        '''
        adds a grayscale layer to the layerstack

        :param data: numpy array (2D) containing the data
        :param name: name of layer
        :param visible: bool determining whether this layer should be set to visible
        :return:
        '''
        #assert len(data.shape) == 2
        a, data_shape = createDataSource(data, True)
        self.editor.dataShape = list(data_shape)
        new_layer = GrayscaleLayer(a)
        new_layer.visible = visible
        if name is not None:
            new_layer.name = name
        self.layerstack.append(new_layer)

    def _handle_selected_method_changed(self):
        '''
        activated upon changing the feature selection method
        '''
        self._selection_method = self.__selection_methods[self.select_method_cbox.currentIndex()]
        self._update_gui()

    def retrieve_segmentation(self, feat_matrix):
        '''
        Uses the features of the feat_matrix to retrieve a segmentation of the currently visible slice
        :param feat_matrix: boolean feature matrix as in opFeatureSelection.SelectionMatrix
        :return: segmentation (2d numpy array), out of bag error
        '''
        # remember the currently selected features so that they are not changed in case the user cancels the dialog
        user_defined_matrix = self.opFeatureSelection.SelectionMatrix.value


        # apply new feature matrix and make sure lazyflow applies the changes
        if numpy.sum(user_defined_matrix != feat_matrix) != 0:
            self.opFeatureSelection.SelectionMatrix.setValue(feat_matrix)
            self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
            self.opFeatureSelection.setupOutputs()
            # self.opFeatureSelection.change_feature_cache_size()

        start_time = times()[4]

        old_freeze_prediction_value = self.opPixelClassification.FreezePredictions.value
        self.opPixelClassification.FreezePredictions.setValue(False)

        # retrieve segmentation layer(s)
        slice_shape = self.raw_xy_slice.shape[:2]
        segmentation = numpy.zeros(slice_shape, dtype=numpy.uint8)

        axisOrder = [ tag.key for tag in self.opFeatureSelection.InputImage.meta.axistags ]
        bbox = self._bbox

        do_transpose = axisOrder.index('x') > axisOrder.index('y')

        # we need to reset the 'c' axis because it only has length 1 for segmentation
        if 'c' not in list(bbox.keys()):
            axisOrder += ['c']

        bbox['c'] = [0, 1]

        total_slicing = [slice(bbox[ai][0], bbox[ai][1]) for ai in axisOrder]

        # combine segmentation layers
        for i, seglayer in enumerate(self.opPixelClassification.SegmentationChannels):
            single_layer_of_segmentation = numpy.squeeze(seglayer[total_slicing].wait())
            if do_transpose:
                single_layer_of_segmentation = single_layer_of_segmentation.transpose()
            segmentation[single_layer_of_segmentation != 0] = i

        end_time = times()[4]

        oob_err = 100. * numpy.mean(self.opPixelClassification.opTrain.outputs['Classifier'].value.oobs)

        # revert changes to matrix and other operators
        if numpy.sum(user_defined_matrix != feat_matrix) != 0:
            self.opFeatureSelection.SelectionMatrix.setValue(user_defined_matrix)
            self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
            self.opFeatureSelection.setupOutputs()

        self.opPixelClassification.FreezePredictions.setValue(old_freeze_prediction_value)

        return segmentation, oob_err, end_time-start_time

    def retrieve_segmentation_new(self, feat):
        '''
        Attempt to use the opSimplePixelClassification by Stuart. Could not get this to work so far...
        :param feat:
        :return:
        '''
        from . import opSimplePixelClassification
        from lazyflow import graph
        from lazyflow.classifiers import ParallelVigraRfLazyflowClassifierFactory

        self.opSimpleClassification = opSimplePixelClassification.OpSimplePixelClassification(parent = self.opPixelClassification.parent.pcApplet.topLevelOperator)
        self.opSimpleClassification.Labels.connect(self.opPixelClassification.opLabelPipeline.Output)
        self.opSimpleClassification.Features.connect(self.opPixelClassification.FeatureImages)
        self.opSimpleClassification.Labels.resize(1)
        self.opSimpleClassification.Features.resize(1)
        self.opSimpleClassification.ingest_labels()
        self.opSimpleClassification.ClassifierFactory.setValue(ParallelVigraRfLazyflowClassifierFactory(100))

        # resize of input slots required, otherwise "IndexError: list index out of range" after this line
        segmentation = self.opSimpleClassification.Predictions[0][0, :, :, 25, 0].wait()

        # now I get:
        '''RuntimeError:
        Precondition violation!
        Sampler(): Requested sample count must be at least as large as the number of strata.
        (/miniconda/conda-bld/work/include/vigra/sampling.hxx:371)'''


        '''
        In [72]: self.opSimpleClassification.Predictions[0].meta.shape
        Out[72]: (1, 300, 275, 50, 1)
        '''

    def _convert_featureIDs_to_featureMatrix(self, selected_feature_IDs):
        '''
        The feature Selection Operators return id's of selected features. Here, these IDs are converted to fit the
        feature matrix as in opFeatureSelection.SelectionMatrix

        :param selected_feature_IDs: list of selected feature ids
        :return: feature matrix for opFeatureSelection
        '''
        scales = self.opFeatureSelection.Scales.value
        featureIDs = self.opFeatureSelection.FeatureIds.value
        new_matrix = numpy.zeros((len(featureIDs), len(scales)), 'bool')  # initialize new matrix as all False

        # now find out where i need to make changes in the matrix
        # matrix is len(features) by len(scales)
        for feature in selected_feature_IDs:
            channel_name = self.feature_channel_names[feature]
            eq_sign_pos = channel_name.find("=")
            right_bracket_pos = channel_name.find(")")
            scale = float(channel_name[eq_sign_pos + 1 : right_bracket_pos])
            if "Smoothing" in channel_name:
                featureID = "GaussianSmoothing"
            elif "Laplacian" in channel_name:
                featureID = "LaplacianOfGaussian"
            elif "Magnitude" in channel_name:
                featureID = "GaussianGradientMagnitude"
            elif "Difference" in channel_name:
                featureID = "DifferenceOfGaussians"
            elif "Structure" in channel_name:
                featureID = "StructureTensorEigenvalues"
            elif "Hessian" in channel_name:
                featureID = "HessianOfGaussianEigenvalues"
            else:
                raise Exception("Unkown feature encountered!")

            col_position_in_matrix = scales.index(scale)
            row_position_in_matrix = featureIDs.index(featureID)
            new_matrix[row_position_in_matrix, col_position_in_matrix] = True

        return new_matrix

    def _convert_featureMatrix_to_featureIDs(self, feature_matrix):
        feature_ids = ["Gaussian Smoothing", "Laplacian of Gaussian", "Gaussian Gradient Magnitude",
                       "Difference of Gaussians", "Structure Tensor Eigenvalues", "Hessian of Gaussian Eigenvalues"]
        scales = self.opFeatureSelection.Scales.value
        featureIDs = self.opFeatureSelection.FeatureIds.value

        ids = []
        for i in range(feature_matrix.shape[0]):
            for j in range(feature_matrix.shape[1]):
                if feature_matrix[i, j]:
                    id = feature_ids[i]
                    scale = scales[j]
                    for feat_num, feat_name in enumerate(self.feature_channel_names):
                        if id in feat_name and str(scale) in feat_name:
                            ids += [feat_num]

        return ids

    def _auto_select_num_features(self, feature_order):
        '''
        Determines the optimal number of features. This is achieved by sequentially adding features from the
        feature_order to the list and comparing the accuracies achieved with the growing feature sets. These accuracies
        are penalized by the feature set size ('accuracy - size trade-off' from GUI) to prevent the set size from
        becoming too large with too little accuracy benefit
        ToDO: This should actually use the opTrain of Ilastik

        :param feature_order: ordered list of feature IDs
        :return: optimal number of selected features
        '''
        from sklearn.ensemble import RandomForestClassifier
        from ilastik_feature_selection.wrapper_feature_selection import EvaluationFunction


        feature_order = numpy.array(feature_order)

        rf = RandomForestClassifier(n_jobs=-1, n_estimators=255)
        ev_func = EvaluationFunction(rf, complexity_penalty=self._selection_params["c"])
        n_select = 1
        overshoot = 0
        score = 0.
        X = self.featureLabelMatrix_all_features[:, 1:]
        Y = self.featureLabelMatrix_all_features[:, 0]
        n_select_opt = n_select

        while (overshoot < 3) & (n_select < self.n_features):
            score_old = score
            score = ev_func.evaluate_feature_set_size_penalty(X, Y, None, feature_order[:n_select])

            if score > score_old:
                n_select_opt = n_select
                overshoot = 0
            else:
                overshoot += 1

            n_select += 1

        return n_select_opt

    def _run_selection(self):
        QtWidgets.QApplication.instance().setOverrideCursor( QCursor(QtCore.Qt.WaitCursor) )
        '''
        runs the feature selection based on the selected parameters and selection method. Adds a segmentation layer
        showing the segmentation result achieved with the selected set
        '''
        # self.retrieve_segmentation_new(None)

        user_defined_matrix = self.opFeatureSelection.SelectionMatrix.value


        all_features_active_matrix = numpy.zeros(user_defined_matrix.shape, 'bool')
        all_features_active_matrix[:, 1:] = True
        all_features_active_matrix[0, 0] = True
        all_features_active_matrix[1:, 0] = False # do not use any other feature than gauss smooth on sigma=0.3
        self.opFeatureSelection.SelectionMatrix.setValue(all_features_active_matrix)
        self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
        self.opFeatureSelection.setupOutputs()
        # self.opFeatureSelection.change_feature_cache_size()
        self.feature_channel_names = self.opPixelClassification.FeatureImages.meta['channel_names']

        '''
        Here we retrieve the labels and feature matrix of all features. This is done only once each time the
        FeatureSelectionDialog is opened.

        Reason for not connecting the feature selection operators to the ilastik lazyflow graph:
        Whenever we are retrieving a new segmentation layer of a new feature set we are overriding the SelectionMatrix
        of the opFeatureSelection. If we then wanted to find another feature set, the feature selection operators would
        request the features and label matrix again. In the meantime, the feature set has been changed and changed back,
        however, resulting in the featureLabelMatrix to be dirty. Therefore it would have to be recalculated whenever we
        are requesting a new feature set. The way this is prevented here is by simply retrieving the FeatureLabelMatrix
        once each time the dialog is opened and manually writing it into the inputSlot of the feature selection
        operators. This is possible because the FeatureLabelMatrix cannot change from within the FeatureSelectionDialog
        (it contians feature values and the corresponding labels of all labeled voxels and all features. The labels
        cannot be modified from within this dialog)
        '''
        if not self._initialized_feature_matrix:
            self.featureLabelMatrix_all_features = self.opFeatureMatrixCaches.LabelAndFeatureMatrix.value #FIXME: why is this initialized?
            self.opFilterFeatureSelection.FeatureLabelMatrix.setValue(self.featureLabelMatrix_all_features)
            self.opFilterFeatureSelection.FeatureLabelMatrix.resize(1)
            self.opFilterFeatureSelection.setupOutputs()
            self.opWrapperFeatureSelection.FeatureLabelMatrix.setValue(self.featureLabelMatrix_all_features)
            self.opWrapperFeatureSelection.FeatureLabelMatrix.resize(1)
            self.opWrapperFeatureSelection.setupOutputs()
            self.opGiniFeatureSelection.FeatureLabelMatrix.setValue(self.featureLabelMatrix_all_features)
            self.opGiniFeatureSelection.FeatureLabelMatrix.resize(1)
            self.opGiniFeatureSelection.setupOutputs()
            self._initialized_feature_matrix = True
            self.n_features = self.featureLabelMatrix_all_features.shape[1] - 1

        if not self._initialized_all_features_segmentation_layer:
            if numpy.sum(all_features_active_matrix != user_defined_matrix) != 0:
                segmentation_all_features, oob_all, time_all = self.retrieve_segmentation(all_features_active_matrix)
                selected_ids = self._convert_featureMatrix_to_featureIDs(all_features_active_matrix)
                all_features_result = FeatureSelectionResult(all_features_active_matrix,
                                                             selected_ids,
                                                 segmentation_all_features,
                                                 {'num_of_feat': 'all', 'c': 'None'},
                                                 'all features', oob_all, time_all)
                self._add_feature_set_to_results(all_features_result)
            self._initialized_all_features_segmentation_layer = True

        # run feature selection using the chosen parameters
        if self._selection_method == "gini":
            if self._selection_params["num_of_feat"] == 0:
                self.opGiniFeatureSelection.NumberOfSelectedFeatures.setValue(self.n_features)
                selected_feature_ids = self.opGiniFeatureSelection.SelectedFeatureIDs.value

                # now decide how many features you would like to use
                # features are ordered by their gini importance
                n_selected = self._auto_select_num_features(selected_feature_ids)
                selected_feature_ids = selected_feature_ids[:n_selected]
            else:
                # make sure no more than n_features are requested
                self.opGiniFeatureSelection.NumberOfSelectedFeatures.setValue(numpy.min([self._selection_params["num_of_feat"], self.n_features]))
                selected_feature_ids = self.opGiniFeatureSelection.SelectedFeatureIDs.value
        elif self._selection_method == "filter":
            if self._selection_params["num_of_feat"] == 0:
                self.opFilterFeatureSelection.NumberOfSelectedFeatures.setValue(self.n_features)
                selected_feature_ids = self.opFilterFeatureSelection.SelectedFeatureIDs.value

                # now decide how many features you would like to use
                # features are ordered
                n_selected = self._auto_select_num_features(selected_feature_ids)
                selected_feature_ids = selected_feature_ids[:n_selected]
            else:
                # make sure no more than n_features are requested
                self.opFilterFeatureSelection.NumberOfSelectedFeatures.setValue(numpy.min([self._selection_params["num_of_feat"], self.n_features]))
                selected_feature_ids = self.opFilterFeatureSelection.SelectedFeatureIDs.value
        else:
            self.opWrapperFeatureSelection.ComplexityPenalty.setValue(self._selection_params["c"])
            selected_feature_ids = self.opWrapperFeatureSelection.SelectedFeatureIDs.value

        # create a new layer for display in the volumina viewer
        # make sure to save the feature matrix used to obtain it
        # maybe also write down feature computation time and oob error
        new_matrix = self._convert_featureIDs_to_featureMatrix(selected_feature_ids)
        new_segmentation, new_oob, new_time = self.retrieve_segmentation(new_matrix)
        new_feature_selection_result = FeatureSelectionResult(new_matrix,
                                                              selected_feature_ids,
                                                              new_segmentation,
                                                              self._selection_params,
                                                              self._selection_method,
                                                              oob_err=new_oob,
                                                              feature_calc_time=new_time)
        self._add_feature_set_to_results(new_feature_selection_result)

        if not self._initialized_current_features_segmentation_layer:
            #FIXME: this should probably be moved somewhere else
            self.opFeatureSelection.setupOutputs()  # deletes cache for realistic feature computation time
            segmentation_current_features, oob_user, time_user = self.retrieve_segmentation(user_defined_matrix)
            selected_ids = self._convert_featureMatrix_to_featureIDs(user_defined_matrix)
            current_features_result = FeatureSelectionResult(user_defined_matrix,
                                                             selected_ids,
                                                             segmentation_current_features,
                                                             {'num_of_feat': 'user', 'c': 'None'},
                                                             'user features', oob_user, time_user)
            self._add_feature_set_to_results(current_features_result)
            self._initialized_current_features_segmentation_layer = True




        # revert changes to matrix
        self.opFeatureSelection.SelectionMatrix.setValue(user_defined_matrix)
        self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
        self.opFeatureSelection.setupOutputs()
        QtWidgets.QApplication.instance().restoreOverrideCursor()


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    #import sys
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #    QtWidgets.QApplication.instance().exec_()
    app = QtWidgets.QApplication([])
    win = QtWidgets.QMainWindow()
    win.resize(800, 800)

    feat_dial = FeatureSelectionDialog()
    button = QtWidgets.QPushButton("open feature selection dialog")
    button.clicked.connect(feat_dial.show)

    central_widget = QtWidgets.QWidget()
    layout2 = QtWidgets.QHBoxLayout()
    layout2.addWidget(button)

    central_widget.setLayout(layout2)
    win.setCentralWidget(central_widget)

    win.show()
    QtWidgets.QApplication.instance().exec_()
