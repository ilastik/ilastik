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
    #info.filePath = '/magnetic/synapse_small.npy'
    info.filePath = '/magnetic/synapse_small.npy_results.h5'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)

    # Select the watershed drawer
    shell.setSelectedAppletDrawer(1)

    # Save the project
    shell.onSaveProjectActionTriggered()


if __name__ == "__main__":
    from optparse import OptionParser
    usage = "%prog [options] filename"
    parser = OptionParser(usage)

    (options, args) = parser.parse_args()

    # Start the GUI
    if len(args) == 1:
        def loadProject(shell):
            shell.openProjectFile(args[0])
        startShellGui( VigraWatershedWorkflow, loadProject )
    elif len(args) == 0:
        startShellGui( VigraWatershedWorkflow )
    else:
        parser.error("incorrect number of arguments")
