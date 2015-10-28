__author__ = 'fabian'

import numpy as np
# import scipy
from PyQt4 import QtCore, QtGui
# import pyqtgraph as pg

import IPython

# from volumina.api import Viewer
from volumina.widgets import layerwidget
from volumina import volumeEditorWidget
from volumina.layer import ColortableLayer
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
                name = "%s_num_feat_auto" % self.selection_method
            else:
                name = "%s_num_feat_%d" % (self.selection_method, self.parameters["num_of_feat"])
        else:
            name = "%s_c_%1.02f" % (self.selection_method, self.parameters["c"])
        return name

    def change_name(self, name):
        self.name = name



class FeatureSelectionDialog(QtGui.QDialog):
    def __init__(self):
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
        self._selected_feature_set_id = None
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

        # just add some random layers to test functionality
        self._add_random_layers(5)


    def _init_gui(self):
        if not self._gui_initialized:
            # ------------------------------------------------------------------------------------------------------------
            # Layer Widget (displays all available layers and lets the user change their visibility)
            # ------------------------------------------------------------------------------------------------------------
            layer_widget = layerwidget.LayerWidget()
            layer_widget.init(self.layerstack)

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

            text_c_widget = QtGui.QLabel("Set Size vs Accuracy Trade-off") # not a good text
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
            upper_widget_layout.addWidget(layer_widget)

            # make sure the volume viewer gets more space
            upper_widget_layout.setStretchFactor(self.viewer, 4)
            upper_widget_layout.setStretchFactor(left_side_panel, 2)
            upper_widget_layout.setStretchFactor(layer_widget, 1)

            upper_widget.setLayout(upper_widget_layout)

            # ------------------------------------------------------------------------------------------------------------
            # Add 2 buttons and a combo box to the bottom (combo box is used to select feature set, one button for accepting
            # the new set, one for canceling)
            # ------------------------------------------------------------------------------------------------------------
            self.all_feature_sets_combo_box = QtGui.QComboBox()
            self.select_set_button = QtGui.QPushButton("Select Feature Set")
            self.cancel_button = QtGui.QPushButton("Cancel")

            bottom_widget = QtGui.QWidget()
            bottom_layout = QtGui.QHBoxLayout()
            bottom_layout.addStretch(1)
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
        self._selected_feature_set_id = id

    def _add_feature_set_to_results(self, feature_set_result):
        self._feature_selection_results.append(feature_set_result)
        self._add_segmentation_layer(feature_set_result.segmentation, name=feature_set_result.name)
        self.all_feature_sets_combo_box.addItem(feature_set_result.name)

    def _update_parameters(self):
        self._selection_params["num_of_feat"] = self.number_of_feat_box.value()
        self._selection_params["c"] = self.spinbox_c_widget.value()

    def _add_segmentation_layer(self, data, name=None, visible=False):
        assert len(data.shape) == 2
        a, data_shape = createDataSource(data, True)
        self.editor.dataShape = list(data_shape)
        new_layer = ColortableLayer(a, self.colortable)
        new_layer.visible = visible
        if name is not None:
            new_layer.name = name
        self.layerstack.append(new_layer)


    def _handle_selected_method_changed(self):
        if (self.select_method_cbox.currentIndex() == 0) | (self.select_method_cbox.currentIndex() == 1):
            self.c_widget.setEnabled(False)
            self.number_of_features_selection_widget.setEnabled(True)
        else:
            self.c_widget.setEnabled(True)
            self.number_of_features_selection_widget.setEnabled(False)
        self._selection_method = self.__selection_methods[self.select_method_cbox.currentIndex()]

    def _run_selection(self):
        # run feature selection using the chosen parameters

        # create a new layer for display in the volumina viewer
        # make sure to save the feature matrix used to obtain it
        # maybe also write down feature computation time and oob error

        raise NotImplementedError







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