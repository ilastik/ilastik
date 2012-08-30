from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWithWatershedWorkflow import PixelClassificationWithVigraWatershedWorkflow


def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"
    #projFilePath = '/magnetic/gigacube.ilp'
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
    #projFilePath = '/magnetic/250-2.ilp'
    # Open a project
    shell.openProjectFile(projFilePath)

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(3)

def debug_with_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_watershed_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    info.filePath = '/magnetic/gigacube.h5'
    #info.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/synapse_small.npy_results.h5'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)

    # Select the watershed drawer
    shell.setSelectedAppletDrawer(1)

    # Save the project
    shell.onSaveProjectActionTriggered()


if __name__ == "__main__":
    startShellGui( PixelClassificationWithVigraWatershedWorkflow )
    #startShellGui( PixelClassificationWithVigraWatershedWorkflow, debug_with_new )
    #startShellGui( PixelClassificationWithVigraWatershedWorkflow, debug_with_existing )





