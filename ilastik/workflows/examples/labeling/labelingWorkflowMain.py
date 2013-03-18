from ilastik.shell.gui.startShellGui import startShellGui
from labelingWorkflow import LabelingWorkflow

def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"
    # Open a project
    shell.openProjectFile(projFilePath)

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(1)

def debug_with_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    info.filePath = '/magnetic/gigacube.h5'
    #info.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
    
    # Save the project
    shell.onSaveProjectActionTriggered()

if __name__ == "__main__":    
    startShellGui( LabelingWorkflow )
    #startShellGui( LabelingWorkflow, debug_with_new )
    #startShellGui( LabelingWorkflow, debug_with_existing )
