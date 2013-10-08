#Fixme: this test currently fails due to an issue to be fixed
# Checks that the boxes remains in the image when switching image
# Other things to be tested:
# - interaction with boxes : move them around etc...


import os
import numpy
from PyQt4.QtGui import QApplication,QKeyEvent
from PyQt4.QtCore import QEvent,Qt
from ilastik.workflows.counting import CountingWorkflow
from tests.helpers import ShellGuiTestCaseBase
from lazyflow.operators import OpPixelFeaturesPresmoothed

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
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/0.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/1.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/2.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/3.npy')
    SAMPLE_DATA.append( os.path.split(__file__)[0] + '/4.npy')




    @classmethod
    def setupClass(cls):
        # Base class first
        super(TestObjectCountingGuiMultiImage, cls).setupClass()

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
    def teardownClass(cls):
        # Call our base class so the app quits!
        super(TestObjectCountingGuiMultiImage, cls).teardownClass()

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


                opDataSelection.DatasetGroup.resize(i+1)
                opDataSelection.DatasetGroup[i][0].setValue(info)

            # Set some features
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
            assert self.shell.appletBar.count() == 0

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    def test_3_OpenProject(self):
        def impl():
            self.shell.openProjectFile(self.PROJECT_FILE)
            assert self.shell.projectManager.currentProjectFile is not None

        # Run this test from within the shell event loop
        self.exec_in_shell(impl)

    # These points are relative to the CENTER of the view
    LABEL_START = (-10,-10)
    LABEL_STOP = (-10,0)
    LABEL_SAMPLE = (0,0)
    LABEL_ERASE_START = (-10,-10)
    LABEL_ERASE_STOP = (10,10)


    def test_4_AddDotsAndBackground(self):
        """
        Add labels and draw them in the volume editor.
        """
        def impl():


            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()

            opPix = countingClassApplet.topLevelOperator
            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()


            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

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

            dot_start_list = [(-20,-20),(15,-15),(9,-3)]
            dot_stop_list = [(-20,-19),(15,-14),(8,-3)]

            for start,stop in zip(dot_start_list,dot_stop_list):
                self.strokeMouseFromCenter( imgView, start,stop )


            # Set the brush size
            gui.currentGui()._labelControlUi.labelListModel.select(1)
            gui.currentGui()._labelControlUi.brushSizeComboBox.setCurrentIndex(6)

            self.strokeMouseFromCenter( imgView, self.LABEL_START,self.LABEL_STOP)

            #The background in this configuration should override the dots
            labelData = opPix.LabelImages[0][:].wait()
            assert labelData.max() == 2, "Max label value was {}".format( labelData.max() )


            labelData = opPix.LabelImages[0][:].wait()
            assert numpy.sum(labelData[labelData==1]) == 2, "Max label value was {}".format( labelData.max() )



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
            self.shell.setSelectedAppletDrawer(3)

            # Turn off the huds and so we can capture the raw image
            viewMenu = gui.currentGui().menus()[0]
            viewMenu.actionToggleAllHuds.trigger()



            # Select the labeling drawer
            self.shell.setSelectedAppletDrawer(3)

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


    # def test_7_InteractiveMode(self):
    #     """
    #     Click the "interactive mode" to see if anything crashes for each of the available counting modalities.

    #     """
    #     def impl():
    #         workflow = self.shell.projectManager.workflow
    #         countingClassApplet = workflow.countingApplet
    #         gui = countingClassApplet.getMultiLaneGui()


    #         clicked=False
    #         def toggle(clicked):
    #             clicked= not clicked
    #             gui.currentGui()._labelControlUi.liveUpdateButton.click()
    #             return clicked

    #         SVROptions=gui.currentGui()._labelControlUi.SVROptions

    #         #Test each one of the counting modality which is registered
    #         for el in range(SVROptions.count()):
    #             if clicked:
    #                 clicked=toggle(clicked)

    #             SVROptions.setCurrentIndex(el)
    #             clicked=toggle(clicked)
    #             imgView = gui.currentGui().editor.imageViews[2]


    #             self.waitForViews([imgView])
    #         if clicked:
    #             clicked=toggle(clicked)


    #     # Run this test from within the shell event loop
    #     self.exec_in_shell(impl)


    def test_7_SwitchImages(self):
        """
        Switch back and forth between a labeled image and an unlabeled one.  boxes should disappear and then reappear.
        """
        def impl():
            workflow = self.shell.projectManager.workflow
            countingClassApplet = workflow.countingApplet
            gui = countingClassApplet.getMultiLaneGui()


            # Select the second image
            self.shell.imageSelectionCombo.setCurrentIndex(1)
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
            assert added_boxes==3," Not all boxes added to the model curr = %d"%added_boxes


            # Select the second image
            self.shell.imageSelectionCombo.setCurrentIndex(1)
            gui = countingClassApplet.getMultiLaneGui()
            gui.currentGui().editor.posModel.slicingPos = (0,0,0)
            self.waitForViews(gui.currentGui().editor.imageViews)




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

                assert density[0]>0,"Density value is not updated \
                {0:.2f} #########################################################".format(density[0])

            #if clicked:
                #clicked=toggle(clicked)
        # Run this test from within the shell event loop
        self.exec_in_shell(impl)


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
    from tests.helpers.shellGuiTestCaseBase import run_shell_nosetest
    run_shell_nosetest(__file__)








