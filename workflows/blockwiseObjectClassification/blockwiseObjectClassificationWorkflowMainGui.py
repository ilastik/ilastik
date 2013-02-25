from ilastik.shell.gui.startShellGui import startShellGui
from blockwiseObjectClassificationWorkflow import BlockwiseObjectClassificationWorkflow

def debug_with_existing(shell):
    """
    (Function for debug and testing.)
    """
    #projFilePath = "/magnetic/test_project.ilp"
    #projFilePath = "/magnetic/best_v4_imported_snapshot.ilp"
    projFilePath = "/home/bergs/MyProject.ilp"
    #projFilePath = '/magnetic/gigacube.ilp'
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
    #projFilePath = '/magnetic/250-2.ilp'
    # Open a project
    shell.openProjectFile(projFilePath)

    # Select a default drawer
    shell.setSelectedAppletDrawer(5)

def debug_with_new(shell):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)
    workflow = shell.projectManager.workflow

    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo

    # Add raw data file
    rawInfo = DatasetInfo()
    rawInfo.filePath = '/magnetic/synapse_small.npy'
    opDataSelection = workflow.rawDataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(rawInfo)

    # Add binary image file
    binaryInfo = DatasetInfo()
    binaryInfo.filePath = '/magnetic/synapse_small_binary.npy'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(binaryInfo)

    shell.setSelectedAppletDrawer(4)

if __name__=="__main__":
    #startShellGui(BlockwiseObjectClassificationWorkflow)
    startShellGui(BlockwiseObjectClassificationWorkflow, debug_with_new)
