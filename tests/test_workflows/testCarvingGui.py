from tests.helpers import ShellGuiTestCaseBase
import h5py
import filecmp
import logging
import numpy
import os
import sys
import shutil
import tempfile
import threading
import time
import zipfile

from PyQt5.QtWidgets import QApplication

from ilastik.applets.dataSelection.opDataSelection import DatasetInfo, FilesystemDatasetInfo
from ilastik.workflows.carving import CarvingWorkflow
from lazyflow.utility.timer import Timer

from lazyflow.operators.opReorderAxes import OpReorderAxes
from lazyflow.operators.ioOperators import OpInputDataReader
from lazyflow import roi

from volumina.widgets.exportHelper import get_export_operator

from ilastik.utility import bind

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.DEBUG)


class TestCarvingnGui(ShellGuiTestCaseBase):
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
            "carving_label_file": os.path.join(cls.reference_path, "testCarvingGuiReference/3d_carving_labels.h5"),
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
        shutil.rmtree(cls.temp_dir, onerror=lambda *x: logger.error(f"Could not delete file {x}"))

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
            info_raw = FilesystemDatasetInfo(
                filePath=self.sample_data_raw, project_file=self.shell.projectManager.currentProjectFile
            )
            opDataSelection.DatasetGroup[0][0].setValue(info_raw)

            # Save
            shell.projectManager.saveProject()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_02_do_preprocessing(self):
        """
        Go to the second applet and adjust some preprocessing settings.
        Apply and check the outcome.
        """

        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            preprocessingApplet = workflow.preprocessingApplet
            gui = preprocessingApplet.getMultiLaneGui()
            op_preprocessing = preprocessingApplet.topLevelOperator.getLane(0)

            # activate the preprocessing applet
            shell.setSelectedAppletDrawer(1)
            # let the gui catch up
            QApplication.processEvents()

            # set the required values
            sigma = 2.0
            gui.currentGui().setSigma(sigma)

            assert gui.currentGui().drawer.sigmaSpin.value() == sigma
            gui.currentGui().drawer.filter2.click()

            # get the final layer and check that it is not visible yet
            layermatch = [x.name.startswith("Watershed") for x in gui.currentGui().centralGui.editor.layerStack]
            assert sum(layermatch) == 1, "Watershed Layer expected."
            final_layer = gui.currentGui().centralGui.editor.layerStack[layermatch.index(True)]
            assert not final_layer.visible, "Expected the final layer not to be visible before apply is triggered."
            # in order to wait until the preprocessing is finished
            finished = threading.Event()

            def processing_finished():
                nonlocal finished
                finished.set()

            preprocessingApplet.appletStateUpdateRequested.subscribe(processing_finished)

            # trigger the preprocessing and wait
            gui.currentGui().drawer.runButton.click()
            finished.wait(timeout=10)
            assert finished.is_set()

            assert op_preprocessing.Sigma.value == sigma

            assert final_layer.visible

            watershed_output = op_preprocessing.WatershedImage[:].wait()

            # Hard-coded for this data and settings
            assert watershed_output.max() == 245

            # check that the write-protection did it's job:
            assert not gui.currentGui().drawer.sigmaSpin.isEnabled()
            assert not gui.currentGui().drawer.runButton.isEnabled()
            assert not gui.currentGui().drawer.sizeRegularizerSpin.isEnabled()
            assert not gui.currentGui().drawer.reduceToSpin.isEnabled()
            assert not gui.currentGui().drawer.doAggloCheckBox.isEnabled()

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_03_do_carving(self):
        """
        go to the "carving" applet and load some annotations via import.
        do the segmentation and compare to saved reference.

        this, of course, is not testing the real gui functionality of painting,
        but for now this is close enough.
        """

        def impl():
            shell = self.shell
            workflow = shell.projectManager.workflow
            carvingApplet = workflow.carvingApplet
            gui = carvingApplet.getMultiLaneGui()
            op_carving = carvingApplet.topLevelOperator.getLane(0)

            # activate the carving applet
            shell.setSelectedAppletDrawer(2)
            # let the gui catch up
            QApplication.processEvents()
            self.waitForViews(gui.currentGui().editor.imageViews)
            # inject the labels
            op5 = OpReorderAxes(parent=op_carving.parent)
            opReader = OpInputDataReader(parent=op_carving.parent)
            try:
                opReader.FilePath.setValue(f"{self.reference_files['carving_label_file']}/exported_data")
                op5.AxisOrder.setValue(op_carving.WriteSeeds.meta.getAxisKeys())
                op5.Input.connect(opReader.Output)
                label_data = op5.Output[:].wait()
            finally:
                op5.cleanUp()
                opReader.cleanUp()
            slicing = roi.fullSlicing(label_data.shape)
            op_carving.WriteSeeds[slicing] = label_data

            gui.currentGui().labelingDrawerUi.segment.click()
            QApplication.processEvents()

            op_carving.saveObjectAs("Object 1")
            op_carving.deleteObject("<not saved yet>")

            # export the mesh:
            req = gui.currentGui()._exportMeshes(["Object 1"], [self.output_obj_file])
            req.wait()

            # compare meshes
            with open(self.output_obj_file, "r") as f:
                left = f.read()

            with open(self.reference_files["output_obj_file"], "r") as f:
                right = f.read()

            # TODO: might result in errors due to rounding on different systems
            assert left == right

            # export the completed segments layer
            layermatch = [
                x.name.startswith("Completed segments (unicolor)") for x in gui.currentGui().editor.layerStack
            ]
            assert sum(layermatch) == 1, "Completed segments (unicolor) Layer expected."
            completed_segments_layer = gui.currentGui().editor.layerStack[layermatch.index(True)]
            opExport = get_export_operator(completed_segments_layer)
            try:
                opExport.OutputFilenameFormat.setValue(self.output_file)
                opExport.run_export()
            finally:
                opExport.cleanUp()

            assert os.path.exists(self.output_file)

            # compare completed segments
            with h5py.File(self.reference_files["output_file"], "r") as f_left:
                data_left = f_left["exported_data"][:]

            with h5py.File(self.output_file, "r") as f_right:
                data_right = f_right["exported_data"][:]

            numpy.testing.assert_array_almost_equal(data_left, data_right)

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)


if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test

    run_shell_test(__file__)
