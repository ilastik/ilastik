from ilastik.shell.gui.startShellGui import startShellGui
from vigraWatershedWorkflow import VigraWatershedWorkflow

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
    #info.filePath = '/magnetic/gigacube.h5'
    info.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)

    # Select the watershed drawer
    shell.setSelectedAppletDrawer(1)

    # Save the project
    shell.onSaveProjectActionTriggered()


if __name__ == "__main__":
    startShellGui( VigraWatershedWorkflow )
    #startShellGui( VigraWatershedWorkflow, debug_with_new )

