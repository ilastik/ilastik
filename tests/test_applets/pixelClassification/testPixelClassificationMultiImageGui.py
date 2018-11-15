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
from builtins import range
import os
import numpy
from PyQt5.QtWidgets import QApplication
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from tests.helpers import ShellGuiTestCaseBase
from lazyflow.operators import OpPixelFeaturesPresmoothed

from ilastik.applets.pixelClassification.pixelClassificationApplet import PixelClassificationApplet
PIXEL_CLASSIFICATION_INDEX = 2

class TestPixelClassificationGuiMultiImage(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the pixel classification workflow.
    
    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """
    
    @classmethod
    def workflowClass(cls):
        return PixelClassificationWorkflow

    PROJECT_FILE = os.path.split(__file__)[0] + '/test_project.ilp'
    #SAMPLE_DATA = []
    #SAMPLE_DATA.append( os.path.split(__file__)[0] + '/synapse_small.npy' )
    #SAMPLE_DATA.append( os.path.split(__file__)[0] + '/synapse_small.npy' )

    @classmethod
    def setup_class(cls):
        # Base class first
        super(TestPixelClassificationGuiMultiImage, cls).setup_class()
        
        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.SAMPLE_DATA = []
            cls.SAMPLE_DATA.append(os.path.split(__file__)[0] + '/random_data1.npy')
            cls.SAMPLE_DATA.append(os.path.split(__file__)[0] + '/random_data2.npy')
            data1 = numpy.random.random((1,200,200,50,1))
            data1 *= 256
            data2 = numpy.random.random((1,50,100,100,1))
            data2 *= 256
            numpy.save(cls.SAMPLE_DATA[0], data1.astype(numpy.uint8))
            numpy.save(cls.SAMPLE_DATA[1], data2.astype(numpy.uint8))

    @classmethod
    def teardown_class(cls):
        # Call our base class so the app quits!
        super(TestPixelClassificationGuiMultiImage, cls).teardown_class()

        # Clean up: Delete any test files we generated
        removeFiles = [ TestPixelClassificationGuiMultiImage.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += TestPixelClassificationGuiMultiImage.SAMPLE_DATA

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
            assert isinstance(self.shell.workflow.applets[PIXEL_CLASSIFICATION_INDEX], PixelClassificationApplet)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    
    # These points are relative to the CENTER of the view
    LABEL_START = (-20,-20)
    LABEL_STOP = (20,20)
    LABEL_SAMPLE = (0,0)
    LABEL_ERASE_START = (-5,-5)
    LABEL_ERASE_STOP = (5,5)

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
            #gui.currentGui().editor.navCtrl.indicateSliceIntersection = False

            # Do our tests at position 0,0,0
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)

            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2

            # Add label classes
            gui.currentGui()._labelControlUi.AddLabelButton.click()
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 3

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
                self.strokeMouseFromCenter( imgView, self.LABEL_START, self.LABEL_STOP )
                # Make sure the labels were added to the label array operator
                labelData = opPix.LabelImages[0][:].wait()
                assert labelData.max() == i+1, "Max label value was {}".format( labelData.max() )

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Verify the actual rendering of each view
            for i in range(3):
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = gui.currentGui()._colorTable16[i+1]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

            # Save the project
            self.shell.onSaveProjectActionTriggered()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_5_InteractiveMode(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opPix = pixClassApplet.topLevelOperator

            # Clear the additional labels
            while len(gui.currentGui()._labelControlUi.labelListModel) > 2:
                gui.currentGui()._labelControlUi.labelListModel.removeRow(2)

            # Erase the labels that where not deleted
            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(PIXEL_CLASSIFICATION_INDEX)

            for i in range(2):
                # Use the second view for this test (which has the max label value)
                imgView = gui.currentGui().editor.imageViews[i]

                # Sanity check: There should be labels in the view that we can erase
                self.waitForViews([imgView])
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                labelColor = gui.currentGui()._colorTable16[i+1]
                assert observedColor == labelColor, "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format(
                    hex(labelColor), hex(observedColor))

                # Hide labels and sample raw data
                labelLayer = gui.currentGui().layerstack[0]
                assert labelLayer.name == "Labels"
                labelLayer.visible = False
                self.waitForViews([imgView])
                rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                assert rawDataColor != labelColor, "Pixel color was not correct after label was hidden.  rawDataColor: {}, labelColor: {}".format(
                    hex(rawDataColor), hex(labelColor))

                # Show labels
                labelLayer.visible = True
                # Select the eraser and brush size
                gui.currentGui()._labelControlUi.eraserToolButton.click()
                gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
                self.waitForViews([imgView])

                # Erase and verify
                self.strokeMouseFromCenter(imgView, self.LABEL_START, self.LABEL_STOP)
                self.waitForViews([imgView])
                erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                assert erasedColor == rawDataColor, "Eraser did not remove labels! Expected {}, got {}".format(
                    hex(rawDataColor), hex(erasedColor))

            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            # Re-add all labels
            self.test_4_AddLabels()

            # Enable interactive mode            
            assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
            gui.currentGui()._labelControlUi.liveUpdateButton.click()

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Disable iteractive mode.            
            gui.currentGui()._labelControlUi.liveUpdateButton.click()

            self.waitForViews(gui.currentGui().editor.imageViews)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_6_SwitchImages(self):
        """
        Switch back and forth between a labeled image and an unlabeled one.  Labels should disappear and then reappear.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            # Get the colors of the labels
            originalLabelColors = gui.currentGui()._colorTable16[1:4]

            # Sanity check: Verify the actual rendering of each view WITH the labels
            # (we haven't switched images yet)
            for i in range(3):
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = gui.currentGui()._colorTable16[i+1]
                assert observedColor == expectedColor, "Label is missing (should have been drawn in a previous test).  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

            # Select the second image
            self.shell.imageSelectionCombo.setCurrentIndex(1)
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)

            # Verify the actual rendering of each view (labels should NOT be present on the second image)
            for i in range(3):
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                oldColor = originalLabelColors[i]
                assert observedColor != oldColor, "Label should not be presnt on the second image in this test."

            # Select the first image again
            self.shell.imageSelectionCombo.setCurrentIndex(0)
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)

            # Verify the actual rendering of each view.  Labels should re-appear.
            for i in range(3):
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = gui.currentGui()._colorTable16[i+1]
                assert observedColor == expectedColor, "Label is missing (should have been drawn in a previous test).  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test
    run_shell_test(__file__)








