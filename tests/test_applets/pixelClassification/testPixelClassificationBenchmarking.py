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
import sys
import numpy
import pytest

from PyQt5.QtWidgets import QApplication
from tests.helpers import ShellGuiTestCaseBase
from ilastik.workflows.pixelClassification import PixelClassificationWorkflow
from lazyflow.operators import OpPixelFeaturesPresmoothed

from lazyflow.utility.timer import Timer

from ilastik.applets.pixelClassification.pixelClassificationApplet import PixelClassificationApplet
PIXEL_CLASSIFICATION_INDEX = 2

import logging
logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler(sys.stdout) )
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)


class TestPixelClassificationGuiBenchmarking(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the pixel classification workflow.
    
    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """
    
    @classmethod
    def workflowClass(cls):
        return PixelClassificationWorkflow

    PROJECT_FILE = os.path.split(__file__)[0] + '/test_project.ilp'
    #SAMPLE_DATA = os.path.split(__file__)[0] + '/synapse_small.npy'

    @classmethod
    def setup_class(cls):
        # Base class first
        super(TestPixelClassificationGuiBenchmarking, cls).setup_class()

        # This test is useful for performance evaluation,
        # but it takes too long to be useful as part of the normal test suite.
        super().teardown_class()
        pytest.skip("For benchmark purposes only")

        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.SAMPLE_DATA = os.path.split(__file__)[0] + '/random_data.npy'
            data = numpy.random.random((1,512,512,128,1))
            data *= 256
            numpy.save(cls.SAMPLE_DATA, data.astype(numpy.uint8))
        
        # Start the timer
        cls.timer = Timer()
        cls.timer.unpause()

    @classmethod
    def teardown_class(cls):
        logger.debug( "Total Time: {} seconds".format( cls.timer.seconds() ) )
        
        # Call our base class so the app quits!
        super(TestPixelClassificationGuiBenchmarking, cls).teardown_class()

        # Clean up: Delete any test files we generated
        removeFiles = [ TestPixelClassificationGuiBenchmarking.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += [ TestPixelClassificationGuiBenchmarking.SAMPLE_DATA ]

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
        
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = self.SAMPLE_DATA
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.DatasetGroup.resize(1)
            opDataSelection.DatasetGroup[0][0].setValue(info)
            
            # Set some features
            opFeatures = workflow.featureSelectionApplet.topLevelOperator
            #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
            selections = numpy.array( [[True, True, True, True, True, True, False],
                                       [True, True, True, True, True, True, False],
                                       [True, True, True, True, True, True, False],
                                       [True, True, True, True, True, True, False],
                                       [True, True, True, True, True, True, False],
                                       [True, True, True, True, True, True, False]] )

            opFeatures.SelectionMatrix.setValue(selections)
        
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    # These points are relative to the CENTER of the view
    LABEL_START = (-20,-20)
    LABEL_STOP = (20,20)
    LABEL_SAMPLE = (0,0)
    LABEL_ERASE_START = (-10,-10)
    LABEL_ERASE_STOP = (10,10)

    def test_2_AddLabels(self):
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
            assert isinstance(self.shell.workflow.applets[PIXEL_CLASSIFICATION_INDEX], PixelClassificationApplet)
            
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
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2,\
                "Got {} rows".format(gui.currentGui()._labelControlUi.labelListModel.rowCount())
            
            # Add label classes
            for i in range(3):
                gui.currentGui()._labelControlUi.AddLabelButton.click()
                assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 3 + i,\
                    "Expected {}, but got {} rows".format(2 + i, gui.currentGui()._labelControlUi.labelListModel.rowCount())

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

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Verify the actual rendering of each view
            for i in range(3):
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = gui.currentGui()._colorTable16[i+1]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_3_InteractiveMode(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            # Make sure the entire slice is visible
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionFitToScreen.trigger()

            with Timer() as timer:
                # Enable interactive mode            
                assert gui.currentGui()._labelControlUi.liveUpdateButton.isChecked() == False
                gui.currentGui()._labelControlUi.liveUpdateButton.click()
    
                # Do to the way we wait for the views to finish rendering, the GUI hangs while we wait.
                self.waitForViews(gui.currentGui().editor.imageViews)

            logger.debug("Interactive Mode Rendering Time: {}".format( timer.seconds() ))

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    
    def test_4_SwitchSlice(self):
        """
        Move the z-window by 1 slice.  The data should already be cached, so this is really measuring the performance of cache access.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            with Timer() as timer:
                gui.currentGui().editor.posModel.slicingPos = (0,0,1)
    
                # Do to the way we wait for the views to finish rendering, the GUI hangs while we wait.
                self.waitForViews(gui.currentGui().editor.imageViews)

            logger.debug("New Slice Rendering Time: {}".format( timer.seconds() ))

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    



if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test
    run_shell_test(__file__)
