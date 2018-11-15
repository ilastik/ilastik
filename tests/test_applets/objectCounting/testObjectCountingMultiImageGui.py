from __future__ import division
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
#Fixme: this test currently fails due to an issue to be fixed
# Checks that the boxes remains in the image when switching image
# Other things to be tested:
# - interaction with boxes : move them around etc...


from builtins import range
from past.utils import old_div
import os
import numpy
import vigra

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import QEvent,Qt
from ilastik.workflows.counting import CountingWorkflow
from tests.helpers import ShellGuiTestCaseBase
from lazyflow.operators import OpPixelFeaturesPresmoothed

from ilastik.applets.counting.countingApplet import CountingApplet
COUNTING_APPLET_INDEX = 2

class TestObjectCountingGuiMultiImage(ShellGuiTestCaseBase):
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
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/0.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/2.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/3.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/4.npy')


    @classmethod
    def setup_class(cls):
        # Base class first
        super(TestObjectCountingGuiMultiImage, cls).setup_class()

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
        super(TestObjectCountingGuiMultiImage, cls).teardown_class()

        # Clean up: Delete any test files we generated
        removeFiles = [ TestObjectCountingGuiMultiImage.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += TestObjectCountingGuiMultiImage.SAMPLE_DATA

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
                info.axistags = vigra.defaultAxistags('xyc')

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


            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(COUNTING_APPLET_INDEX)

            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()
            viewMenu.parent().selectedZoomToOriginal.trigger()

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


            dot_start_list = [(-14,-20),(6,-8),(10,4), (20,21)]
            dot_stop_list = [(-20,-11),(9,-12),(15,-3), (20,21)]

            LABEL_START = (-14,-20)
            LABEL_STOP = (-14,-21)
            LABEL_ERASE_START = (6,-8)
            LABEL_ERASE_STOP = (9,-8)


           #draw foreground dots
            for start,stop in zip(dot_start_list,dot_stop_list):
                self.strokeMouseFromCenter( imgView, start,stop )

            labelData = opPix.LabelImages[imageId][:].wait()

            assert numpy.sum(labelData[labelData==1]) == 4, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )

            center = old_div((numpy.array(labelData.shape[:-1])),2) + 1

            true_idx = numpy.array([center + dot for dot in dot_start_list])
            idx = numpy.where(labelData)
            test_idx = numpy.array((idx[0],idx[1])).transpose()
            
            # This test doesn't require *exact* pixel locations to match due to rounding differences in mouse strokes.
            # Instead, we just require them to be close.
            # FIXME: This should be fixable by ensuring that the image is properly zoomed to 1-1 scale before the test.
            assert numpy.abs(test_idx - true_idx).max() <= 1


            # Set the brush size
            # Draw background
            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)

            self.strokeMouseFromCenter( imgView, LABEL_START,LABEL_STOP)

            #The background in this configuration should override the dots
            labelData = opPix.LabelImages[imageId][:].wait()
            assert labelData.max() == 2, "Max label value was {}".format( labelData.max() )

            assert numpy.sum(labelData[labelData==1]) == 3, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )


            #Now select eraser
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.strokeMouseFromCenter( imgView, LABEL_ERASE_START,LABEL_ERASE_STOP)

            labelData = opPix.LabelImages[imageId][:].wait()
            assert numpy.sum(labelData[labelData==1]) == 2, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )

            true_idx = numpy.array([center + dot for dot in dot_start_list[2:]])
            idx = numpy.where(labelData == 1)
            test_idx = numpy.array((idx[0],idx[1])).transpose()
            # This test doesn't require *exact* pixel locations to match due to rounding differences in mouse strokes.
            # Instead, we just require them to be close.
            # FIXME: This should be fixable by ensuring that the image is properly zoomed to 1-1 scale before the test.
            assert numpy.abs(test_idx - true_idx).max() <= 1
            self.waitForViews([imgView])


            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)



    def test_5_AddBox(self):

        """
        Add boxes and draw them in the volume editor.
        """
        def impl():


            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()

            opPix = countingClassApplet.topLevelOperator
            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(COUNTING_APPLET_INDEX)

            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()



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
            gui.currentGui()._labelControlUi.AddBoxButton.click()

            imgView = gui.currentGui().editor.imageViews[2]

            start_box_list=[(-22,-1),(0,1)]
            stop_box_list=[(0,10),(50,20)]

            for start,stop in zip(start_box_list,stop_box_list):
                self.strokeMouseFromCenter( imgView, start,stop)

            added_boxes=len(gui.currentGui()._labelControlUi.boxListModel._elements)
            assert added_boxes==2," Not all boxes added to the model curr = %d"%added_boxes
            start_box_list= [(-128,-128), (128,128)]
            stop_box_list = [(128,128), (-128,-128)]
            for start,stop in zip(start_box_list,stop_box_list):
                self.strokeMouseFromCenter( imgView, start,stop)

            added_boxes=len(gui.currentGui()._labelControlUi.boxListModel._elements)
            assert added_boxes==4," Not all boxes added to the model curr = %d"%added_boxes


            self.waitForViews([imgView])

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)


    def test_6_SwitchImages(self):
        """
        Switch back and forth between a labeled image and an unlabeled one.  boxes should disappear and then reappear.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()


            # Select the second image
            self.shell.imageSelectionCombo.setCurrentIndex(2)
            gui = countingClassApplet.getMultiLaneGui()
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)


            #check that there is no box then add one

            added_boxes=gui.currentGui()._labelControlUi.boxListModel._elements
            assert len(added_boxes) == 0, " %s no boxes added yet for the new image"%len(added_boxes)

            # Select the first image
            self.shell.imageSelectionCombo.setCurrentIndex(0)
            gui = countingClassApplet.getMultiLaneGui()
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)

            #Check that old boxes are still there
            added_boxes=len(gui.currentGui()._labelControlUi.boxListModel._elements)
            assert added_boxes==4," Not all boxes added to the model curr = %d"%added_boxes


            # Select the second image
            self.shell.imageSelectionCombo.setCurrentIndex(1)
            gui = countingClassApplet.getMultiLaneGui()
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)


        # Run this test from within the shell event loop
        self.exec_in_shell(impl)




    def test_7_AddDotsAndBackground(self):
        """
        Add labels and draw them in the volume editor.
        """
        def impl():

            imageId = 1

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


            dot_start_list = [(-25,-20),(9,-15),(15,-3)]
            dot_stop_list = [(-25,-11),(9,-12),(15,-3)]

            LABEL_START = (-25,-30)
            LABEL_STOP = (-25,-20)
            LABEL_ERASE_START = (9,-15)
            LABEL_ERASE_STOP = (15,-3)


           #draw foreground dots
            for start,stop in zip(dot_start_list,dot_stop_list):
                self.strokeMouseFromCenter( imgView, start,stop )

            labelData = opPix.LabelImages[imageId][:].wait()

            assert numpy.sum(labelData[labelData==1]) == 3, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )

            center = old_div((numpy.array(labelData.shape[:-1])),2) + 1

            true_idx = numpy.array([center + dot for dot in dot_start_list])
            idx = numpy.where(labelData)
            test_idx = numpy.array((idx[0],idx[1])).transpose()
            # This test doesn't require *exact* pixel locations to match due to rounding differences in mouse strokes.
            # Instead, we just require them to be close.
            # FIXME: This should be fixable by ensuring that the image is properly zoomed to 1-1 scale before the test.
            assert numpy.abs(test_idx - true_idx).max() <= 1


            # Set the brush size
            # Draw background
            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)

            self.strokeMouseFromCenter( imgView, LABEL_START,LABEL_STOP)

            #The background in this configuration should override the dots
            labelData = opPix.LabelImages[imageId][:].wait()
            assert labelData.max() == 2, "Max label value was {}".format( labelData.max() )

            assert numpy.sum(labelData[labelData==1]) == 2, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )
            assert numpy.sum(labelData[labelData==2]) > 50, "Number of background dots was {}".format(
                numpy.sum(labelData[labelData==2]) )


            #Now select eraser
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.strokeMouseFromCenter( imgView, LABEL_ERASE_START,LABEL_ERASE_STOP)

            labelData = opPix.LabelImages[imageId][:].wait()
            assert numpy.sum(labelData[labelData==1]) == 0, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )

            self.waitForViews([imgView])

            QApplication.processEvents()
            LABEL_START = (-128,-128)
            LABEL_STOP = (128,128)
            LABEL_ERASE_START = (-128,-128)
            LABEL_ERASE_STOP = (128,128)

            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(0)


            self.strokeMouseFromCenter( imgView, LABEL_START,LABEL_STOP)
            self.waitForViews([imgView])
            labelData = opPix.LabelImages[imageId][:].wait()

#            assert numpy.sum(labelData[labelData==2]) > 22, "Number of background dots was {}".format(
#                numpy.sum(labelData[labelData==2]) )

            gui.currentGui()._labelControlUi.AddBoxButton.click()
            self.strokeMouseFromCenter(imgView, LABEL_START, LABEL_STOP)

            labelData = opPix.LabelImages[imageId][:].wait()
            self.waitForViews([imgView])

            gui.currentGui()._labelControlUi.eraserToolButton.click()
            self.strokeMouseFromCenter( imgView, LABEL_ERASE_START,LABEL_ERASE_STOP)
            labelData = opPix.LabelImages[imageId][:].wait()
 #           assert numpy.sum(labelData[labelData==2]) == 20, "Number of background dots was {}".format(
 #               numpy.sum(labelData[labelData==2]) )

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)



    def test_8_UpdateSum(self):
        """
        Click on the interactive mode to see if training has been
        suceesfull in the secod images even if the labels are given
        in the first one

        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()

            clicked=False
            def toggle(clicked):
                clicked= not clicked
                gui.currentGui()._labelControlUi.liveUpdateButton.click()
                return clicked

            SVROptions=gui.currentGui()._labelControlUi.SVROptions

            #Test each one of the counting modality which is registered
            for el in range(SVROptions.count()):
                #if clicked:
                #    clicked=toggle(clicked)

                SVROptions.setCurrentIndex(el)
                #clicked=toggle(clicked)
                imgView = gui.currentGui().editor.imageViews[2]


               # FIXME: somehow this triggers computation of the density but
               # this value is not updated
                gui.currentGui().labelingDrawerUi.DensityButton.click()
                self.waitForViews([imgView])
                density = gui.currentGui().op.OutputSum[...].wait()
                # Check that the predicted count is in a fine range
                assert density[0]>70,"Density value is too low: {0:.2f}".format(density[0])
                assert density[0]<150,"Density value is too high: {0:.2f}".format(density[0])

            #if clicked:
                #clicked=toggle(clicked)
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_9_CheckDensity(self):

        """
        Test if the different operators produce the same density
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()

            self.shell.imageSelectionCombo.setCurrentIndex(0)
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)

            operatorDensity = numpy.sum(gui.currentGui().op.Density[...].wait())
            sumDensity = gui.currentGui().op.OutputSum[...].wait()
            gui.currentGui().labelingDrawerUi.liveUpdateButton.setChecked(False)
            displayedDensity = gui.currentGui()._labelControlUi.CountText.text()
            while str(displayedDensity) == ' -- --':
                gui.currentGui().labelingDrawerUi.DensityButton.click()
                displayedDensity = gui.currentGui()._labelControlUi.CountText.text()
                self.waitForViews(gui.currentGui().editor.imageViews)
            displayedDensity = float(str(displayedDensity))

            assert abs(displayedDensity - operatorDensity) < 1E-1, "Density mismatch:, the displayed Density {} is not\
            equal to the internal density from the Operator {}".format(displayedDensity, operatorDensity)
            
            assert abs(operatorDensity - sumDensity) < 1E-1, "Density mismatch: the Sum operator {} does not return the same\
            result as using numpy.sum {}".format(operatorDensity, sumDensity)
            

        self.exec_in_shell(impl)


    def test_6_CheckBox(self):

        """
        Click on the interactive mode to see if training has been
        sucessful in the second image even if the labels are given
        in the first one

        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()

            self.shell.imageSelectionCombo.setCurrentIndex(0)
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)

            boxes = gui.currentGui()._labelControlUi.boxListModel._elements
            boxList = gui.currentGui().boxController._currentBoxesList
            for box, boxHandle in zip(boxes, boxList):
                start = boxHandle.getStart()
                stop = boxHandle.getStop()
                slicing = [slice(s1, s2) for s1, s2 in zip(start, stop)]
                # rounding here is necessary, because box label is rounded too
                val = numpy.round(numpy.sum(gui.currentGui().op.Density[slicing[1:3]].wait()), 1)
                val2 = float(box.density)
                assert abs(val - val2) < 1E-3,\
                    f"The value written to the box {val} differs from the one gotten via the operator {val2}"

        # FIXME same as test below?
        # self.exec_in_shell(impl)


    def test_11_CheckBoxes(self):
        """
        Click on the interactive mode to see if training has been
        suceesfull in the secod images even if the labels are given
        in the first one

        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()

            self.shell.imageSelectionCombo.setCurrentIndex(0)
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)

            boxes = gui.currentGui()._labelControlUi.boxListModel._elements
            fullBoxVal = float(boxes[2]._density)
            fullBoxVal2 = float(boxes[3]._density)

            assert abs(fullBoxVal - fullBoxVal2) < 1E-5, "Box mismatch: {.2f} is not close to\
            {.2f}".format(fullBoxVal, fullBoxVal2)

            self.shell.imageSelectionCombo.setCurrentIndex(1)
            gui.currentGui().labelingDrawerUi.DensityButton.click()
            boxes = gui.currentGui()._labelControlUi.boxListModel._elements
            fullBoxVal = float(boxes[0]._density)

            density = gui.currentGui().op.OutputSum[...].wait()
            assert density[0] == fullBoxVal, "Box mismatch: {} != {}".format(density[0], fullBoxVal)


        #FIXME: this test is disabled. for inconpatibility
        # betwenn the coordinates which are passed when drowing the box with
        # strokeMouseFromCenter and the coordinates of the boxes.
        # It should check that the density of the entire image is = to the density of a box which covers the whole image
        # Run this test from within the shell event loop
        #self.exec_in_shell(impl)




    def _switchToImg(self,img_number):
        # Select the second image
        self.shell.imageSelectionCombo.setCurrentIndex(img_number)
        workflow = self.shell.projectManager.workflow
        countingClassApplet = workflow.countingApplet
        gui = countingClassApplet.getMultiLaneGui()
        gui.currentGui().editor.posModel.slicingPos = (0,0,0)
        self.waitForViews(gui.currentGui().editor.imageViews)
        return gui,gui.currentGui(),gui.currentGui().editor.imageViews[2]



        #FIXME Currently not working, for some reason the ctrl modifier has no effect here
    # def test_8_MoveBoxAroundAndDelete(self):
    #     """
    #     Try to move around a box and delete mode to see if training has been
    #     suceesfull in the secod images even if the labels are given
    #     in the first one

    #     """
    #     def impl():
    #         gui,currentGui,imgView = self._switchToImg(0)


    #         gui.currentGui()._labelControlUi.AddBoxButton.click()
    #         start_box_list=[(-50,-50)]
    #         stop_box_list=[(150,150)]


    #         for start,stop in zip(start_box_list,stop_box_list):
    #             QApplication.processEvents()
    #             self.strokeMouseFromCenter( imgView, start,stop,Qt.NoModifier,1)
    #         QApplication.processEvents()
    #         import time
    #         time.sleep(3)


    #         #if clicked:
    #             #clicked=toggle(clicked)
    #     # Run this test from within the shell event loop
    #     self.exec_in_shell(impl)




if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test
    run_shell_test(__file__)








