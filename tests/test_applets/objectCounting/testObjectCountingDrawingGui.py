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
#		   http://ilastik.org/license.html
###############################################################################
import numpy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import QEvent,Qt
from ilastik.workflows.counting import CountingWorkflow
from tests.helpers import ShellGuiTestCaseBase
from lazyflow.operators import OpPixelFeaturesPresmoothed
import os

from ilastik.applets.counting.countingApplet import CountingApplet
COUNTING_APPLET_INDEX = 2

class TestObjectCountingDrawing(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the pixel classification workflow.

    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """

    @classmethod
    def workflowClass(cls):
        return CountingWorkflow

    PROJECT_FILE = os.path.split(__file__)[0] + '/test_project.ilp'
    SAMPLE_DATA = []
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/1.npy')

    @classmethod
    def setup_class(cls):
        # Base class first
        super(TestObjectCountingDrawing, cls).setup_class()

        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.SAMPLE_DATA = []
            cls.SAMPLE_DATA.append(os.path.split(__file__)[0] + '/random_data1.npy')
            cls.SAMPLE_DATA.append(os.path.split(__file__)[0] + '/random_data2.npy')
            data1 = numpy.random.random((1,200,200,1,1))
            data1 *= 256
            data2 = numpy.random.random((1,50,100,1,1))
            data2 *= 256
            numpy.save(cls.SAMPLE_DATA[0], data1.astype(numpy.uint8))
            numpy.save(cls.SAMPLE_DATA[1], data2.astype(numpy.uint8))

    @classmethod
    def teardown_class(cls):
        # Call our base class so the app quits!
        super(TestObjectCountingDrawing, cls).teardown_class()

        # Clean up: Delete any test files we generated
        removeFiles = [ TestObjectCountingDrawing.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += TestObjectCountingDrawing.SAMPLE_DATA

        for f in removeFiles:
            try:
                os.remove(f)
            except:
                pass


    def test_1_NewProject(self):
        """
        Create a blank project, manipulate few couple settings, and save it.
        """
        def impl():
            projFilePath = self.PROJECT_FILE
            shell = self.shell

            # New project
            shell.createAndLoadNewProject(projFilePath, self.workflowClass())
            workflow = shell.projectManager.workflow

            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            for i, dataFile in enumerate(self.SAMPLE_DATA):
                # Add a file
                info = DatasetInfo()

                info.filePath = dataFile


                opDataSelection.DatasetGroup.resize(i+1)
                opDataSelection.DatasetGroup[i][0].setValue(info)

            # Set some features
            opFeatures = workflow.featureSelectionApplet.topLevelOperator
            #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
            selections = numpy.array( [[True, False, False, False, False, False, False],
                                       [True, False, False, False, False, False, False],
                                       [True, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False]] )
            opFeatures.SelectionMatrix.setValue(selections)

            # Save and close
            shell.projectManager.saveProject()
            shell.ensureNoCurrentProject(assertClean=True)

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
            assert isinstance(self.shell.workflow.applets[COUNTING_APPLET_INDEX], CountingApplet)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    # These points are relative to the CENTER of the view


    def test_4_AddDotsAndBackground(self):
        """
        Add labels and draw them in the volume editor.
        """
        def impl():

            imageId = 0

            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            self.shell.imageSelectionCombo.setCurrentIndex(imageId)

            gui = countingClassApplet.getMultiLaneGui()
            self.waitForViews(gui.currentGui().editor.imageViews)

            opPix = countingClassApplet.topLevelOperator
            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(COUNTING_APPLET_INDEX)

            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()

            ## Turn off the slicing position lines
            ## FIXME: This disables the lines without unchecking the position
            ##        box in the VolumeEditorWidget, making the checkbox out-of-sync
            #gui.currentGui().editor.navCtrl.indicateSliceIntersection = False

            # Do our tests at position 0,0,0
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Got {} rows".format(gui.currentGui()._labelControlUi.labelListModel.rowCount())


            # Select the brush
            gui.currentGui()._labelControlUi.paintToolButton.click()

            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            # Draw some arbitrary labels in the view using mouse events.

            # Set the brush size
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(1)
            gui.currentGui()._labelControlUi.labelListModel.select(0)

            imgView = gui.currentGui().editor.imageViews[2]


            QApplication.processEvents()
            LABEL_START = (-128,-128)
            LABEL_STOP = (0,0)
            LABEL_ERASE_START = (-128,-128)
            LABEL_ERASE_STOP = (128,128)

            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(0)


            self.strokeMouseFromCenter( imgView, LABEL_START,LABEL_STOP)
            self.waitForViews([imgView])
            labelData = opPix.LabelImages[imageId][:].wait()
#
#            assert numpy.sum(labelData[labelData==2]) > 22, "Number of background dots was {}".format(
#                numpy.sum(labelData[labelData==2]) )

            gui.currentGui()._labelControlUi.AddBoxButton.click()
            self.strokeMouseFromCenter(imgView, LABEL_START, LABEL_STOP)

            labelData = opPix.LabelImages[imageId][:].wait()
            self.waitForViews([imgView])

            rectangles = gui.currentGui().boxController._currentBoxesList
            rect = rectangles[0]._rectItem.rect()
#            go.db

            assert rect.bottomRight().x() == 128, "Rectangle is incorrect: {} is not 255".format(rect.bottomRight().x())
            assert rect.bottomRight().y() == 128, "Rectangle is incorrect: {} is not 255".format(rect.bottomRight().y())

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)




if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test
    run_shell_test(__file__)

