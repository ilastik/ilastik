import os
import numpy
from PyQt4.QtGui import QApplication
from volumina.layer import AlphaModulatedLayer
from workflow.autocontextClassificationWorkflow import AutocontextClassificationWorkflow
from tests.helpers import ShellGuiTestCaseBase
from lazyflow.operators import OpPixelFeaturesPresmoothed

class TestPixelClassificationGui(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the pixel classification workflow.
    
    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """
    
    @classmethod
    def workflowClass(cls):
        return AutocontextClassificationWorkflow

    PROJECT_FILE = os.path.split(__file__)[0] + '/test_project.ilp'
    #SAMPLE_DATA = os.path.split(__file__)[0] + '/synapse_small.npy'

    @classmethod
    def setupClass(cls):
        # Base class first
        super(TestPixelClassificationGui, cls).setupClass()
        
        if hasattr(cls, 'SAMPLE_DATA'):
            cls.using_random_data = False
        else:
            cls.using_random_data = True
            cls.SAMPLE_DATA = os.path.split(__file__)[0] + '/random_data.npy'
            data = numpy.random.random((200,200,50,1))
            data *= 256
            numpy.save(cls.SAMPLE_DATA, data.astype(numpy.uint8))

    @classmethod
    def teardownClass(cls):
        # Call our base class so the app quits!
        super(TestPixelClassificationGui, cls).teardownClass()

        # Clean up: Delete any test files we generated
        removeFiles = [ TestPixelClassificationGui.PROJECT_FILE ]
        if cls.using_random_data:
            removeFiles += [ TestPixelClassificationGui.SAMPLE_DATA ]

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
            shell.createAndLoadNewProject(projFilePath)
            workflow = shell.projectManager.workflow
        
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = self.SAMPLE_DATA
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.Dataset.resize(1)
            opDataSelection.Dataset[0].setValue(info)
            
            # Set some features
            featureGui = workflow.featureSelectionApplet.getMultiLaneGui()
            opFeatures = workflow.featureSelectionApplet.topLevelOperator
            opFeatures.FeatureIds.setValue( OpPixelFeaturesPresmoothed.DefaultFeatureIds )
            opFeatures.Scales.setValue( [0.3, 0.7, 1, 1.6, 3.5, 5.0, 10.0] )
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
            assert self.shell.appletBar.invisibleRootItem().childCount() == 0

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_3_OpenProject(self):
        def impl():
            self.shell.openProjectFile(self.PROJECT_FILE)
            assert self.shell.projectManager.currentProjectFile is not None

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    
    # These points are relative to the CENTER of the view
    LABEL_START = (-20,-20)
    LABEL_STOP = (20,20)
    LABEL_SAMPLE = (0,0)
    LABEL_ERASE_START = (-10,-10)
    LABEL_ERASE_STOP = (10,10)

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
            self.shell.setSelectedAppletDrawer(3)
            
            # Turn off the huds and so we can capture the raw image
            gui.currentGui().menuGui.actionToggleAllHuds.trigger()

            ## Turn off the slicing position lines
            ## FIXME: This disables the lines without unchecking the position  
            ##        box in the VolumeEditorWidget, making the checkbox out-of-sync
            #gui.currentGui().editor.navCtrl.indicateSliceIntersection = False

            # Do our tests at position 0,0,0
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)

            assert gui.currentGui()._viewerControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 0, "Got {} rows".format(gui.currentGui()._labelControlUi.labelListModel.rowCount())
            
            # Add label classes
            for i in range(3):
                gui.currentGui()._labelControlUi.AddLabelButton.click()
                assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == i+1, "Got {} rows".format(gui.currentGui()._labelControlUi.labelListModel.rowCount())

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
                assert opPix.MaxLabelValue.value == i+1, "Max label value was {}".format( opPix.MaxLabelValue.value )

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

    def test_5_DeleteLabel(self):
        """
        Delete a label from the label list.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opPix = pixClassApplet.topLevelOperator

            originalLabelColors = gui.currentGui()._colorTable16[1:4]
            originalLabelNames = [label.name for label in gui.currentGui().labelListData]

            # We assume that there are three labels to start with (see previous test)
            assert opPix.MaxLabelValue.value == 3, "Max label value was {}".format( opPix.MaxLabelValue.value )

            # Make sure that it's okay to delete a row even if the deleted label is selected.
            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.labelListModel.removeRow(1)

            # Let the GUI catch up: Process all events
            QApplication.processEvents()
            
            # Selection should auto-reset back to the first row.
            assert gui.currentGui()._labelControlUi.labelListModel.selectedRow() == 0, "Row {} was selected.".format(gui.currentGui()._labelControlUi.labelListModel.selectedRow())
            
            # Did the label get removed from the label array?
            assert opPix.MaxLabelValue.value == 2, "Max label value did not decrement after the label was deleted.  Expected 2, got {}".format( opPix.MaxLabelValue.value  )

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Check the actual rendering of the two views with remaining labels
            for i in [0,2]:
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = originalLabelColors[i]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

            # Make sure we actually deleted the middle label (it should no longer be visible)
            for i in [1]:
                imgView = gui.currentGui().editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                oldColor = originalLabelColors[i]
                assert observedColor != oldColor, "Label was not deleted."
            
            # Original layer should not be anywhere in the layerstack.
            for layer in gui.currentGui().layerstack:
                assert layer.name is not originalLabelNames[1], "Layer {} was still present in the stack.".format(layer.name)
            
            # All the other layers should be in the layerstack.
            for i in [0,2]:
                labelName = originalLabelNames[i]
                try:
                    index = gui.currentGui().layerstack.findMatchingIndex(lambda layer: labelName in layer.name)
                    layer = gui.currentGui().layerstack[index]
                    
                    # Check the color
                    assert isinstance(layer, AlphaModulatedLayer), "layer is {}".format( layer )
                    assert layer.tintColor.rgba() == originalLabelColors[i], "Expected {}, got {}".format( hex(originalLabelColors[i]), hex(layer.tintColor.rgba()) )
                except ValueError:
                    assert False, "Could not find layer for label with name: {}".format(labelName)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_6_EraseSome(self):
        """
        Erase a few of the previously drawn labels from the volume editor using the eraser.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

            assert gui.currentGui()._viewerControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Row count was {}".format( gui.currentGui()._labelControlUi.labelListModel.rowCount() )
            
            # Use the first view for this test
            imgView = gui.currentGui().editor.imageViews[0]

            # Sanity check: There should be labels in the view that we can erase
            self.waitForViews([imgView])
            observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            labelColor = gui.currentGui()._colorTable16[1]
            assert observedColor == labelColor, "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format( hex(labelColor), hex(observedColor) )

            # Hide labels and sample raw data
            labelLayer = gui.currentGui().layerstack[0]
            assert labelLayer.name == "Labels", "Layer name was wrong: {}".labelLayer.name
            labelLayer.visible = False            
            self.waitForViews([imgView])
            rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert rawDataColor != labelColor, "Pixel color was not correct after label was hidden.  rawDataColor: {}, labelColor: {}".format(hex(rawDataColor), hex(labelColor))
            
            # Show labels
            labelLayer.visible = True
            # Select the eraser and brush size
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.waitForViews([imgView])
            
            # Erase and verify
            self.strokeMouseFromCenter( imgView, self.LABEL_ERASE_START, self.LABEL_ERASE_STOP )
            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert erasedColor == rawDataColor, "Pixel color was not correct after label was erased.  Expected {}, got {}".format(hex(rawDataColor), hex(erasedColor))
        
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    def test_7_EraseCompleteLabel(self):
        """
        Erase all of the labels of a particular color using the eraser.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()
            opPix = pixClassApplet.topLevelOperator

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

            assert gui.currentGui()._viewerControlUi.liveUpdateButton.isChecked() == False
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 2, "Row count was {}".format( gui.currentGui()._labelControlUi.labelListModel.rowCount() )

            assert opPix.MaxLabelValue.value == 2, "Max label value was wrong. Expected 2, got {}".format( opPix.MaxLabelValue.value  )
            
            # Use the third view for this test (which has the max label value)
            imgView = gui.currentGui().editor.imageViews[2]

            # Sanity check: There should be labels in the view that we can erase
            self.waitForViews([imgView])
            observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            labelColor = gui.currentGui()._colorTable16[2]
            assert observedColor == labelColor, "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format( hex(labelColor), hex(observedColor) )

            # Hide labels and sample raw data
            labelLayer = gui.currentGui().layerstack[0]
            assert labelLayer.name == "Labels"
            labelLayer.visible = False            
            self.waitForViews([imgView])
            rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert rawDataColor != labelColor, "Pixel color was not correct after label was hidden.  rawDataColor: {}, labelColor: {}".format(hex(rawDataColor), hex(labelColor))
            
            # Show labels
            labelLayer.visible = True
            # Select the eraser and brush size
            gui.currentGui()._labelControlUi.eraserToolButton.click()
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.waitForViews([imgView])
            
            # Erase and verify
            self.strokeMouseFromCenter( imgView, self.LABEL_START, self.LABEL_STOP )
            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert erasedColor == rawDataColor, "Eraser did not remove labels! Expected {}, got {}".format( hex(rawDataColor), hex(erasedColor) )

            # We just erased all the labels of value 2, so the max label value should be reduced.
            assert opPix.MaxLabelValue.value == 1, "Max label value was wrong. Expected 2, got {}".format( opPix.MaxLabelValue.value  )

            # Now stroke the eraser once more.
            # The new stroke should make NO DIFFERENCE to the image.
            rawDataColor = self.getPixelColor(imgView, (5,-5))
            self.strokeMouseFromCenter( imgView, (10,-10), (0,0) )
            
            # Move the cursor out of the way so we can sample the image
            self.moveMouseFromCenter(imgView, (20,20))

            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, (5,-5))
            assert erasedColor == rawDataColor, "Erasing blank pixels generated non-zero labels. Expected {}, got {}".format( hex(rawDataColor), hex(erasedColor) )

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_8_InteractiveMode(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            pixClassApplet = workflow.pcApplet
            gui = pixClassApplet.getMultiLaneGui()

            # Clear all the labels
            while len(gui.currentGui()._labelControlUi.labelListModel) > 0:
                gui.currentGui()._labelControlUi.labelListModel.removeRow(0)
                
            # Re-add all labels
            self.test_4_AddLabels()

            # Enable interactive mode            
            assert gui.currentGui()._viewerControlUi.liveUpdateButton.isChecked() == False
            gui.currentGui()._viewerControlUi.liveUpdateButton.click()

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Disable iteractive mode.            
            gui.currentGui()._viewerControlUi.pauseUpdateButton.click()

            self.waitForViews(gui.currentGui().editor.imageViews)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)
    



if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_nosetest
    run_shell_nosetest(__file__)