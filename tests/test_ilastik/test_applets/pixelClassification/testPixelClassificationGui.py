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
# 		   http://ilastik.org/license.html
###############################################################################
import os
from pathlib import Path
import sys
import tempfile
import pytest
import numpy
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QAction
from volumina.layer import AlphaModulatedLayer
from ilastik.widgets.stackFileSelectionWidget import SubvolumeSelectionDlg

from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from lazyflow.utility.timer import Timer, timeLogged

from tests.test_ilastik.helpers import ShellGuiTestCaseBase
from tests.test_ilastik.helpers.wait import wait_until, wait_signal, wait_slot_ready

from ilastik.applets.pixelClassification.pixelClassificationApplet import PixelClassificationApplet
from ilastik.applets.pixelClassification.suggestFeaturesDialog import SuggestFeaturesDialog

DATA_SELECTION_INDEX = 0
PIXEL_CLASSIFICATION_INDEX = 2

import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
# logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)


class TestPixelClassificationGui(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the pixel classification workflow.

    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """

    @pytest.fixture(autouse=True)
    def initenv(self, qtbot, monkeypatch, tmp_path: Path, tmp_h5_single_dataset: Path, tmp_h5_multiple_dataset: Path):
        # FIXME: it might be a good idea to have this apply globally, for every test, so we don't polute the real HOME
        monkeypatch.setenv("HOME", str(tmp_path))
        self.qtbot = qtbot
        self.tmp_path = tmp_path
        self.tmp_h5_single_dataset = tmp_h5_single_dataset
        self.tmp_h5_multiple_dataset = tmp_h5_multiple_dataset

    @classmethod
    def workflowClass(cls):
        return PixelClassificationWorkflow

    dir = tempfile.mkdtemp()
    PROJECT_FILE = os.path.join(dir, "test_project.ilp")
    # SAMPLE_DATA = os.path.split(__file__)[0] + '/synapse_small.npy'

    @classmethod
    def setup_class(cls):
        # Base class first
        super(TestPixelClassificationGui, cls).setup_class()

        if hasattr(cls, "SAMPLE_DATA"):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.SAMPLE_DATA = os.path.split(__file__)[0] + "/random_data.npy"
            data = numpy.random.random((1, 50, 200, 200, 1))
            data *= 256
            numpy.save(cls.SAMPLE_DATA, data.astype(numpy.uint8))

        # Start the timer
        cls.timer = Timer()
        cls.timer.unpause()

    @classmethod
    def teardown_class(cls):
        cls.timer.pause()
        logger.debug("Total Time: {} seconds".format(cls.timer.seconds()))

        # Call our base class so the app quits!
        super(TestPixelClassificationGui, cls).teardown_class()

        # Clean up: Delete any test files we generated
        removeFiles = [TestPixelClassificationGui.PROJECT_FILE]
        if cls.using_random_data:
            removeFiles += [TestPixelClassificationGui.SAMPLE_DATA]

        for f in removeFiles:
            try:
                os.remove(f)
            except:
                pass

    @property
    def data_selection_gui(self):
        return self.shell.workflow.applets[DATA_SELECTION_INDEX].getMultiLaneGui()

    def add_file(self, path: Path, inner_path: str = ""):
        model = self.data_selection_gui._detailViewerWidgets[0].model()
        with wait_signal(model.rowsInserted):
            add_file_role_0_button = self.data_selection_gui.laneSummaryTableView.addFilesButtons[0]
            add_file_role_0_button.click()
            add_file_role_0_button.menu().actions()[0].activate(QAction.Trigger)
            self.select_file(path)
            if inner_path:
                self.select_inner_path(inner_path)

    def select_file(self, path: Path):
        file_dialog = wait_until(QApplication.instance().activeModalWidget)
        file_dialog.selectFile(path.as_posix())
        lineEdit = file_dialog.focusWidget()
        lineEdit.setText(str(path))
        file_dialog.accept()

    def select_inner_path(self, inner_path: str):
        wait_until(lambda: isinstance(QApplication.instance().activeModalWidget(), SubvolumeSelectionDlg))
        inner_path_dialog = QApplication.instance().activeModalWidget()
        matching_idx = inner_path_dialog.combo.findText(inner_path)
        assert matching_idx >= 0
        inner_path_dialog.combo.setCurrentIndex(matching_idx)
        inner_path_dialog.accept()

    def remove_first_dataset(self):
        model = self.data_selection_gui._detailViewerWidgets[0].model()
        with wait_signal(model.rowsRemoved):
            self.data_selection_gui._detailViewerWidgets[0].overlay.placeAtRow(0)
            self.data_selection_gui._detailViewerWidgets[0].overlay.current_row = 0
            self.data_selection_gui._detailViewerWidgets[0].overlay.click()

    def test_00_CreateEmptyProject(self):
        self.exec_in_shell(self.shell.createAndLoadNewProject, self.PROJECT_FILE, self.workflowClass())
        assert os.path.exists(self.PROJECT_FILE)

    @pytest.mark.skip(
        reason="this part of the test hangs on all platforms, hangs/segfaults on any CI provider.",
    )
    def test_01_AddRemoveData(self):
        workflow = self.shell.projectManager.workflow
        opDataSelection = workflow.dataSelectionApplet.topLevelOperator
        # opens multi dataset file and expects second dialog to choose inner path
        self.add_file(self.tmp_h5_multiple_dataset, "/test_group_3d/test_data_3d")
        with wait_slot_ready(opDataSelection.get_lane(0).DatasetGroup[0]):
            assert (
                opDataSelection.get_lane(0).DatasetGroup[0].value.nickname
                == "multiple_datasets-test_group_3d-test_data_3d"
            )
        self.remove_first_dataset()

        # opens multi dataset file and expects inner path to be picked automatically
        self.add_file(self.tmp_h5_multiple_dataset)
        with wait_slot_ready(opDataSelection.get_lane(0).DatasetGroup[0]):
            assert (
                opDataSelection.get_lane(0).DatasetGroup[0].value.nickname
                == "multiple_datasets-test_group_3d-test_data_3d"
            )
        self.remove_first_dataset()

        # opens single dataset file and expects inner path to be picked automatically
        self.add_file(self.tmp_h5_single_dataset)
        with wait_slot_ready(opDataSelection.get_lane(0).DatasetGroup[0]):
            assert opDataSelection.get_lane(0).DatasetGroup[0].value.nickname == "single_dataset-test_group-test_data"
        self.remove_first_dataset()

    def test_1_NewProject(self):
        """
        Create a blank project, manipulate few couple settings, and save it.
        """
        workflow = self.shell.projectManager.workflow
        opDataSelection = workflow.dataSelectionApplet.topLevelOperator

        # FIXME: this part of the test doesn't work on windows, or on any CI (hang/segfault)

        def impl():
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, FilesystemDatasetInfo

            info = FilesystemDatasetInfo(
                filePath=self.SAMPLE_DATA, project_file=self.shell.projectManager.currentProjectFile
            )
            opDataSelection.DatasetGroup.resize(1)
            opDataSelection.DatasetGroup[0][0].setValue(info)

            # Set some features
            opFeatures = workflow.featureSelectionApplet.topLevelOperator
            #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
            selections = numpy.array(
                [
                    [1, 0, 0, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0, 0, 0],
                ]
            ).astype(bool)

            opFeatures.SelectionMatrix.setValue(selections)

            # Save and close
            self.shell.projectManager.saveProject()
            self.shell.ensureNoCurrentProject(assertClean=True)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_2_ClosedState(self):
        """
        Check the state of various shell and gui members when no project is currently loaded.
        """

        def impl():
            assert self.shell.projectManager is None
            assert self.shell.appletBar.count() == 0

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_3_OpenProject(self):
        def impl():
            self.shell.openProjectFile(self.PROJECT_FILE)
            assert self.shell.projectManager.currentProjectFile is not None
            assert isinstance(self.shell.workflow.applets[PIXEL_CLASSIFICATION_INDEX], PixelClassificationApplet)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    # These points are relative to the CENTER of the view
    LABEL_START = (-20, -20)
    LABEL_STOP = (20, 20)
    LABEL_SAMPLE = (0, 0)
    LABEL_ERASE_START = (-10, -10)
    LABEL_ERASE_STOP = (10, 10)

    @timeLogged(logger, logging.INFO)
    def test_4_AddLabels(self):
        """
        Add labels and draw them in the volume editor.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opPix = pixClassApplet.topLevelOperator

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(PIXEL_CLASSIFICATION_INDEX)

            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()

            ## Turn off the slicing position lines
            ## FIXME: This disables the lines without unchecking the position
            ##        box in the VolumeEditorWidget, making the checkbox out-of-sync
            # gui.currentGui().editor.navCtrl.indicateSliceIntersection = False

            # Do our tests at position 0,0,0
            gui.currentGui().editor.posModel.slicingPos = (0, 0, 0)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Got {} rows".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            # Add label classes. we want three for the following tests. Two are initially added by the constructors.
            # Add one to the two existing ones:
            gui.currentGui()._labelControlUi.AddLabelButton.click()

            gui.currentGui()._labelControlUi.AddLabelButton.click()
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 4, "Got {} rows".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            # Select the brush
            gui.currentGui()._labelControlUi.paintToolButton.click()

            # Set the brush size
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(1)

            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            # Draw some arbitrary labels in each view using mouse events.
            for i in range(3):
                # Post this as an event to ensure sequential execution.
                gui.currentGui()._labelControlUi.labelListModel.select(i)

                imgView = gui.currentGui().editor.imageViews[i]
                self.strokeMouseFromCenter(imgView, self.LABEL_START, self.LABEL_STOP)

                # Make sure the labels were added to the label array operator
                labelData = opPix.LabelImages[0][:].wait()
                assert labelData.max() == i + 1, "Max label value was {}".format(labelData.max())

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Verify the actual rendering of each view
            for i in range(3):
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = gui.currentGui()._colorTable16[i + 1]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format(
                    hex(expectedColor), hex(observedColor)
                )

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    @timeLogged(logger, logging.INFO)
    def test_5_DeleteLabel(self):
        """
        Delete a label from the label list.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opPix = pixClassApplet.topLevelOperator

            originalLabelColors = gui.currentGui()._colorTable16[1:4]
            originalLabelNames = [label.name for label in gui.currentGui().labelListData]

            # We assume that there are three of the 4 labels drawn to start with (see previous test)
            labelData = opPix.LabelImages[0][:].wait()
            assert labelData.max() == 3, "Max label value was {}".format(labelData.max())
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 4, "Row count was {}".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            # Make sure that it's okay to delete a row even if the deleted label is selected.
            gui.currentGui()._labelControlUi.labelListModel.select(2)
            gui.currentGui()._labelControlUi.labelListModel.removeRow(2)
            # Delete a unselected row
            gui.currentGui()._labelControlUi.labelListModel.removeRow(2)

            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Row count was {}".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            # Make sure, the remaining two labels cannot be deleted
            gui.currentGui()._labelControlUi.labelListModel.removeRow(0)
            gui.currentGui()._labelControlUi.labelListModel.removeRow(1)

            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Row count was {}".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            # Selection should auto-reset back to the first row.
            assert gui.currentGui()._labelControlUi.labelListModel.selectedRow() == 0, "Row {} was selected.".format(
                gui.currentGui()._labelControlUi.labelListModel.selectedRow()
            )

            # Did the label get removed from the label array?
            labelData = opPix.LabelImages[0][:].wait()
            assert (
                labelData.max() == 2
            ), "Max label value did not decrement after the label was deleted.  Expected 2, got {}".format(
                labelData.max()
            )

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Check the actual rendering of the two views with remaining labels
            for i in [0, 1]:
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = originalLabelColors[i]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format(
                    hex(expectedColor), hex(observedColor)
                )

            # Make sure we actually deleted the third label(it should no longer be visible)
            for i in [2]:
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                oldColor = originalLabelColors[i]
                assert observedColor != oldColor, "Label was not deleted."

            # Original layer should not be anywhere in the layerstack.
            for layer in gui.currentGui().layerstack:
                assert layer.name is not originalLabelNames[1], "Layer {} was still present in the stack.".format(
                    layer.name
                )

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    @timeLogged(logger, logging.INFO)
    def test_6_EraseSome(self):
        """
        Erase a few of the previously drawn labels from the volume editor using the eraser.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(PIXEL_CLASSIFICATION_INDEX)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Row count was {}".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            # Use the first view for this test
            imgView = gui.currentGui().editor.imageViews[0]

            # Sanity check: There should be labels in the view that we can erase
            self.waitForViews([imgView])
            observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            labelColor = gui.currentGui()._colorTable16[1]
            assert (
                observedColor == labelColor
            ), "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format(
                hex(labelColor), hex(observedColor)
            )

            # Hide labels and sample raw data
            labelLayer = gui.currentGui().layerstack[0]
            assert labelLayer.name == "Labels", "Layer name was wrong: {}".labelLayer.name
            labelLayer.visible = False
            self.waitForViews([imgView])
            rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert (
                rawDataColor != labelColor
            ), "Pixel color was not correct after label was hidden.  rawDataColor: {}, labelColor: {}".format(
                hex(rawDataColor), hex(labelColor)
            )

            # Show labels
            labelLayer.visible = True
            # Select the eraser and brush size
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.waitForViews([imgView])

            # Erase and verify
            self.strokeMouseFromCenter(imgView, self.LABEL_ERASE_START, self.LABEL_ERASE_STOP)
            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert (
                erasedColor == rawDataColor
            ), "Pixel color was not correct after label was erased.  Expected {}, got {}".format(
                hex(rawDataColor), hex(erasedColor)
            )

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    @timeLogged(logger, logging.INFO)
    def test_7_EraseCompleteLabel(self):
        """
        Erase all of the labels of a particular color using the eraser.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opPix = pixClassApplet.topLevelOperator

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(PIXEL_CLASSIFICATION_INDEX)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Row count was {}".format(
                gui.currentGui()._labelControlUi.labelListModel.rowCount()
            )

            labelData = opPix.LabelImages[0][:].wait()
            assert labelData.max() == 2, "Max label value was wrong. Expected 2, got {}".format(labelData.max())

            # Use the second view for this test (which has the max label value)
            imgView = gui.currentGui().editor.imageViews[1]

            # Sanity check: There should be labels in the view that we can erase
            observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            labelColor = gui.currentGui()._colorTable16[2]
            assert (
                observedColor == labelColor
            ), "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format(
                hex(labelColor), hex(observedColor)
            )

            # Hide labels and sample raw data
            labelLayer = gui.currentGui().layerstack[0]
            assert labelLayer.name == "Labels"
            labelLayer.visible = False
            rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert (
                rawDataColor != labelColor
            ), "Pixel color was not correct after label was hidden.  rawDataColor: {}, labelColor: {}".format(
                hex(rawDataColor), hex(labelColor)
            )

            # Show labels
            labelLayer.visible = True
            # Select the eraser and brush size
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.waitForViews([imgView])

            # Erase and verify
            self.strokeMouseFromCenter(imgView, self.LABEL_START, self.LABEL_STOP)
            erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert erasedColor == rawDataColor, "Eraser did not remove labels! Expected {}, got {}".format(
                hex(rawDataColor), hex(erasedColor)
            )

            # We just erased all the labels of value 2, so the max label value should be reduced.
            labelData = opPix.LabelImages[0][:].wait()
            assert labelData.max() == 1, "Max label value was wrong. Expected 2, got {}".format(labelData.max())

            # Now stroke the eraser once more.
            # The new stroke should make NO DIFFERENCE to the image.
            rawDataColor = self.getPixelColor(imgView, (5, -5))
            self.strokeMouseFromCenter(imgView, (10, -10), (0, 0))

            erasedColor = self.getPixelColor(imgView, (5, -5))
            assert (
                erasedColor == rawDataColor
            ), "Erasing blank pixels generated non-zero labels. Expected {}, got {}".format(
                hex(rawDataColor), hex(erasedColor)
            )

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_8_InteractiveMode(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            # Clear all the labels
            while len(gui.currentGui()._labelControlUi.labelListModel) > 2:
                gui.currentGui()._labelControlUi.labelListModel.removeRow(2)

            # Re-add all labels
            self.test_4_AddLabels()

            # Make sure the entire slice is visible
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionFitToScreen.trigger()

            with Timer() as timer:
                # Enable interactive mode
                assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
                gui.currentGui()._labelControlUi.liveUpdateButton.click()

                # Do to the way we wait for the views to finish rendering, the GUI hangs while we wait.
                self.waitForViews(gui.currentGui().editor.imageViews)

            logger.debug("Interactive Mode Rendering Time: {}".format(timer.seconds()))

            # There should be a prediction layer for each label
            labelNames = [label.name for label in gui.currentGui().labelListData]
            labelColors = gui.currentGui()._colorTable16[1:5]
            for i, labelName in enumerate(labelNames):
                try:
                    index = gui.currentGui().layerstack.findMatchingIndex(lambda layer: labelName in layer.name)
                    layer = gui.currentGui().layerstack[index]

                    # Check the color
                    assert isinstance(layer, AlphaModulatedLayer), "layer is {}".format(layer)
                    assert layer.tintColor.rgba() == labelColors[i], "Expected {}, got {}".format(
                        hex(labelColors[i]), hex(layer.tintColor.rgba())
                    )
                except ValueError:
                    assert False, "Could not find layer for label with name: {}".format(labelName)

            # Disable iteractive mode.
            gui.currentGui()._labelControlUi.liveUpdateButton.click()

            self.waitForViews(gui.currentGui().editor.imageViews)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_91_suggestFeaturesDlg_close_no_change(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            gui.currentGui()._labelControlUi.suggestFeaturesButton.click()
            wait_until(lambda: isinstance(QApplication.instance().activeModalWidget(), SuggestFeaturesDialog))
            dlg = QApplication.instance().activeModalWidget()
            dlg.accept()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_92_suggestFeaturesDlg_run(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """

        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opFeatures = workflow.featureSelectionApplet.topLevelOperator

            # this time we want to trigger the message box that informs us,
            # that some sigmas can only be computed in 2D
            # so we add a sigma that doesn't fit into size of 50 along z:
            scales = [0.3, 0.7, 15.0]
            selections = numpy.array(
                [
                    [1, 0, 0],
                    [0, 1, 0],
                    [0, 1, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0]
                ]
            ).astype(bool)  # fmt: skip

            opFeatures.SelectionMatrix.setValue(None)
            opFeatures.Scales.setValue(scales)
            opFeatures.ComputeIn2d.setValue([False] * len(scales))
            opFeatures.SelectionMatrix.setValue(selections)

            gui.currentGui()._labelControlUi.suggestFeaturesButton.click()
            wait_until(lambda: isinstance(QApplication.instance().activeModalWidget(), SuggestFeaturesDialog))
            dlg = QApplication.instance().activeModalWidget()
            dlg.number_of_feat_box.setValue(2)

            with wait_signal(dlg._runComplete, timeout=10000):
                dlg.run_button.click()

            # select the filtered feature set in the dialog and accept
            idx = dlg.all_feature_sets_combo_box.findText("2 features, filter selection", Qt.MatchContains)
            dlg.all_feature_sets_combo_box.setCurrentIndex(idx)
            QApplication.processEvents()
            dlg.accept()
            QApplication.processEvents()

            features_dlg = dlg.selected_features_matrix
            features_after = opFeatures.SelectionMatrix.value

            numpy.testing.assert_array_equal(features_dlg, features_after)
            numpy.testing.assert_array_equal(opFeatures.ComputeIn2d.value, [False, False, True])

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
