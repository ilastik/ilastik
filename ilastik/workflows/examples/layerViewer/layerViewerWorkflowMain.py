from ilastik.shell.gui.startShellGui import startShellGui
from layerViewerWorkflow import LayerViewerWorkflow

def debug_with_new(shell):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)
    # Save the project
    shell.onSaveProjectActionTriggered()

if __name__ == "__main__":    
    #startShellGui( LayerViewerWorkflow )
    startShellGui( LayerViewerWorkflow, debug_with_new )
    