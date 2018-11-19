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
#TODO: refactor
#TODO: test erase dots and brush strokes
#TODO: test remove the box
#TODO: test switch to a new image
#TODO: test load a referecence project


import os
import sys
import numpy
import vigra
from PyQt5.QtWidgets import QApplication
from lazyflow.operators import OpPixelFeaturesPresmoothed


from lazyflow.utility.timer import Timer, timeLogged

from ilastik.applets.counting.countingApplet import CountingApplet
COUNTING_APPLET_INDEX = 2

from tests.helpers import ShellGuiTestCaseBase

import logging
logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler(sys.stdout) )
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)


class TestObjectCountingGui(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the object counting workflow.
    
    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """
    
    @classmethod
    def workflowClass(cls):
        from ilastik.workflows.counting import CountingWorkflow
        return CountingWorkflow

    PROJECT_FILE = os.path.join(os.path.split(__file__)[0], 'test_project-counting.ilp')
    #SAMPLE_DATA = os.path.join(os.path.split(__file__)[0], 'synapse_small.npy')

    @classmethod
    def setup_class(cls):
        # Base class first
        super(TestObjectCountingGui, cls).setup_class()
        
        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.SAMPLE_DATA = os.path.join(os.path.split(__file__)[0], 'random_data.npy')
            data = numpy.random.random((200,200,3))
            data *= 256
            numpy.save(cls.SAMPLE_DATA, data.astype(numpy.uint8))

        # Sample Sigma value for OpCounting.opTrain (OpTrainCounter).
        cls.COUNTING_SIGMA = 4.2
        
        # Start the timer
        cls.timer = Timer()
        cls.timer.unpause()

    @classmethod
    def teardown_class(cls):
        cls.timer.pause()
        logger.debug( "Total Time: {} seconds".format( cls.timer.seconds() ) )
        
        # Call our base class so the app quits!
        super(TestObjectCountingGui, cls).teardown_class()

        # Clean up: Delete any test files we generated
        removeFiles = [ TestObjectCountingGui.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += [ TestObjectCountingGui.SAMPLE_DATA ]

        for f in removeFiles:        
            try:
                os.remove(f)
            except:
                pass

    def test_1_loadSerializedProject(self):
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
            selections = numpy.array( [[True, False, False, False, False, False, False],
                                       [True, False, False, False, False, False, False],
                                       [True, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False]] )
 
            opFeatures.SelectionMatrix.setValue(selections)
            
            
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()
            opCount = countingClassApplet.topLevelOperator

            opCount.opTrain.Sigma.setValue(self.COUNTING_SIGMA)
 
            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(COUNTING_APPLET_INDEX)
             
            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()
        

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
            opCount = self.shell.projectManager.workflow.countingApplet.topLevelOperator
            assert opCount.opTrain.Sigma.value == self.COUNTING_SIGMA
  
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    

    @timeLogged(logger, logging.INFO)
    def test_4_AddDots(self):
        """
        Add labels and draw them in the volume editor.
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
            
            dot_start_list = [(-20,-20),(9,-15),(15,-3)]
            dot_stop_list = [(-20,-11),(9,-12),(15,-3)]
            #dot_start_list = [(5,5)]
            #dot_stop_list = [(5,5)]
            
            for start,stop in zip(dot_start_list,dot_stop_list):
                self.strokeMouseFromCenter( imgView, start,stop )
  
  
  
            # Make sure the labels were added to the label array operator
            labelData = opPix.LabelImages[0][:].wait()
            labelData = vigra.taggedView( labelData, opPix.LabelImages[0].meta.axistags )
            labelData = labelData.withAxes('xy')
            center = (numpy.array(labelData.shape[:-1]) // 2) + 1
            
            true_idx = numpy.array([center + dot for dot in dot_start_list])
            idx = numpy.where(labelData)
            test_idx = numpy.array((idx[0],idx[1])).transpose()
            # This test doesn't require *exact* pixel locations to match due to rounding differences in mouse strokes.
            # Instead, we just require them to be close.
            # FIXME: This should be fixable by ensuring that the image is properly zoomed to 1-1 scale before the test.
            assert numpy.abs(test_idx - true_idx).max() <= 1

            assert numpy.sum(labelData)==len(dot_start_list)
            #assert labelData.max() == i+1, "Max label value was {}".format( labelData.max() )
  
            self.waitForViews([imgView])
  
            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()
  
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
        
        
    # These points are relative to the CENTER of the view
    LABEL_START = (-20,-30)
    LABEL_STOP = (-20,-20)
    LABEL_ERASE_START = (9,-15)
    LABEL_ERASE_STOP = (5,-15)
 
    @timeLogged(logger, logging.INFO)
    def test_5_AddDotsAndBackground(self):
        """
        Add labels and draw them in the volume editor.
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
             
            # Set the brush size
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(1)
            gui.currentGui()._labelControlUi.labelListModel.select(0)
                  
            imgView = gui.currentGui().editor.imageViews[2]
            
            dot_start_list = [(-20,-20),(9,-15),(15,-3)]
            dot_stop_list = [(-20,-11),(9,-12),(15,-3)]
           
           #draw foreground dots
            for start,stop in zip(dot_start_list,dot_stop_list):
                self.strokeMouseFromCenter( imgView, start,stop )
  
            
            # Set the brush size
            # Draw background
            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            
            self.strokeMouseFromCenter( imgView, self.LABEL_START,self.LABEL_STOP)
            
            #The background in this configuration should override the dots
            labelData = opPix.LabelImages[0][:].wait()
            labelData = vigra.taggedView( labelData, opPix.LabelImages[0].meta.axistags )
            labelData = labelData.withAxes('xy')
            assert labelData.max() == 2, "Max label value was {}".format( labelData.max() )
            
            assert numpy.sum(labelData[labelData==1]) == 2, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )


            #Now select eraser            
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.strokeMouseFromCenter( imgView, self.LABEL_ERASE_START,self.LABEL_ERASE_STOP)
            
            labelData = opPix.LabelImages[0][:].wait()
            labelData = vigra.taggedView( labelData, opPix.LabelImages[0].meta.axistags )
            labelData = labelData.withAxes('xy')
            assert numpy.sum(labelData[labelData==1]) == 1, "Number of foreground dots was {}".format(
                numpy.sum(labelData[labelData==1]) )
            
            
  
            self.waitForViews([imgView])
  
            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()
  
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
        
        
    @timeLogged(logger, logging.INFO)
    def test_6_AddBox(self):
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
            
            start_box_list=[(-100,-100),(-22,-1),(0,1)]
            stop_box_list=[(100,100),(0,10),(50,20)]
            
            for start,stop in zip(start_box_list,stop_box_list):
                self.strokeMouseFromCenter( imgView, start,stop)
            
            added_boxes=len(gui.currentGui()._labelControlUi.boxListModel._elements)
            assert added_boxes==3," Not all boxes added to the model curr = %d"%added_boxes
            self.waitForViews([imgView])
            
            # Save the project
            saveThread = self.shell.onSaveProjectActionTriggered()
            saveThread.join()
            
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)


        

    def test_7_InteractiveMode(self):
        """
        Click the "interactive mode" to see if anything crashes for each of the available counting modalities.
        
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
                if clicked: 
                    clicked=toggle(clicked)
            
                SVROptions.setCurrentIndex(el)
                clicked=toggle(clicked)
                imgView = gui.currentGui().editor.imageViews[2]
                                
            
                self.waitForViews([imgView])
            if clicked: 
                clicked=toggle(clicked)
            
            
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
        
    def test_8_changeSigmaValue(self):
        """
        Change the sigma value and check that works
         
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()
             
            gui.currentGui()._labelControlUi.liveUpdateButton.click()
            
            gui.currentGui()._labelControlUi.SigmaBox.setValue(6)
            
            imgView = gui.currentGui().editor.imageViews[2]
            self.waitForViews([imgView])
             
             
             
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
        



if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_test
    run_shell_test(__file__)
