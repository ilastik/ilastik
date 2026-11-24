import numpy as np
import pytest
import vigra
from qtpy.QtWidgets import QCheckBox

from ilastik.applets.dataSelection.opDataSelection import PreloadedArrayDatasetInfo
from ilastik.workflows.objectClassification.objectClassificationWorkflow import ObjectClassificationWorkflowBinary
from tests.test_ilastik.helpers import ShellGuiTestCaseBase


class TestObjectFeatureChannelSelection(ShellGuiTestCaseBase):
    @classmethod
    def workflowClass(cls):
        return ObjectClassificationWorkflowBinary

    @pytest.fixture(autouse=True)
    def project_path(self, tmp_path):
        self.project_file = str(tmp_path / "channels.ilp")

    def test_object_features_follow_channel_selection(self):
        def impl():
            self.shell.createAndLoadNewProject(self.project_file, self.workflowClass())
            try:
                workflow = self.shell.workflow
                raw_data = np.zeros((20, 21, 3), dtype=np.float32)
                raw_data[2:4, 3:6] = [10, 20, 30]
                segmentation = np.zeros((20, 21, 1), dtype=np.uint8)
                segmentation[2:4, 3:6] = 1

                roles = workflow.InputImageRoles
                op_data = workflow.dataSelectionApplet.topLevelOperator
                op_data.DatasetGroup.resize(1)
                for role, data in ((roles.RAW_DATA, raw_data), (roles.SEGMENTATION_IMAGE, segmentation)):
                    op_data.DatasetGroup[0][role].setValue(
                        PreloadedArrayDatasetInfo(preloaded_array=data, axistags=vigra.AxisTags("yxc"))
                    )

                feature_applet = workflow.objectExtractionApplet
                plugin_name = "Standard Object Features"
                feature_applet.topLevelOperator.Features.setValue({plugin_name: {"Mean": {}, "Count": {}}})
                object_features_slot = workflow.objectClassificationApplet.topLevelOperator.getLane(0).ObjectFeatures

                self.shell.setSelectedAppletDrawer(1)
                gui = feature_applet.getMultiLaneGui().currentGui()
                drawer = gui.appletDrawer()
                channel_checkboxes = gui.channelSelectionWidget.findChildren(QCheckBox)

                assert [checkbox.isChecked() for checkbox in channel_checkboxes] == [True, True, True]
                assert drawer.featuresSelected.text().splitlines()[0] == "2 feature(s) on 3 channel(s)"
                all_features = object_features_slot([0]).wait()[0][plugin_name]
                # The feature arrays include a zero row for the background.
                np.testing.assert_array_equal(all_features["Mean"], [[0, 0, 0], [10, 20, 30]])
                np.testing.assert_array_equal(all_features["Count"], [[0], [6]])

                channel_checkboxes[1].click()

                assert drawer.featuresSelected.text().splitlines()[0] == "2 feature(s) on 2 channel(s)"
                selected_features = object_features_slot([0]).wait()[0][plugin_name]
                np.testing.assert_array_equal(selected_features["Mean"], [[0, 0], [10, 30]])
                np.testing.assert_array_equal(selected_features["Count"], all_features["Count"])
            finally:
                self.shell.closeCurrentProject()

        self.exec_in_shell(impl)
