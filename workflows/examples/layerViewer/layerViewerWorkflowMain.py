from ilastik.shell.gui.startShellGui import startShellGui
from layerViewerWorkflow import LayerViewerWorkflow

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
    #info.filePath = '/magnetic/gigacube.h5'
    info.filePath = '/magnetic/5d.npy'
    #info.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
    
    # Save the project
    shell.onSaveProjectActionTriggered()

if __name__ == "__main__":    
    startShellGui( LayerViewerWorkflow )
    #startShellGui( LayerViewerWorkflow, debug_with_new )
