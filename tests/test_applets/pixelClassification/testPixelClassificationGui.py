from PyQt4.QtGui import QApplication
from volumina.layer import AlphaModulatedLayer
from workflows.pixelClassification import PixelClassificationWorkflow
from tests.helpers import ShellGuiTestCaseBase

class TestPixelClassificationGui(ShellGuiTestCaseBase):
    """
    Run a set of GUI-based tests on the pixel classification workflow.
    
    Note: These tests are named in order so that simple cases are tried before complex ones.
          Additionally, later tests may depend on earlier ones to run properly.
    """
    
    @classmethod
    def workflowClass(cls):
        return PixelClassificationWorkflow

    SAMPLE_DATA = '/magnetic/synapse_small.npy'
    PROJECT_FILE = '/magnetic/test_project.ilp'

    @classmethod
    def teardownClass(cls):
        """
        Call our base class to quit the app during teardown.
        (Comment this out if you want the app to stay open for further debugging.)
        """
        super(TestPixelClassificationGui, cls).teardownClass()

    def test_1_NewProject(self):
        """
        Create a blank project, manipulate few couple settings, and save it.
        """
        def impl():
            projFilePath = self.PROJECT_FILE
        
            shell = self.shell
            workflow = self.workflow
            
            # New project
            shell.createAndLoadNewProject(projFilePath)
        
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = self.SAMPLE_DATA
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.Dataset.resize(1)
            opDataSelection.Dataset[0].setValue(info)
            
            # Set some features
            import numpy
            featureGui = workflow.featureSelectionApplet.gui
            opFeatures = workflow.featureSelectionApplet.topLevelOperator
            opFeatures.Scales.setValue( featureGui.ScalesList )
            opFeatures.FeatureIds.setValue( featureGui.FeatureIds )
            #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
            selections = numpy.array( [[True, False, False, False, False, False, False],
                                       [True, False, False, False, False, False, False],
                                       [True, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False]] )
            opFeatures.SelectionMatrix.setValue(selections)
        
            # Save the project
            shell.onSaveProjectActionTriggered()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    # These points are relative to the CENTER of the view
    LABEL_START = (-20,-20)
    LABEL_STOP = (20,20)
    LABEL_SAMPLE = (0,0)
    LABEL_ERASE_START = (-5,-5)
    LABEL_ERASE_STOP = (5,5)

    def test_2_AddLabels(self):
        """
        Add labels and draw them in the volume editor.
        """
        def impl():
            pixClassApplet = self.workflow.pcApplet
            gui = pixClassApplet.gui
            opPix = pixClassApplet.topLevelOperator

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)
            
            # Turn of the huds so we can capture the raw image
            gui.menuGui.actionToggleAllHuds.trigger()

            assert not gui._labelControlUi.checkInteractive.isChecked()
            assert gui._labelControlUi.labelListModel.rowCount() == 0
            
            # Add label classes
            for i in range(3):
                gui._labelControlUi.AddLabelButton.click()
                assert gui._labelControlUi.labelListModel.rowCount() == i+1

            # Select the brush
            gui._labelControlUi.paintToolButton.click()

            # Set the brush size
            gui._labelControlUi.brushSizeComboBox.setCurrentIndex(1)

            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            # Draw some arbitrary labels in each view using mouse events.
            for i in range(3):
                # Post this as an event to ensure sequential execution.
                gui._labelControlUi.labelListModel.select(i)
                
                imgView = gui.editor.imageViews[i]
                self.strokeMouseFromCenter( imgView, self.LABEL_START, self.LABEL_STOP )

                # Make sure the labels were added to the label array operator
                assert opPix.MaxLabelValue.value == i+1

            self.waitForViews(gui.editor.imageViews)

            # Verify the actual rendering of each view
            for i in range(3):
                imgView = gui.editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = gui._colorTable16[i+1]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

            # Save the project
            self.shell.onSaveProjectActionTriggered()

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_3_DeleteLabel(self):
        """
        Delete a label from the label list.
        """
        def impl():
            pixClassApplet = self.workflow.pcApplet
            gui = pixClassApplet.gui
            opPix = pixClassApplet.topLevelOperator

            originalLabelColors = gui._colorTable16[1:4]
            originalLabelNames = [label.name for label in gui.labelListData]

            # We assume that there are three labels to start with (see previous test)
            assert opPix.MaxLabelValue.value == 3

            # Make sure that it's okay to delete a row even if the deleted label is selected.
            gui._labelControlUi.labelListModel.select(1)
            gui._labelControlUi.labelListModel.removeRow(1)

            # Let the GUI catch up: Process all events
            QApplication.processEvents()
            
            # Selection should auto-reset back to the first row.
            assert gui._labelControlUi.labelListModel.selectedRow() == 0
            
            # Did the label get removed from the label array?
            assert opPix.MaxLabelValue.value == 2

            self.waitForViews(gui.editor.imageViews)

            # Check the actual rendering of the two views with remaining labels
            for i in [0,2]:
                imgView = gui.editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                expectedColor = originalLabelColors[i]
                assert observedColor == expectedColor, "Label was not drawn correctly.  Expected {}, got {}".format( hex(expectedColor), hex(observedColor) )                

            # Make sure we actually deleted the middle label (it should no longer be visible)
            for i in [1]:
                imgView = gui.editor.imageViews[i]
                observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
                oldColor = originalLabelColors[i]
                assert observedColor != oldColor, "Label was not deleted."
            
            # Original layer should not be anywhere in the layerstack.
            for layer in gui.layerstack:
                assert layer.name is not originalLabelNames[1]
            
            # All the other layers should be in the layerstack.
            for i in [0,2]:
                labelName = originalLabelNames[i]
                try:
                    index = gui.layerstack.findMatchingIndex(lambda layer: labelName in layer.name)
                    layer = gui.layerstack[index]
                    
                    # Check the color
                    assert isinstance(layer, AlphaModulatedLayer)
                    assert layer.tintColor.rgba() == originalLabelColors[i]
                except ValueError:
                    assert False, "Could not find layer for label with name: {}".format(labelName)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_4_EraseSome(self):
        """
        Erase a few of the previously drawn labels from the volume editor using the eraser.
        """
        def impl():
            pixClassApplet = self.workflow.pcApplet
            gui = pixClassApplet.gui

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

            assert not gui._labelControlUi.checkInteractive.isChecked()
            assert gui._labelControlUi.labelListModel.rowCount() == 2
            
            # Use the first view for this test
            imgView = gui.editor.imageViews[0]

            # Sanity check: There should be labels in the view that we can erase
            self.waitForViews([imgView])
            observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            labelColor = gui._colorTable16[1]
            assert observedColor == labelColor, "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format( hex(labelColor), hex(observedColor) )

            # Hide labels and sample raw data
            labelLayer = gui.layerstack[0]
            assert labelLayer.name == "Labels"
            labelLayer.visible = False            
            self.waitForViews([imgView])
            rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert rawDataColor != labelColor
            
            # Show labels
            labelLayer.visible = True
            # Select the eraser and brush size
            gui._labelControlUi.eraserToolButton.click()
            gui._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.waitForViews([imgView])
            
            # Erase and verify
            self.strokeMouseFromCenter( imgView, self.LABEL_ERASE_START, self.LABEL_ERASE_STOP )
            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert erasedColor == rawDataColor
        
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_5_EraseCompleteLabel(self):
        """
        Erase all of the labels of a particular color using the eraser.
        """
        def impl():
            pixClassApplet = self.workflow.pcApplet
            gui = pixClassApplet.gui
            opPix = pixClassApplet.topLevelOperator

            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

            assert not gui._labelControlUi.checkInteractive.isChecked()
            assert gui._labelControlUi.labelListModel.rowCount() == 2

            assert opPix.MaxLabelValue.value == 2
            
            # Use the third view for this test (which has the max label value)
            imgView = gui.editor.imageViews[2]

            # Sanity check: There should be labels in the view that we can erase
            self.waitForViews([imgView])
            observedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            labelColor = gui._colorTable16[2]
            assert observedColor == labelColor, "Can't run erase test.  Missing the expected label.  Expected {}, got {}".format( hex(labelColor), hex(observedColor) )

            # Hide labels and sample raw data
            labelLayer = gui.layerstack[0]
            assert labelLayer.name == "Labels"
            labelLayer.visible = False            
            self.waitForViews([imgView])
            rawDataColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert rawDataColor != labelColor
            
            # Show labels
            labelLayer.visible = True
            # Select the eraser and brush size
            gui._labelControlUi.eraserToolButton.click()
            gui._labelControlUi.brushSizeComboBox.setCurrentIndex(3)
            self.waitForViews([imgView])
            
            # Erase and verify
            self.strokeMouseFromCenter( imgView, self.LABEL_START, self.LABEL_STOP )
            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, self.LABEL_SAMPLE)
            assert erasedColor == rawDataColor, "Eraser did not remove labels!"

            # We just erased all the labels of value 2, so the max label value should be reduced.
            assert opPix.MaxLabelValue.value == 1

            # Now stroke the eraser once more.
            # The new stroke should make NO DIFFERENCE to the image.
            rawDataColor = self.getPixelColor(imgView, (5,-5))
            self.strokeMouseFromCenter( imgView, (10,-10), (0,0) )
            
            # Move the cursor out of the way so we can sample the image
            self.moveMouseFromCenter(imgView, (20,20))

            self.waitForViews([imgView])
            erasedColor = self.getPixelColor(imgView, (5,-5))
            assert erasedColor == rawDataColor, "Erasing blank pixels generated non-zero labels."

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_6_InteractiveMode(self):
        """
        Click the "interactive mode" checkbox and see if any errors occur.
        """
        def impl():
            pixClassApplet = self.workflow.pcApplet
            gui = pixClassApplet.gui

            # Clear all the labels
            while len(gui._labelControlUi.labelListModel) > 0:
                gui._labelControlUi.labelListModel.removeRow(0)
                
            # Re-add all labels
            self.test_2_AddLabels()

            # Enable interactive mode            
            assert not gui._labelControlUi.checkInteractive.isChecked()
            gui._labelControlUi.checkInteractive.click()

            self.waitForViews(gui.editor.imageViews)

            # Disable iteractive mode.            
            gui._labelControlUi.checkInteractive.click()

            self.waitForViews(gui.editor.imageViews)

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

if __name__ == "__main__":
    from tests.helpers.shellGuiTestCaseBase import run_shell_nosetest
    run_shell_nosetest(__file__)








