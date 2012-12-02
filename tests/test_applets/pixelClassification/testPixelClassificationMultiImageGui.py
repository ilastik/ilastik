import os
import numpy
from PyQt4.QtGui import QApplication
from volumina.layer import AlphaModulatedLayer
from workflows.pixelClassification import PixelClassificationWorkflow
from tests.helpers import ShellGuiTestCaseBase
from lazyflow.operators import OpPixelFeaturesPresmoothed

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
    def setupClass(cls):
        # Base class first
        super(TestPixelClassificationGuiMultiImage, cls).setupClass()
        
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
    def teardownClass(cls):
        # Call our base class so the app quits!
        super(TestPixelClassificationGuiMultiImage, cls).teardownClass()

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
            shell.createAndLoadNewProject(projFilePath)
            workflow = shell.projectManager.workflow

            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            for i, dataFile in enumerate(self.SAMPLE_DATA):        
                # Add a file
                info = DatasetInfo()
                info.filePath = dataFile
                opDataSelection.Dataset.resize(i+1)
                opDataSelection.Dataset[i].setValue(info)
            
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
            assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == 0
            
            # Add label classes
            for i in range(3):
                gui.currentGui()._labelControlUi.AddLabelButton.click()
                assert gui.currentGui()._labelControlUi.labelListModel.rowCount() == i+1

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
                assert opPix.MaxLabelValue.value == i+1

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

            # Clear all the labels
            while len(gui.currentGui()._labelControlUi.labelListModel) > 0:
                gui.currentGui()._labelControlUi.labelListModel.removeRow(0)
                
            # Let the GUI catch up: Process all events
            QApplication.processEvents()

            # Re-add all labels
            self.test_4_AddLabels()

            # Enable interactive mode            
            assert gui.currentGui()._viewerControlUi.liveUpdateButton.isChecked() == False
            gui.currentGui()._viewerControlUi.liveUpdateButton.click()

            self.waitForViews(gui.currentGui().editor.imageViews)

            # Disable iteractive mode.            
            gui.currentGui()._viewerControlUi.liveUpdateButton.click()

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
    from tests.helpers.shellGuiTestCaseBase import run_shell_nosetest
    run_shell_nosetest(__file__)








