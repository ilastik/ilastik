__author__ = 'fabian'

import numpy as np
# import scipy
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
# import pyqtgraph as pg

import IPython

# from volumina.api import Viewer
from volumina.widgets import layerwidget
from volumina import volumeEditorWidget
from volumina.layer import ColortableLayer, GrayscaleLayer
from volumina import colortables
from volumina.pixelpipeline.datasourcefactories import createDataSource

from copy import deepcopy

# just a container class
class FeatureSelectionResult(object):
    def __init__(self, feature_matrix, segmentation, parameters, selection_method, oob_err = None, feature_calc_time = None):
        self.feature_matrix = feature_matrix
        self.segmentation = segmentation
        self.parameters = parameters
        self.selection_method = selection_method
        self.oob_err = oob_err
        self.feature_calc_time = feature_calc_time

        self.name = self._create_name()

    def _create_name(self):
        if self.selection_method == "filter" or self.selection_method == "gini":
            if self.parameters["num_of_feat"]==0:
                name = "%s_num_feat_auto_%d" % (self.selection_method, np.sum(self.feature_matrix))
            else:
                name = "%s_num_feat_%d" % (self.selection_method, self.parameters["num_of_feat"])
        else:
            name = "%s_c_%1.02f" % (self.selection_method, self.parameters["c"])
        return name

    def change_name(self, name):
        self.name = name



class FeatureSelectionDialog(QtGui.QDialog):
    def __init__(self, opFeatureSelection, opPixelClassification):
        self.opPixelClassification = opPixelClassification
        self.opFeatureSelection = opFeatureSelection
        self.opFilterFeatureSelection = self.opPixelClassification.opFilterFeatureSelection
        self.opWrapperFeatureSelection = self.opPixelClassification.opWrapperFeatureSelection
        self.opGiniFeatureSelection = self.opPixelClassification.opGiniFeatureSelection
        self.opFeatureMatrixCaches = self.opPixelClassification.opFeatureMatrixCaches

        self.opFilterFeatureSelection.FeatureLabelMatrix.connect(self.opFeatureMatrixCaches.LabelAndFeatureMatrix)
        self.opWrapperFeatureSelection.FeatureLabelMatrix.connect(self.opFeatureMatrixCaches.LabelAndFeatureMatrix)
        self.opGiniFeatureSelection.FeatureLabelMatrix.connect(self.opFeatureMatrixCaches.LabelAndFeatureMatrix)
        self._xysliceID = -1

        self._initialized_all_features_segmentation_layer = False
        self._initialized_current_features_segmentation_layer = False
        self._initialized_feature_matrix = False
        self._selected_feature_set_id = None

        # this should be changed
        self._stackdim = self.opPixelClassification.InputImages.meta.shape

        super(FeatureSelectionDialog, self).__init__()

        self.__selection_methods = {
            0: "gini",
            1: "filter",
            2: "wrapper"
        }

        self._selection_params = {
            "num_of_feat": 0,
            "c": 0.1
        }
        self._selection_method = "None"
        self._gui_initialized = False #  is set to true once gui is initialized, prevents multiple initialization
        self._feature_selection_results = []

        self.colortable = colortables.default16
        self.layerstack = layerwidget.LayerStackModel()

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
        ilastik_editor = self.opPixelClassification.parent.pcApplet.getMultiLaneGui().currentGui().editor
        ilastik_currentslicing = ilastik_editor.posModel.slicingPos
        self._ilastik_currentslicing_5D = ilastik_editor.posModel.slicingPos5D

        if ilastik_currentslicing[-1] != self._xysliceID:
            self._xysliceID = ilastik_currentslicing[-1]
            self.reset_me()
            # show raw data of slice
            # this is stupid - is there any mor intelligent way to code this?
            if len(self._stackdim) == 5:
                self.raw_xy_slice = np.squeeze(self.opPixelClassification.InputImages[self._ilastik_currentslicing_5D[0], :, :, self._xysliceID, :].wait())
            elif len(self._stackdim) == 4:
                self.raw_xy_slice = np.squeeze(self.opPixelClassification.InputImages[:, :, self._xysliceID, :].wait())
            elif len(self._stackdim) == 3:
                self.raw_xy_slice = np.squeeze(self.opPixelClassification.InputImages[:, self._xysliceID, :].wait())
            else:
                raise Exception

            self.add_grayscale_layer(self.raw_xy_slice, "raw_data", True)

        # now launch the dialog
        super(FeatureSelectionDialog, self).exec_()

    def reset_me(self):
        # this deletes everything from the layerstack
        while(self.layerstack.removeRow(0)):
            pass
        self._feature_selection_results = []
        self._initialized_all_features_segmentation_layer = False
        self._initialized_current_features_segmentation_layer = False
        self._initialized_feature_matrix = False
        self.all_feature_sets_combo_box.resetInputContext()
        self._selected_feature_set_id = None

    def _init_gui(self):
        if not self._gui_initialized:
            # ------------------------------------------------------------------------------------------------------------
            # Layer Widget (displays all available layers and lets the user change their visibility)
            # ------------------------------------------------------------------------------------------------------------
            self.layer_widget = layerwidget.LayerWidget()
            self.layer_widget.init(self.layerstack)

            # ------------------------------------------------------------------------------------------------------------
            # Instantiation of the volumeEditor (+ widget)
            # ------------------------------------------------------------------------------------------------------------
            self.editor = volumeEditorWidget.VolumeEditor(self.layerstack, parent=self)
            self.viewer = volumeEditorWidget.VolumeEditorWidget()
            self.viewer.init(self.editor)

            # ------------------------------------------------------------------------------------------------------------
            # This section constructs the GUI elements that are displayed on the left side of the window
            # ------------------------------------------------------------------------------------------------------------
            left_side_panel = QtGui.QListWidget()
            left_side_layout = QtGui.QVBoxLayout()

            # combo box for selecting desired feature selection method
            self.select_method_cbox = QtGui.QComboBox()
            self.select_method_cbox.addItem("Gini Importance")
            self.select_method_cbox.addItem("Filter Method")
            self.select_method_cbox.addItem("Wrapper Method")
            self.select_method_cbox.setCurrentIndex(1)


            # number of selected features
            # create a widget containing 2 child widgets in a horizontal layout
            # child widgets: QLabel for text and QSpinBox for selecting an integer value for number of features
            self.number_of_features_selection_widget = QtGui.QWidget()

            text_number_of_feat = QtGui.QLabel("Number of Features (0=auto)")
            self.number_of_feat_box = QtGui.QSpinBox()

            number_of_features_selction_layout = QtGui.QHBoxLayout()
            number_of_features_selction_layout.addWidget(text_number_of_feat)
            number_of_features_selction_layout.addWidget(self.number_of_feat_box)

            self.number_of_features_selection_widget.setLayout(number_of_features_selction_layout)


            # regularization parameter for wrapper
            # create a widget containing 2 child widgets in a horizontal layout
            # child widgets: QLabel for text and QDoubleSpinBox for selecting a float value for c (parameter)
            self.c_widget = QtGui.QWidget()

            text_c_widget = QtGui.QLabel("Set Size Penalty") # not a good text
            self.spinbox_c_widget = QtGui.QDoubleSpinBox()
            # may have to set increment to 0.01

            c_widget_layout = QtGui.QHBoxLayout()
            c_widget_layout.addWidget(text_c_widget)
            c_widget_layout.addWidget(self.spinbox_c_widget)

            self.c_widget.setLayout(c_widget_layout)

            # run button
            self.run_button = QtGui.QPushButton("Run Feature Selection")


            # now add these widgets together to form the left_side_layout
            left_side_layout.addWidget(self.select_method_cbox)
            left_side_layout.addWidget(self.number_of_features_selection_widget)
            left_side_layout.addWidget(self.c_widget)
            left_side_layout.addWidget(self.run_button)
            left_side_layout.addStretch(1)
            # assign that layout to the left side widget
            left_side_panel.setLayout(left_side_layout)

            # ------------------------------------------------------------------------------------------------------------
            # The three widgets create above (left_side_panel, viewer, layerWidget) are now collected into one single
            # widget (centralWidget)
            # ------------------------------------------------------------------------------------------------------------
            upper_widget_layout = QtGui.QHBoxLayout()
            upper_widget = QtGui.QWidget()

            upper_widget_layout.addWidget(left_side_panel)
            upper_widget_layout.addWidget(self.viewer)
            upper_widget_layout.addWidget(self.layer_widget)

            # make sure the volume viewer gets more space
            upper_widget_layout.setStretchFactor(self.viewer, 8)
            upper_widget_layout.setStretchFactor(left_side_panel, 3)
            upper_widget_layout.setStretchFactor(self.layer_widget, 2)

            upper_widget.setLayout(upper_widget_layout)

            # ------------------------------------------------------------------------------------------------------------
            # Add 2 buttons and a combo box to the bottom (combo box is used to select feature set, one button for accepting
            # the new set, one for canceling)
            # ------------------------------------------------------------------------------------------------------------
            self.all_feature_sets_combo_box = QtGui.QComboBox()
            self.all_feature_sets_combo_box.resize(500, 100)
            self.select_set_button = QtGui.QPushButton("Select Feature Set")
            self.cancel_button = QtGui.QPushButton("Cancel")
            self.current_status_label = QtGui.QLabel("Current Status: Waiting for user input...\t")

            bottom_widget = QtGui.QWidget()
            bottom_layout = QtGui.QHBoxLayout()
            bottom_layout.addWidget(self.current_status_label)
            #bottom_layout.addStretch(1)
            bottom_layout.addWidget(self.all_feature_sets_combo_box)
            bottom_layout.addWidget(self.select_set_button)
            bottom_layout.addWidget(self.cancel_button)

            bottom_widget.setLayout(bottom_layout)


            central_widget_layout = QtGui.QVBoxLayout()
            central_widget_layout.addWidget(upper_widget)
            central_widget_layout.addWidget(bottom_widget)

            central_widget = QtGui.QWidget()
            central_widget.setLayout(central_widget_layout)

            self.setLayout(central_widget_layout)
            self.setWindowTitle("Feature Selection")

            self._gui_initialized = True

    def _add_random_layers(self, n=2):
        for i in range(n):
            f = np.round(np.random.random((450, 450))*10).astype("int")
            dummy_result = FeatureSelectionResult(None, f, self._selection_params, "None")
            dummy_result.change_name("dummy_result%d" % i)
            self._add_feature_set_to_results(dummy_result)

    def _handle_selected_feature_set_changed(self):
        id = self.all_feature_sets_combo_box.currentIndex()
        for i, layer in enumerate(self.layerstack):
            layer.visible = (i == id)
            layer.opacity = 1.
        self._selected_feature_set_id = id

    def _add_feature_set_to_results(self, feature_set_result):
        self._feature_selection_results.append(feature_set_result)
        self._add_segmentation_layer(feature_set_result.segmentation, name=feature_set_result.name)
        self.all_feature_sets_combo_box.addItem(feature_set_result.name)

    def _update_parameters(self):
        self._selection_params["num_of_feat"] = self.number_of_feat_box.value()
        self._selection_params["c"] = self.spinbox_c_widget.value()
        self._update_gui()

    def _update_gui(self):
        if (self.select_method_cbox.currentIndex() == 0) | (self.select_method_cbox.currentIndex() == 1):
            self.c_widget.setEnabled(False)
            self.number_of_features_selection_widget.setEnabled(True)
        else:
            self.c_widget.setEnabled(True)
            self.number_of_features_selection_widget.setEnabled(False)
        if self.number_of_feat_box.value() == 0:
            self.c_widget.setEnabled(True)

    def _add_segmentation_layer(self, data, name=None, visible=False):
        assert len(data.shape) == 2
        a, data_shape = createDataSource(data, True)
        self.editor.dataShape = list(data_shape)
        new_layer = ColortableLayer(a, self.colortable)
        new_layer.visible = visible
        if name is not None:
            new_layer.name = name
        self.layerstack.append(new_layer)

    def add_grayscale_layer(self, data, name=None, visible=False):
        assert len(data.shape) == 2
        a, data_shape = createDataSource(data, True)
        self.editor.dataShape = list(data_shape)
        new_layer = GrayscaleLayer(a)
        new_layer.visible = visible
        if name is not None:
            new_layer.name = name
        self.layerstack.append(new_layer)

    def _handle_selected_method_changed(self):
        self._selection_method = self.__selection_methods[self.select_method_cbox.currentIndex()]
        self._update_gui()


    def retrieve_segmentation(self, feat_matrix):
        # remember the currently selected features so that they are not changed in case the user cancels the dialog
        user_defined_matrix = self.opFeatureSelection.SelectionMatrix.value

        # apply new feature matrix and make sure lazyflow applies the changes
        if np.sum(user_defined_matrix != feat_matrix) == 0:
            self.opFeatureSelection.SelectionMatrix.setValue(feat_matrix)
            self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
            self.opFeatureSelection.setupOutputs()
            # self.opFeatureSelection.change_feature_cache_size()

        old_freeze_prediction_value = self.opPixelClassification.FreezePredictions.value
        self.opPixelClassification.FreezePredictions.setValue(False)

        # retrieve segmentation layer(s)
        slice_shape = self.raw_xy_slice.shape
        segmentation = np.zeros(slice_shape)
        for i, seglayer in enumerate(self.opPixelClassification.SegmentationChannels):
            if len(self._stackdim) == 5:
                single_layer_of_segmentation = np.squeeze(seglayer[self._ilastik_currentslicing_5D[0], :, :, self._xysliceID, :].wait())
            elif len(self._stackdim) == 4:
                single_layer_of_segmentation = np.squeeze(seglayer[:, :, self._xysliceID, :].wait())
            elif len(self._stackdim) == 3:
                single_layer_of_segmentation = np.squeeze(seglayer[:, self._xysliceID, :].wait())
            else:
                raise Exception
            segmentation[single_layer_of_segmentation != 0] = i

        # revert changes to matrix and other operators
        if np.sum(user_defined_matrix != feat_matrix) == 0:
            self.opFeatureSelection.SelectionMatrix.setValue(user_defined_matrix)
            self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
            self.opFeatureSelection.setupOutputs()

        self.opPixelClassification.FreezePredictions.setValue(old_freeze_prediction_value)

        return segmentation

    def _convert_featureIDs_to_featureMatrix(self, selected_feature_IDs):
        feature_channel_names = self.opPixelClassification.FeatureImages.meta['channel_names']
        scales = self.opFeatureSelection.Scales.value
        featureIDs = self.opFeatureSelection.FeatureIds.value
        new_matrix = np.zeros((len(featureIDs), len(scales)), 'bool')  # initialize new matrix as all False

        # now find out where i need to make changes in the matrix
        # matrix is len(features) by len(scales)
        for feature in selected_feature_IDs:
            channel_name = feature_channel_names[feature]
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

    def _auto_select_num_features(self, feature_order):
        from sklearn.ensemble import RandomForestClassifier
        from feature_selection.wrapper_feature_selection import EvaluationFunction


        feature_order = np.array(feature_order)

        rf = RandomForestClassifier(n_jobs=1, n_estimators=255)
        ev_func = EvaluationFunction(rf, complexity_penalty=self._selection_params["c"])
        n_select = 1
        overshoot = 0
        score = 0.
        X = self.featureLabelMatrix_all_features[:, 1:]
        Y = self.featureLabelMatrix_all_features[:, 0]

        while overshoot < 3:
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
        pyqtRemoveInputHook()
        IPython.embed()
        pyqtRestoreInputHook()
        if not self._initialized_feature_matrix:
            self.current_status_label.setText("Current Status: Feature calculation")
            self.current_status_label.repaint()
            self.featureLabelMatrix_all_features = self.opFeatureMatrixCaches.LabelAndFeatureMatrix.value
            self.n_features = self.featureLabelMatrix_all_features.shape[1] - 1
            self._initialized_feature_matrix = True


        # self.opFeatureSelection.change_feature_cache_size()
        QtGui.QApplication.instance().setOverrideCursor( QtGui.QCursor(QtCore.Qt.WaitCursor) )

        user_defined_matrix = self.opFeatureSelection.SelectionMatrix.value

        if not self._initialized_current_features_segmentation_layer:
            self.current_status_label.setText("Current Status: Get segmentation (user features)")
            self.current_status_label.repaint()
            segmentation_current_features = self.retrieve_segmentation(user_defined_matrix)
            self._add_segmentation_layer(segmentation_current_features, "user_selected_features")
            self._initialized_current_features_segmentation_layer = True

        all_features_active_matrix = np.zeros(user_defined_matrix.shape, 'bool')
        all_features_active_matrix[:, 1:] = True
        all_features_active_matrix[0, 0] = True
        all_features_active_matrix[1:, 0] = False # do not use any other feature than gauss smooth on sigma=0.3
        self.opFeatureSelection.SelectionMatrix.setValue(all_features_active_matrix)
        self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
        self.opFeatureSelection.setupOutputs()
        # self.opFeatureSelection.change_feature_cache_size()

        if not self._initialized_all_features_segmentation_layer:
            if np.sum(all_features_active_matrix != user_defined_matrix) != 0:
                self.current_status_label.setText("Current Status: Get segmentation (all features)")
                self.current_status_label.repaint()
                segmentation_all_features = self.retrieve_segmentation(all_features_active_matrix)
                self._add_segmentation_layer(segmentation_all_features, "all_features")
            self._initialized_all_features_segmentation_layer = True

        # run feature selection using the chosen parameters
        self.current_status_label.setText("Current Status: Feature selection")
        self.current_status_label.repaint()
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
                self.opGiniFeatureSelection.NumberOfSelectedFeatures.setValue(np.min([self._selection_params["num_of_feat"], self.n_features]))
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
                self.opFilterFeatureSelection.NumberOfSelectedFeatures.setValue(np.min([self._selection_params["num_of_feat"], self.n_features]))
                selected_feature_ids = self.opFilterFeatureSelection.SelectedFeatureIDs.value
        else:
            self.opWrapperFeatureSelection.ComplexityPenalty.setValue(self._selection_params["c"])
            selected_feature_ids = self.opWrapperFeatureSelection.SelectedFeatureIDs.value

        self.current_status_label.setText("Current Status: Get segmentation (new feature set)")
        self.current_status_label.repaint()
        # create a new layer for display in the volumina viewer
        # make sure to save the feature matrix used to obtain it
        # maybe also write down feature computation time and oob error
        new_matrix = self._convert_featureIDs_to_featureMatrix(selected_feature_ids)
        new_segmentation = self.retrieve_segmentation(new_matrix)
        new_feature_selection_result = FeatureSelectionResult(new_matrix, new_segmentation, self._selection_params, self._selection_method)
        self._add_feature_set_to_results(new_feature_selection_result)

        # revert changes to matrix
        self.opFeatureSelection.SelectionMatrix.setValue(user_defined_matrix)
        self.opFeatureSelection.SelectionMatrix.setDirty() # this does not do anything!?!?
        self.opFeatureSelection.setupOutputs()
        self.current_status_label.setText("Current Status: Waiting for user input...\t")
        self.current_status_label.repaint()
        QtGui.QApplication.instance().restoreOverrideCursor()


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    #import sys
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #    QtGui.QApplication.instance().exec_()
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.resize(800, 800)

    feat_dial = FeatureSelectionDialog()
    button = QtGui.QPushButton("open feature selection dialog")
    button.clicked.connect(feat_dial.show)

    central_widget = QtGui.QWidget()
    layout2 = QtGui.QHBoxLayout()
    layout2.addWidget(button)

    central_widget.setLayout(layout2)
    win.setCentralWidget(central_widget)

    win.show()
    QtGui.QApplication.instance().exec_()