from tests.helpers import ShellGuiTestCaseBase
from workflows.pixelClassification import PixelClassificationWorkflow

class TestPixelClassificationGui(ShellGuiTestCaseBase):
    
    @classmethod
    def workflowClass(cls):
        return PixelClassificationWorkflow
    
    def testProjectOpen(self):
        def impl():
            projFilePath = '/magnetic/gigacube.ilp'
            self.shell.openProjectFile(projFilePath)
            assert self.shell.projectManager.currentProjectFile is not None

        self.exec_in_shell(impl)

    def testNewProject(self):
        """
        Create a blank project and manipulate a couple settings.
        Then save it.
        """
        def impl():
            projFilePath = "/magnetic/test_project.ilp"
        
            shell = self.shell
            workflow = self.workflow
            
            # New project
            shell.createAndLoadNewProject(projFilePath)
        
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = '/magnetic/gigacube.h5'
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.Dataset.resize(1)
            opDataSelection.Dataset[0].setValue(info)
            
            # Set some features
            import numpy
            opFeatures = workflow.featureSelectionApplet.topLevelOperator
            #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
            selections = numpy.array( [[False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False,  True, False, False], # ST EVs
                                       [False, False, False, False, False, False, False],
                                       [False, False, False, False, False, False, False],  # GGM
                                       [False, False, False, False, False, False, False]] )
            opFeatures.SelectionMatrix.setValue(selections)
        
            # Save the project
            shell.onSaveProjectActionTriggered()

        self.exec_in_shell(impl)

if __name__ == "__main__":
    import sys
    import nose
    sys.argv.append("--nocapture")    # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture") # Don't set the logging level to DEBUG.  Leave it alone.
    nose.run(defaultTest=__file__)
