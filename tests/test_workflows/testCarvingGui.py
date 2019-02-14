from tests.helpers import ShellGuiTestCaseBase
import logging
import os
import sys
import tempfile
import zipfile

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
from ilastik.workflows.carving import CarvingWorkflow
from lazyflow.utility.timer import Timer


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class TestObjectClassificationGui(ShellGuiTestCaseBase):
    """Run a set of GUI-based tests on the carving workflow.

    Note: These tests are named (prefixed with `test_%02d`) in order to impose
        an order. Tests simulate interaction with a ilastik and depend on
        the earlier ones.
    """

    @classmethod
    def workflowClass(cls):
        return CarvingWorkflow

    @classmethod
    def setup_class(cls):
        # Base class first
        super().setup_class()

        # input files:
        current_dir = os.path.split(__file__)[0]
        cls.sample_data_raw = os.path.abspath(os.path.join(current_dir, "../data/inputdata/3d.h5"))

        # output files:
        cls.temp_dir = tempfile.mkdtemp()
        # uncomment for debugging
        # cls.temp_dir = os.path.expanduser('~/tmp')
        # if os.path.exists(cls.temp_dir):
        #     shutil.rmtree(cls.temp_dir)
        # os.makedirs(cls.temp_dir)
        cls.project_file = os.path.join(cls.temp_dir, "test_project_carving.ilp")
        cls.output_file = os.path.join(cls.temp_dir, "out_carving_object_segmentation.h5")
        cls.output_obj_file = os.path.join(cls.temp_dir, "out_carving_object_1.obj")

        # reference files
        # unzip the zip-file ;)
        cls.reference_zip_file = os.path.join(current_dir, "../data/outputdata/testCarvingGuiReference.zip")
        cls.reference_path = os.path.join(cls.temp_dir, "reference")
        cls.reference_files = {
            "output_obj_file": os.path.join(cls.reference_path, "testCarvingGuiReference/3d_carving_object_1.obj"),
            "output_file": os.path.join(
                cls.reference_path, "testCarvingGuiReference/3d_carving_completed_segments_1_object.h5"
            ),
        }
        os.makedirs(cls.reference_path)
        with zipfile.ZipFile(cls.reference_zip_file, mode="r") as zip_file:
            zip_file.extractall(path=cls.reference_path)
        cls.unzipped_reference_files = [os.path.join(cls.reference_path, fp) for fp in zip_file.namelist()]

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
        needed_files = [self.sample_data_raw]
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

            # Save
            # TODO: enable this once issue https://github.com/ilastik/ilastik/issues/1952 is fixed
            # shell.projectManager.saveProject()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)


if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test

    run_shell_test(__file__)
