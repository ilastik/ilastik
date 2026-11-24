from contextlib import contextmanager

import numpy as np
import pytest
import vigra
from qtpy.QtWidgets import QCheckBox

from ilastik.applets.dataSelection.opDataSelection import PreloadedArrayDatasetInfo
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from tests.test_ilastik.helpers import ShellGuiTestCaseBase


class TestPixelClassificationChannelSelection(ShellGuiTestCaseBase):
    @classmethod
    def workflowClass(cls):
        return PixelClassificationWorkflow

    @pytest.fixture(autouse=True)
    def project_path(self, tmp_path):
        self.project_file = str(tmp_path / "channels.ilp")

    @contextmanager
    def _feature_selection(self):
        self.shell.createAndLoadNewProject(self.project_file, self.workflowClass())
        try:
            workflow = self.shell.workflow
            raw_data = np.random.default_rng(0).random((20, 21, 3), dtype=np.float32)
            op_data = workflow.dataSelectionApplet.topLevelOperator
            op_data.DatasetGroup.resize(1)
            op_data.DatasetGroup[0][workflow.Roles.RAW_DATA].setValue(
                PreloadedArrayDatasetInfo(preloaded_array=raw_data, axistags=vigra.AxisTags("yxc"))
            )

            feature_applet = workflow.featureSelectionApplet
            op_features = feature_applet.topLevelOperator
            op_features.FeatureIds.setValue(["GaussianSmoothing", "LaplacianOfGaussian"])
            op_features.Scales.setValue([0.7])
            op_features.SelectionMatrix.setValue(np.ones((2, 1), dtype=bool))

            self.shell.setSelectedAppletDrawer(workflow.applets.index(feature_applet))
            gui = feature_applet.getMultiLaneGui().currentGui()
            channel_checkboxes = gui.channelSelectionWidget.findChildren(QCheckBox)
            yield workflow.pcApplet.topLevelOperator.getLane(0), channel_checkboxes
        finally:
            self.shell.closeCurrentProject()

    def test_uses_all_channels_by_default(self):
        def impl():
            with self._feature_selection() as (op_classification, channel_checkboxes):
                assert [checkbox.isChecked() for checkbox in channel_checkboxes] == [True, True, True]
                for feature_image in (op_classification.FeatureImages, op_classification.CachedFeatureImages):
                    # Two scalar features for each of three channels.
                    assert feature_image[:].wait().shape[-1] == 6

        self.exec_in_shell(impl)

    def test_updates_features_when_a_channel_is_deselected(self):
        def impl():
            with self._feature_selection() as (op_classification, channel_checkboxes):
                all_features = op_classification.CachedFeatureImages[:].wait()

                channel_checkboxes[1].click()

                # Remove channels 1, 4 from filters (those were the ones corresponding to channel 1)
                expected_features = all_features[..., [0, 2, 3, 5]]
                for feature_image in (op_classification.FeatureImages, op_classification.CachedFeatureImages):
                    selected_features = feature_image[:].wait()
                    assert selected_features.shape[-1] == 4
                    np.testing.assert_allclose(selected_features, expected_features)

        self.exec_in_shell(impl)
