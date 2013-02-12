from ilastik.shell.gui.startShellGui import startShellGui
from objectClassificationWorkflow import ObjectClassificationWorkflow


def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    # set this variable
    projFilePath = ""
    # Open a project
    shell.openProjectFile(projFilePath)


if __name__=="__main__":
    #startShellGui( ObjectClassificationWorkflow, debug_with_existing )
    startShellGui(ObjectClassificationWorkflow)