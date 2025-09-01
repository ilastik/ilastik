###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2025, the ilastik developers
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
import csv
import os
import shutil
import tempfile
from collections import namedtuple
from enum import IntEnum
from pathlib import Path
from typing import Union

import h5py
import numpy
import numpy.typing as npt
import pytest
from qtpy.QtWidgets import QApplication

from ilastik.applets.dataSelection.opDataSelection import FilesystemDatasetInfo
from ilastik.applets.objectClassification import ObjectClassificationApplet
from ilastik.applets.objectExtraction.opObjectExtraction import OpObjectExtractionFromLabels
from ilastik.widgets.exportObjectInfoDialog import FILE_TYPES, ExportObjectInfoDialog
from ilastik.workflows.objectClassification.objectClassificationWorkflow import ObjectClassificationWorkflowLabels
from tests.test_ilastik.helpers import ShellGuiTestCaseBase


def read_h5_ds(file_path: Union[str, Path], dataset: str) -> npt.ArrayLike:
    with h5py.File(file_path, "r") as f:
        return f[dataset][()]


def read_csv_table(file_path: str):
    with open(file_path, "r") as f:
        csv_data = list(csv.DictReader(f))
    return csv_data


class TestObjectClassificationWorkflowLabels(ShellGuiTestCaseBase):

    @classmethod
    def workflowClass(cls):
        return ObjectClassificationWorkflowLabels

    @classmethod
    def setup_class(cls):
        super().setup_class()

        # input files
        current_dir = Path(__file__).parent.resolve()
        cls.raw_data_file_0 = current_dir.parent / "data" / "inputdata" / "smallVideo.h5"
        cls.label_data_file_0 = current_dir.parent / "data" / "inputdata" / "smallVideo_labels.h5"
        cls.raw_data_file_1 = current_dir.parent / "data" / "inputdata" / "smallVideo_x0-170.h5"
        cls.label_data_file_1 = current_dir.parent / "data" / "inputdata" / "smallVideo_x0-170-labels.h5"

        # output files
        cls.temp_dir = tempfile.mkdtemp()

        cls.project_file = os.path.join(cls.temp_dir, "test_project_labels.ilp")
        cls.table_csv_file = os.path.join(cls.temp_dir, "{nickname}.csv")
        cls.output_file = os.path.join(cls.temp_dir, "{nickname}_output.h5")
        # cls.output_table_file = os.path.join(cls.temp_dir, "output_table.h5")

        cls.selected_plugin = "Standard Object Features"
        cls.selected_features = ["Count", "Sum"]

        cls.expected_relabeling_0 = numpy.array(
            [
                {9: 3, 6: 2, 3: 1, 0: 0},
                {6: 2, 3: 1, 0: 0},
                {6: 2, 3: 1, 0: 0},
                {9: 3, 6: 2, 3: 1, 0: 0},
                {9: 3, 6: 2, 3: 1, 0: 0},
                {12: 4, 9: 3, 6: 2, 3: 1, 0: 0},
                {12: 4, 9: 3, 6: 2, 3: 1, 0: 0},
            ]
        )

        cls.expected_relabeling_1 = numpy.array(
            [
                {126: 2, 42: 1, 0: 0},
                {42: 1, 0: 0},
                {3: 2, 42: 1, 0: 0},
                {126: 2, 42: 1, 0: 0},
                {126: 2, 42: 1, 0: 0},
                {168: 3, 3: 2, 42: 1, 0: 0},
                {168: 3, 3: 2, 42: 1, 0: 0},
            ]
        )

        class AppletIndex(IntEnum):
            DATASELECTION = 0
            OBJECT_FEATURE_SELCTION = 1
            OBJECT_CLASSIFICATION = 2
            OBJECT_EXPORT = 3

        cls.APPLETINEX = AppletIndex

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        super().teardown_class()

    def test_00_check_inputs_exist(self):
        """Make sure the needed files exist"""
        needed_files = [self.raw_data_file_0, self.label_data_file_0, self.raw_data_file_1, self.label_data_file_1]
        for f in needed_files:
            assert os.path.exists(f), f"File {f} does not exist!"

        # check that object ids are not consecutive
        numpy.testing.assert_array_equal(numpy.unique(read_h5_ds(self.label_data_file_0, "labels")), [0, 3, 6, 9, 12])
        numpy.testing.assert_array_equal(
            numpy.unique(read_h5_ds(self.label_data_file_1, "labels")), [0, 3, 42, 126, 168]
        )

    def test_01_create_project(self):
        """
        Test the workflow with two lanes and verify the exported table for original object IDs.
        """

        def impl():
            shell = self.shell

            # Create a new project
            shell.createAndLoadNewProject(self.project_file, self.workflowClass())
            workflow = shell.projectManager.workflow

            # Add two lanes with raw and label images
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.DatasetGroup.resize(2)

            opDataSelection.DatasetGroup[0][0].setValue(FilesystemDatasetInfo(filePath=str(self.raw_data_file_0)))
            opDataSelection.DatasetGroup[0][1].setValue(FilesystemDatasetInfo(filePath=str(self.label_data_file_0)))
            opDataSelection.DatasetGroup[1][0].setValue(FilesystemDatasetInfo(filePath=str(self.raw_data_file_1)))
            opDataSelection.DatasetGroup[1][1].setValue(FilesystemDatasetInfo(filePath=str(self.label_data_file_1)))

            shell.projectManager.saveProject()

        self.exec_in_shell(impl)

    def test_02_object_relabeling(self):
        """
        Swtich to feature selection and check if data has been relabeled.
        """

        def impl():
            shell = self.shell
            shell.setSelectedAppletDrawer(self.APPLETINEX.OBJECT_FEATURE_SELCTION)
            QApplication.processEvents()

            workflow = shell.projectManager.workflow
            object_feature_selection_applet = workflow.objectExtractionApplet

            op_object_features_1: OpObjectExtractionFromLabels = (
                object_feature_selection_applet.topLevelOperator.getLane(1)
            )

            assert op_object_features_1.LabelImage.ready()
            assert op_object_features_1.RelabelDict.ready()

            relabel_dicts_1 = op_object_features_1.RelabelDict[0:7].wait()
            assert relabel_dicts_1.shape == (7,)

            for relabel_dict, relabel_dict_expected in zip(relabel_dicts_1, self.expected_relabeling_1):
                assert len(relabel_dict) == len(relabel_dict_expected)
                for k, v in relabel_dict.items():
                    assert relabel_dict_expected[k] == v

            op_object_features_0: OpObjectExtractionFromLabels = (
                object_feature_selection_applet.topLevelOperator.getLane(0)
            )

            assert op_object_features_0.LabelImage.ready()
            assert op_object_features_0.RelabelDict.ready()

            relabel_dicts_0 = op_object_features_0.RelabelDict[0:7].wait()
            assert relabel_dicts_0.shape == (7,)

            for relabel_dict, relabel_dict_expected in zip(relabel_dicts_0, self.expected_relabeling_0):
                assert len(relabel_dict) == len(relabel_dict_expected)
                for k, v in relabel_dict.items():
                    assert relabel_dict_expected[k] == v

        self.exec_in_shell(impl)

    def test_03_closed_state(self):
        """
        Close the project and check UI state is empty.
        """

        def impl():
            self.shell.ensureNoCurrentProject(assertClean=True)
            assert self.shell.projectManager is None
            assert self.shell.appletBar.count() == 0

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_04_reopen_project(self):
        def impl():
            self.shell.openProjectFile(self.project_file)
            assert self.shell.projectManager.currentProjectFile is not None
            assert isinstance(
                self.shell.workflow.applets[self.APPLETINEX.OBJECT_CLASSIFICATION], ObjectClassificationApplet
            )

        self.exec_in_shell(impl)

    def test_05_select_object_features(self):
        """
        Select some object features and check they are computed.
        """

        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_feature_selection_applet = workflow.objectExtractionApplet

            shell.setSelectedAppletDrawer(self.APPLETINEX.OBJECT_FEATURE_SELCTION)
            QApplication.processEvents()
            shell.imageSelectionCombo.setCurrentIndex(1)
            QApplication.processEvents()

            gui = object_feature_selection_applet.getMultiLaneGui()
            op_object_features_1 = object_feature_selection_applet.topLevelOperator.getLane(1)

            # preconditions
            assert op_object_features_1.RawImage.ready()
            assert op_object_features_1.SegmentationImage.ready()

            # we cannot test the feature-selection dialog here, as it's modal.
            # we therefore select a set of object features and
            # supply them to the operator directly
            features, _ = gui.currentGui()._populate_feature_dict(op_object_features_1)

            features = {
                self.selected_plugin: {feat: features[self.selected_plugin][feat] for feat in self.selected_features}
            }

            op_object_features_1.Features.setValue(features)
            # save a flattened list of feature names for the export applet
            # we should really use the same format in all the applets
            self.selected_feature_ids = [feature_id for plugin in features for feature_id in features[plugin].keys()]

            # now trigger computation of features
            gui.currentGui()._calculateFeatures()

            # Let the GUI catch up: Process all events
            QApplication.processEvents()
            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

            # check the number of computed features:
            # dictionary has the format {time_slice: {plugin_name: {feature_name: [...]}}}
            computed_features = op_object_features_1.RegionFeatures[0].wait()[0]
            assert isinstance(computed_features, dict)
            for plugin in features:
                assert plugin in computed_features, f"Could not find plugin {plugin}"
                for feature_name in features[plugin]:
                    assert feature_name in computed_features[plugin], (
                        f"Could not find feature {feature_name}" f"\n{computed_features[plugin].keys()}"
                    )

        self.exec_in_shell(impl)

    @pytest.mark.usefixtures("reliable_vigra_train_rf_seed")
    def test_06_label_and_train(self):
        """
        Label some objects and check that classifier is trained.
        """

        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_classification_applet = workflow.objectClassificationApplet
            gui = object_classification_applet.getMultiLaneGui()
            op_object_classification = object_classification_applet.topLevelOperator.getLane(0)

            # activate the object classification applet
            shell.setSelectedAppletDrawer(self.APPLETINEX.OBJECT_CLASSIFICATION)
            QApplication.processEvents()

            assert op_object_classification.Classifier.value is None

            # Do our tests at position 0, 0, 0
            gui.currentGui().editor.posModel.slicingPos = (0, 0, 0)
            gui.currentGui().editor.posModel.time = 5

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Got {} rows".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            assert op_object_classification.NumLabels.value == 2

            # position: t, x, y, z, c
            label_position = namedtuple("label_position", ["label", "position"])
            label_lane_0 = label_position(1, (5, 156, 161, 0, 0))
            shell.imageSelectionCombo.setCurrentIndex(0)
            QApplication.processEvents()
            gui.currentGui()._labelControlUi.labelListModel.select(label_lane_0.label)
            gui.currentGui().onClick(layer="unused", pos5d=label_lane_0.position, pos="unused")

            label_lane_1 = label_position(0, (2, 127, 264, 0, 0))
            shell.imageSelectionCombo.setCurrentIndex(1)
            QApplication.processEvents()
            gui.currentGui()._labelControlUi.labelListModel.select(label_lane_1.label)
            gui.currentGui().onClick(layer="unused", pos5d=label_lane_1.position, pos="unused")

            QApplication.processEvents()

            self.waitForViews(gui.currentGui().editor.imageViews)

            # train the classifier
            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False
            gui.currentGui()._labelControlUi.liveUpdateButton.click()
            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is True
            # Do to the way we wait for the views to finish rendering, the GUI hangs while we wait.
            self.waitForViews(gui.currentGui().editor.imageViews)

            # Disable iteractive mode.
            gui.currentGui()._labelControlUi.liveUpdateButton.click()

            assert op_object_classification.Classifier.value is not None

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        self.exec_in_shell(impl)

    def test_07_export(self):
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            object_export_applet = workflow.dataExportApplet

            gui = object_export_applet.getMultiLaneGui()
            op_object_export = object_export_applet.topLevelOperator.getLane(0)
            op_object_export_tlo = object_export_applet.topLevelOperator

            # activate the object information export applet
            shell.setSelectedAppletDrawer(self.APPLETINEX.OBJECT_EXPORT)
            # let the gui catch up
            QApplication.processEvents()

            op_object_export.OutputFilenameFormat.setValue(self.output_file)
            op_object_export.OutputFormat.setValue("hdf5")
            op_object_export.OutputInternalPath.setValue("exported_data")
            op_object_export.InputSelection.setValue(workflow.ExportNames.OBJECT_PROBABILITIES)

            # here is some awkwardness of the csv output, which will alter the
            # table name: some_name.csv -> some_name_test_data_table.csv
            base, ext = os.path.splitext(self.table_csv_file)
            csv_out = f"{base}_table{ext}"

            table_export_settings = {
                "file type": "csv",
                "file path": self.table_csv_file,
                "compression": {},
            }

            exporter = gui.get_exporting_operator()

            exporter.configure_table_export_settings(table_export_settings, [])

            gui.exportSync(op_object_export_tlo)

            assert object_export_applet.busy is False
            op_data_selection = workflow.dataSelectionApplet.topLevelOperator

            for i in range(2):
                nickname = op_data_selection.getLane(i).get_dataset_info("Raw Data").nickname
                table_name = csv_out.format(nickname=nickname)
                assert os.path.exists(table_name), f"Could not find {table_name}"
                output_file = self.output_file.format(nickname=nickname)
                assert os.path.exists(output_file), f"Could not find {output_file}"

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        self.exec_in_shell(impl)

    def test_08_check_csv_labelid_mapping(self):
        """
        Open the csv files and verify that relabel mapping is correct.
        """

        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            op_data_selection = workflow.dataSelectionApplet.topLevelOperator

            base, ext = os.path.splitext(self.table_csv_file)
            csv_out = f"{base}_table{ext}"

            for lane_index, expected_dict in zip(range(2), (self.expected_relabeling_0, self.expected_relabeling_1)):
                nickname = op_data_selection.getLane(lane_index).get_dataset_info("Raw Data").nickname
                csv_data = read_csv_table(csv_out.format(nickname=nickname))
                assert csv_data

                for row in csv_data:
                    t = int(row["timestep"])
                    original_oid = int(row["original_oid"])
                    ilastik_oid = int(row["labelimage_oid"])
                    assert expected_dict[t][original_oid] == ilastik_oid, row

        self.exec_in_shell(impl)

    def test_09_check_obj_probabilities(self):
        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            op_data_selection = workflow.dataSelectionApplet.topLevelOperator
            base, ext = os.path.splitext(self.table_csv_file)
            csv_out = f"{base}_table{ext}"

            for lane_index in range(2):
                nickname = op_data_selection.getLane(lane_index).get_dataset_info("Raw Data").nickname
                image_path = self.output_file.format(nickname=nickname)
                assert Path(image_path).exists()
                img = read_h5_ds(image_path, "exported_data")
                res_dtype = img.dtype
                assert img.sum() > 0, "Probabilities should not be all zero"
                assert numpy.unique(img).size > 1, "There should be various probability values, not just one"
                csv_data = read_csv_table(csv_out.format(nickname=nickname))
                for row in csv_data:
                    # compare center of the object has the same value as table entry
                    t = int(row["timestep"])
                    x = int(float(row["Center of the object_0"]))
                    y = int(float(row["Center of the object_1"]))
                    prob0 = res_dtype.type(row["Probability of Label 1"])
                    prob1 = res_dtype.type(row["Probability of Label 2"])
                    numpy.testing.assert_almost_equal(img[t, y, x, :], [prob0, prob1])

        self.exec_in_shell(impl)

    def configure_export_dialog(self, gui):
        dimensions = gui.get_raw_shape()
        feature_names = gui.get_feature_names()
        op = gui.get_exporting_operator()
        settings, selected_features = op.get_table_export_settings()

        dialog = ExportObjectInfoDialog(
            dimensions,
            feature_names,
            selected_features=selected_features,
            title=gui.get_export_dialog_title(),
            initial_settings=settings,
        )

        dialog.show()
        QApplication.processEvents()

        index = FILE_TYPES.index("csv")
        dialog.ui.fileFormat.setCurrentIndex(index)
        dialog.ui.exportPath.setText(self.table_csv_file)

        dialog.ui.selectAllFeatures.click()
        QApplication.processEvents()

        dialog.accept()
        QApplication.processEvents()
