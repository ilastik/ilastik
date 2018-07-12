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
import logging
import os
import shutil
import sys
import tempfile

from PyQt5.QtWidgets import QApplication

import numpy

from ilastik.workflows import ObjectClassificationWorkflowPrediction
from ilastik.applets.dataSelection.opDataSelection import DatasetInfo

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
    def setupClass(cls):
        # Base class first
        super().setupClass()

        # input files:
        current_dir = os.path.split(__file__)[0]
        cls.sample_data_raw = os.path.abspath(os.path.join(current_dir, '../data/inputdata/3d.h5'))
        cls.sample_data_prob = os.path.abspath(
            os.path.join(current_dir, '../data/inputdata/3d_Probabilities.h5'))

        # output files:
        # cls.temp_dir = tempfile.mkdtemp()
        cls.temp_dir = os.path.expanduser('~/tmp')
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)  # TODO: cleanup when dev is done
        os.makedirs(cls.temp_dir)  # TODO: cleanup when dev is done
        cls.project_file = os.path.join(cls.temp_dir, 'test_project_oc.ilp')
        cls.output_file = os.path.join(cls.temp_dir, '3d_Object_Probabilities_out.h5')

        # Start the timer
        cls.timer = Timer()
        cls.timer.unpause()

    @classmethod
    def teardownClass(cls):
        cls.timer.pause()
        logger.debug(f"Total Time: {cls.timer.seconds()} seconds.")

        # Call our base class so the app quits!
        super().teardownClass()

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

            # make sure some preconditions are met:
            assert op_object_features.RawImage.ready()
            assert op_object_features.BinaryImage.ready()

            # we cannot test the feature-selection dialog here, as it's modal.
            # we therefore select a set of object features (all of them) and
            # supply them to the operator directly
            features, _ = gui.currentGui()._populate_feature_dict(op_object_features)
            features = {
                plugin: features[plugin] for plugin in features if 'test' not in plugin.lower()}
            op_object_features.Features.setValue(features)
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

            # Do our tests at position 0, 0, 0
            gui.currentGui().editor.posModel.slicingPos = (0, 0, 0)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 0, (
                "Got {} rows".format(gui.currentGui()._labelControlUi.labelListModel.rowCount()))

            # Add label classes
            for i in range(2):
                gui.currentGui()._labelControlUi.AddLabelButton.click()
                assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == i + 1, (
                    f"Got {gui.currentGui()._labelControlUi.labelListModel.rowCount()} rows")

            assert op_object_classification.NumLabels.value == 2
            # Add some labels, we use onClick directly in order to bypass problems with painting
            # on different screen resolutions
            # position: t, x, y, z, c
            label_position = namedtuple('label_position', ['label', 'position'])
            label_positions = [
                label_position(0, (0, 10, 10, 10, 0)),  # obj 1
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
            op_object_classification = object_classification_applet.topLevelOperator.getLane(0)

            # activate the object classification applet
            shell.setSelectedAppletDrawer(3)

            with Timer() as timer:
                # Enable interactive mode
                assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() is False
                gui.currentGui()._labelControlUi.liveUpdateButton.click()
                # Do to the way we wait for the views to finish rendering, the GUI hangs while we wait.
                self.waitForViews(gui.currentGui().editor.imageViews)
            logger.debug(f"Interactive Mode Rendering Time: {timer.seconds()}")

            # Disable iteractive mode.
            gui.currentGui()._labelControlUi.liveUpdateButton.click()

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

            self.waitForViews(gui.currentGui().editor.imageViews)

        self.exec_in_shell(impl)

# Export image settings: File: tmp_folder/{nickname}_{result_type}.h5

# Export table settings: tmp_folder/exported_data.csv; features: all

# Export all

# Export table settings: tmp_folder/exported_data.h5; features: all


# Done
if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_nosetest
    run_shell_nosetest(__file__)
