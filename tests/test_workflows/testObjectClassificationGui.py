###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2018, the ilastik developers
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
from collections import namedtuple
import csv
import logging
import os
import shutil
import sys
import tempfile
import zipfile

from PyQt5.QtWidgets import QApplication

import h5py
import numpy

from ilastik.workflows import ObjectClassificationWorkflowPrediction
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.widgets.exportObjectInfoDialog import ExportObjectInfoDialog, FILE_TYPES


from lazyflow.utility.timer import Timer
from tests.helpers import ShellGuiTestCaseBase

from volumina.layer import AlphaModulatedLayer

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class TestObjectClassificationGui(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the object classification workflow.

    Note: These tests are named (prefixed with `test_%02d`) in order to impose
        an order. Tests simulate interaction with a ilastik and depend on
        the earlier ones.
    """
    @classmethod
    def workflowClass(cls):
        return ObjectClassificationWorkflowPrediction

    @classmethod
    def setup_class(cls):
        # Base class first
        super().setup_class()

        # input files:
        current_dir = os.path.split(__file__)[0]
        cls.sample_data_raw = os.path.abspath(os.path.join(current_dir, '../data/inputdata/3d.h5'))
        cls.sample_data_prob = os.path.abspath(
            os.path.join(current_dir, '../data/inputdata/3d_Probabilities.h5'))

        # output files:
        cls.temp_dir = tempfile.mkdtemp()
        # uncomment for debugging
        # cls.temp_dir = os.path.expanduser('~/tmp')
        # if os.path.exists(cls.temp_dir):
        #     shutil.rmtree(cls.temp_dir)
        # os.makedirs(cls.temp_dir)
        cls.project_file = os.path.join(cls.temp_dir, 'test_project_oc.ilp')
        cls.output_file = os.path.join(cls.temp_dir, 'out_object_prediction.h5')
        cls.table_h5_file = os.path.join(cls.temp_dir, 'table.h5')
        cls.table_h5_file_exported = None  # Will be filled in test_06
        cls.table_csv_file = os.path.join(cls.temp_dir, 'table.csv')
        cls.table_csv_file_exported = None  # Will be filled in test_06

        # reference files
        # unzip the zip-file ;)
        cls.reference_zip_file = os.path.join(
            current_dir, '../data/outputdata/testObjectClassificationGuiReference.zip')
        cls.reference_path = os.path.join(cls.temp_dir, 'reference')
        cls.reference_files = {
            'csv_table': os.path.join(
                cls.reference_path, 'testObjectClassificationGuiReference/table-test_data_table.csv'),
            'h5_table': os.path.join(
                cls.reference_path, 'testObjectClassificationGuiReference/table-test_data.h5'),
            'predictions_h5': os.path.join(
                cls.reference_path, 'testObjectClassificationGuiReference/reference_out_object_prediction.h5')
        }
        os.makedirs(cls.reference_path)
        with zipfile.ZipFile(cls.reference_zip_file, mode='r') as zip_file:
            zip_file.extractall(path=cls.reference_path)
        cls.unzipped_reference_files = [os.path.join(cls.reference_path, fp)
                                        for fp in zip_file.namelist()]

        for file_name in cls.reference_files.values():
            assert os.path.exists(file_name)

        # Start the timer
        cls.timer = Timer()
        cls.timer.unpause()

    @classmethod
    def teardown_class(cls):
        cls.timer.pause()
        logger.debug(f"Total Time: {cls.timer.seconds()} seconds.")

        # Call our base class so the app quits!
        super().teardown_class()

        # Clean up: Delete any test files we generated
        # shutil.rmtree(cls.temp_dir)  # TODO: cleanup when dev is done

    def test_00_check_preconditions(self):
        """Make sure the needed files exist"""
        needed_files = [
            self.sample_data_raw,
            self.sample_data_prob
        ]
        for f in needed_files:
            assert os.path.exists(f), f"File {f} does not exist!"

    def test_01_create_project(self):
        """
        Create a blank project, manipulate few couple settings, and save it.
        """
        def impl():
            projFilePath = self.project_file
            shell = self.shell

            # New project
            shell.createAndLoadNewProject(projFilePath, self.workflowClass())
            workflow = shell.projectManager.workflow

            # Add our input files:
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.DatasetGroup.resize(1)
            info_raw = DatasetInfo()
            info_raw.filePath = self.sample_data_raw
            opDataSelection.DatasetGroup[0][0].setValue(info_raw)
            info_prob = DatasetInfo()
            info_prob.filePath = self.sample_data_prob
            info_raw.nickname = 'test_data'
            opDataSelection.DatasetGroup[0][1].setValue(info_prob)

            # Save
            shell.projectManager.saveProject()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_02_do_threshold(self):
        """
        Go to the second applet and adjust some thresholding settings.
        Apply and check the outcome.
        """
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            threshold_applet = workflow.thresholdingApplet
            gui = threshold_applet.getMultiLaneGui()
            op_threshold = threshold_applet.topLevelOperator.getLane(0)

            # activate the thresholding applet
            shell.setSelectedAppletDrawer(1)
            # let the gui catch up
            QApplication.processEvents()

            # set the required values
            # self.sendkeys(gui.currentGui()._drawer.inputChannelComboBox, '1')
            sigmas = {'x': 2.0, 'y': 2.1, 'z': 1.9}
            gui.currentGui()._drawer.sigmaSpinBox_X.setValue(sigmas['x'])
            gui.currentGui()._drawer.sigmaSpinBox_Y.setValue(sigmas['y'])
            gui.currentGui()._drawer.sigmaSpinBox_Z.setValue(sigmas['z'])
            threshold = 0.7
            gui.currentGui()._drawer.lowThresholdSpinBox.setValue(threshold)

            # get the final layer and check that it is not visible yet
            layermatch = [x.name.startswith('Final') for x in gui.currentGui().layerstack]
            assert sum(layermatch) == 1, "Only a single layer with 'Final' in the name expected."
            final_layer = gui.currentGui().layerstack[layermatch.index(True)]
            assert not final_layer.visible, (
                "Expected the final layer not to be visible before apply is triggered.")

            gui.currentGui()._drawer.applyButton.click()
            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

            assert final_layer.visible

            op_sigmas = op_threshold.SmootherSigma.value
            for k in sigmas.keys():
                assert sigmas[k] == op_sigmas[k], f"Sigma for '{k}' did not match."

            assert op_threshold.LowThreshold.value == threshold

            # now get the object count
            n_objects_expected = 23  # including the background object
            output = op_threshold.Output[:].wait()
            n_objects = len(numpy.unique(output))
            assert n_objects == n_objects_expected, (
                f"Number of objects mismatch, expected {n_objects_expected}, got {n_objects}")

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_03_select_object_features(self):
        """
        Select a some object features.
        """
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_feature_selection_applet = workflow.objectExtractionApplet
            gui = object_feature_selection_applet.getMultiLaneGui()
            op_object_features = object_feature_selection_applet.topLevelOperator.getLane(0)

            # activate the feature selection applet
            shell.setSelectedAppletDrawer(2)
            # let the gui catch up
            QApplication.processEvents()

            # make sure some preconditions are met:
            assert op_object_features.RawImage.ready()
            assert op_object_features.BinaryImage.ready()

            # we cannot test the feature-selection dialog here, as it's modal.
            # we therefore select a set of object features (all of them) and
            # supply them to the operator directly
            features, _ = gui.currentGui()._populate_feature_dict(op_object_features)

            # don't use test features
            features = {
                plugin: features[plugin]
                for plugin in features if 'test' not in plugin.lower()}

            # don't use advanced features
            features = {
                plugin: {feature: features[plugin][feature]
                         for feature in features[plugin]
                         if not features[plugin][feature].get('advanced', False)}
                for plugin in features
            }

            op_object_features.Features.setValue(features)
            # save a flattened list of feature names for the export applet
            # we should really use the same format in all the applets
            TestObjectClassificationGui.selected_feature_ids = [
                feature_id
                for plugin in features
                for feature_id in features[plugin].keys()
            ]

            # now trigger computation of features
            gui.currentGui()._calculateFeatures()

            # Let the GUI catch up: Process all events
            QApplication.processEvents()
            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

            # check the number of computed features:
            # dictionary has the format {time_slice: {plugin_name: {feature_name: [...]}}}
            computed_features = op_object_features.RegionFeatures[0].wait()[0]
            assert isinstance(computed_features, dict)
            for plugin in features:
                assert plugin in computed_features, f"Could not find plugin {plugin}"
                for feature_name in features[plugin]:
                    # feature names are altered in the operator:
                    feature_name_in_result = feature_name.split(' ')[0]
                    assert feature_name_in_result in computed_features[plugin], (
                        f"Could not find feature {feature_name_in_result}"
                        f"\n{computed_features[plugin].keys()}")

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_04_do_labeling(self):
        """
        Label some objects
        """
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_classification_applet = workflow.objectClassificationApplet
            gui = object_classification_applet.getMultiLaneGui()
            op_object_classification = object_classification_applet.topLevelOperator.getLane(0)

            # activate the object classification applet
            shell.setSelectedAppletDrawer(3)
            # let the gui catch up
            QApplication.processEvents()

            # Do our tests at position 0, 0, 0
            gui.currentGui().editor.posModel.slicingPos = (0, 0, 0)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, (
                "Got {} rows".format(gui.currentGui()._labelControlUi.labelListModel.rowCount()))

            # Add label classes
            for i in range(3, 5):
                gui.currentGui()._labelControlUi.AddLabelButton.click()
                assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == i, (
                    f"Got {gui.currentGui()._labelControlUi.labelListModel.rowCount()} rows")

            # Now delete the last two labels again
            gui.currentGui()._labelControlUi.labelListModel.removeRow(3)
            gui.currentGui()._labelControlUi.labelListModel.removeRow(2)
            assert op_object_classification.NumLabels.value == 2

            # Now check that the remaining two labels cannot be deleted:
            gui.currentGui()._labelControlUi.labelListModel.removeRow(1)
            gui.currentGui()._labelControlUi.labelListModel.removeRow(0)
            assert op_object_classification.NumLabels.value == 2
            # Add some labels, we use onClick directly in order to bypass problems with painting
            # on different screen resolutions
            # position: t, x, y, z, c
            label_position = namedtuple('label_position', ['label', 'position'])
            label_positions = [
                label_position(0, (0, 10, 10, 10, 0)),  # obj 1
                label_position(1, (0, 50, 5, 5, 0)),    # obj 2
                label_position(1, (0, 48, 10, 48, 0)),  # obj 14
                label_position(1, (0, 15, 59, 48, 0)),  # obj 21
            ]
            for lp in label_positions:
                gui.currentGui()._labelControlUi.labelListModel.select(lp.label)
                gui.currentGui().onClick(layer='unused', pos5d=lp.position, pos='unused')
            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

            label_list = op_object_classification.LabelInputs[0].wait()[0]
            expected_labels = numpy.zeros_like(label_list)
            layer = gui.currentGui().getLayer('Labels')
            for lp in label_positions:
                obj = gui.currentGui()._getObject(layer.segmentationImageSlot, lp.position)
                expected_labels[obj] = lp.label + 1

            numpy.testing.assert_array_equal(label_list, expected_labels)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_05_live_update_mode(self):
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_classification_applet = workflow.objectClassificationApplet
            gui = object_classification_applet.getMultiLaneGui()

            # activate the object classification applet
            shell.setSelectedAppletDrawer(3)
            # let the gui catch up
            QApplication.processEvents()

            with Timer() as timer:
                # Enable interactive mode
                assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False
                gui.currentGui()._labelControlUi.liveUpdateButton.click()
                assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is True
                # Do to the way we wait for the views to finish rendering, the GUI hangs while we wait.
                self.waitForViews(gui.currentGui().editor.imageViews)
            logger.debug(f"Interactive Mode Rendering Time: {timer.seconds()}")

            # Disable iteractive mode.
            gui.currentGui()._labelControlUi.liveUpdateButton.click()
            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False

            # There should be a prediction layer for each label
            labelNames = [label.name for label in gui.currentGui().labelListData]
            labelColors = gui.currentGui()._colorTable16[1:4]
            for i, labelName in enumerate(labelNames):
                try:
                    index = gui.currentGui().layerstack.findMatchingIndex(
                        lambda layer: labelName in layer.name)
                    layer = gui.currentGui().layerstack[index]

                    # Check the color
                    assert isinstance(layer, AlphaModulatedLayer), f"layer is {layer}"
                    assert layer.tintColor.rgba() == labelColors[i], (
                        f"Expected {hex(labelColors[i])}, got {hex(layer.tintColor.rgba())}")
                except ValueError:
                    assert False, "Could not find layer for label with name: {}".format(labelName)

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

            self.waitForViews(gui.currentGui().editor.imageViews)

        self.exec_in_shell(impl)

    def test_06_export(self):
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_export_applet = workflow.dataExportApplet
            gui = object_export_applet.getMultiLaneGui()
            op_object_export = object_export_applet.topLevelOperator.getLane(0)
            object_classification_applet = workflow.objectClassificationApplet
            op_object_classification = object_classification_applet.topLevelOperator.getLane(0)
            op_object_export_tlo = object_export_applet.topLevelOperator

            # activate the object information export applet
            shell.setSelectedAppletDrawer(4)
            # let the gui catch up
            QApplication.processEvents()

            op_object_export.OutputFilenameFormat.setValue(self.output_file)
            op_object_export.OutputFormat.setValue('hdf5')
            op_object_export.OutputInternalPath.setValue('exported_data')

            initial_table_export_settings = {
                "file type": 'csv',
                "file path": self.table_csv_file,
                "normalize": True,  # self.ui.normalizeLabeling.checkState() == Qt.Checked,
                "margin": 3,
                "include raw": False,
                # compression settings cannot be edited in the gui atm.
                # values here are assumed defaults (taken from exportObjectInfoDialog.ui)
                'compression': {
                    'compression': 'gzip',
                    'shuffle': False,
                    'compression_opts': 9
                }
            }
            table_export_settings, export_features = self.configure_export_dialog(
                gui, initial_table_export_settings)
            # here is some awkwardness of the csv output, which will alter the
            # table name: some_name.csv -> some_name_test_data_table.csv
            base, ext = os.path.splitext(self.table_csv_file)
            csv_out = f"{base}-test_data_table{ext}"
            TestObjectClassificationGui.table_csv_file_exported = csv_out

            op_object_classification.configure_table_export_settings(
                table_export_settings,
                export_features)

            # self.configure_export_dialog(op_object_export_tlo)

            with Timer() as timer:
                # this will not properly wait for the export to finish.
                # gui.drawer.exportAllButton.click()
                gui.exportSlots(op_object_export_tlo)

            assert object_export_applet.busy is False
            assert os.path.exists(csv_out), f"Could not find {csv_out}"
            assert os.path.exists(self.output_file)
            logger.debug(f"Export time (data + csv): {timer.seconds()}")

            initial_table_export_settings.update({
                "file type": 'h5',
                "file path": self.table_h5_file
            })

            table_export_settings, export_features = self.configure_export_dialog(
                gui, initial_table_export_settings)

            # here is some awkwardness of the h5 output, which will alter the
            # table name: some_name.h5 -> some_name_test_data.h5
            base, ext = os.path.splitext(self.table_h5_file)
            h5_out = f"{base}-test_data{ext}"
            TestObjectClassificationGui.table_h5_file_exported = h5_out

            op_object_classification.configure_table_export_settings(
                table_export_settings,
                export_features)

            with Timer() as timer:
                # this will not properly wait for the export to finish.
                # gui.drawer.exportAllButton.click()
                gui.exportSlots(op_object_export_tlo)

            assert object_export_applet.busy is False
            assert os.path.exists(h5_out), f"Could not find {h5_out}"
            assert os.path.exists(self.output_file)
            logger.debug(f"Export time (data + h5): {timer.seconds()}")

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        self.exec_in_shell(impl)

    def test_07_verify_exported_data(self):
        reference_data_file = h5py.File(self.reference_files['predictions_h5'], 'r')
        reference_data = reference_data_file['exported_data']
        generated_data_file = h5py.File(self.output_file, 'r')
        assert 'exported_data' in generated_data_file
        generated_data = generated_data_file['exported_data']

        try:
            numpy.testing.assert_array_almost_equal(generated_data, reference_data, decimal=5)
        finally:
            reference_data_file.close()
            generated_data_file.close()

    def test_08_verify_exported_csv_table(self):
        try:
            reference_csv_file = open(self.reference_files['csv_table'], 'r')
            reference_csv = csv.DictReader(reference_csv_file)
            generated_csv_file = open(self.table_csv_file_exported, 'r')
            generated_csv = csv.DictReader(generated_csv_file)

            # fieldnames are not necessarily in the same order
            # maybe I'm setting the export fieldnames wrong in test_06
            assert len(reference_csv.fieldnames) == len(generated_csv.fieldnames)
            for field_name in reference_csv.fieldnames:
                assert field_name in generated_csv.fieldnames, f"{field_name} not in the generated table"

            for row_a, row_b in zip(generated_csv, reference_csv):
                for field_name in reference_csv.fieldnames:
                    compare_values(row_a[field_name], row_b[field_name])
        finally:
            reference_csv_file.close()
            generated_csv_file.close()

    def test_09_verify_exported_h5_table(self):
        try:
            reference_h5_file = h5py.File(self.reference_files['h5_table'], 'r')
            generated_h5_file = h5py.File(self.table_h5_file_exported, 'r')

            # use this to compare image masks of the exported regions
            def compare(name, obj):
                assert name in reference_h5_file
                if not isinstance(obj, h5py.Dataset):
                    return
                if 'images' in name:
                    robj = reference_h5_file[name]
                    numpy.testing.assert_array_almost_equal(obj, robj)

            generated_h5_file.visititems(compare)

            # Now compare the table dataset
            reference_h5_table = reference_h5_file['table']
            generated_h5_table = generated_h5_file['table']
            types = reference_h5_table.dtype.fields
            for col_name, col_type in types.items():
                if col_type[0].type == numpy.string_:
                    numpy.testing.assert_array_equal(
                        generated_h5_table[col_name], reference_h5_table[col_name])
                else:
                    # will not work with higher precision, this is most likely
                    # due to small training set
                    assert numpy.allclose(
                        generated_h5_table[col_name], reference_h5_table[col_name], atol=0.2), (
                        f"column_name; {col_name}")

        finally:
            reference_h5_file.close()
            generated_h5_file.close()

    def test_10_compare_h5_and_csv_export(self):
        try:
            generated_h5_file = h5py.File(self.table_h5_file_exported, 'r')
            generated_csv_file = open(self.table_csv_file_exported, 'r')
            generated_csv = csv.DictReader(generated_csv_file)

            generated_csv_table = {col_name: [] for col_name in generated_csv.fieldnames}
            for row in generated_csv:
                for k, v in row.items():
                    generated_csv_table[k].append(v)

            # Now compare the table dataset
            generated_h5_table = generated_h5_file['table']
            types = generated_h5_table.dtype.fields
            for col_name, col_type in types.items():
                assert col_name in generated_csv_table
                if col_type[0].type == numpy.string_:
                    numpy.testing.assert_array_equal(
                        generated_h5_table[col_name],
                        numpy.array(generated_csv_table[col_name], dtype=col_type[0]))
                else:
                    assert numpy.allclose(
                        generated_h5_table[col_name],
                        numpy.array(generated_csv_table[col_name], dtype=col_type[0]),
                        atol=0.001), (
                        f"found erros in column {col_name}",)

        finally:
            generated_csv_file.close()
            generated_h5_file.close()

    def configure_export_dialog(self, gui, initial_settings):
        dimensions = gui.get_raw_shape()
        feature_names = gui.get_feature_names()
        op = gui.get_exporting_operator()
        settings, selected_features = op.get_table_export_settings()

        dialog = ExportObjectInfoDialog(
            dimensions,
            feature_names,
            selected_features=selected_features,
            title=gui.get_export_dialog_title(),
            initial_settings=settings)

        dialog.show()
        QApplication.processEvents()
        # do the interaction with the dialog
        file_type = initial_settings['file type']
        index = FILE_TYPES.index(file_type)
        dialog.ui.fileFormat.setCurrentIndex(index)

        file_path = initial_settings['file path']
        dialog.ui.exportPath.setText(file_path)

        if file_type == 'h5':
            # TODO: what about normalize?
            margin = initial_settings['margin']
            dialog.ui.addMargin.setValue(margin)
            include_raw = initial_settings['include raw']
            dialog.ui.includeRaw.setChecked(include_raw)
            compression_settings = initial_settings['compression']
            compression_type = compression_settings['compression']
            index = dialog.ui.compressionType.findText(compression_type)
            dialog.ui.compressionType.setCurrentIndex(index)
            shuffle = compression_settings['shuffle']
            dialog.ui.enableShuffling.setChecked(shuffle)
            compression_rate = compression_settings['compression_opts']
            dialog.ui.gzipRate.setValue(compression_rate)

        dialog.ui.selectAllFeatures.click()
        QApplication.processEvents()

        dialog.close()
        QApplication.processEvents()
        settings = dialog.settings()
        selected_features = list(dialog.checked_features())
        return settings, selected_features


def compare_values(test_value, reference_value):
    """Assumes all values come in as strings, but could also hold numbers
    Args:
        test_value: value to test against test_value
        reference_value: reference value to compare to, type here determines
          type of comparison
    """
    rval, rtype = try_convert_to_numeric(reference_value)
    tval = rtype(test_value)

    if rtype in (str, int):
        assert tval == rval, f"{tval} != {rval}"
    elif isinstance(reference_value, float):
        assert numpy.allclose(test_value, reference_value, atol=0.2)


def try_convert_to_numeric(val):
    try:
        ret_val = int(val)
        ret_type = int
        return ret_val, ret_type
    except ValueError:
        pass

    try:
        ret_val = float(val)
        ret_type = float
        return ret_val, ret_type
    except ValueError:
        pass

    return val, str


if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test
    run_shell_test(__file__)
