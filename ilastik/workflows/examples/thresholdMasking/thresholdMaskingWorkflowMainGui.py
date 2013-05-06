from ilastik.shell.gui.startShellGui import startShellGui
from thresholdMaskingWorkflow import ThresholdMaskingWorkflow

debug_testing = False
if debug_testing:
    
    def test(shell):
        projFilePath = '/Users/bergs/MyProject.ilp'
        shell.openProjectFile(projFilePath)
        
    
    startShellGui( ThresholdMaskingWorkflow, test )
else:
    startShellGui( ThresholdMaskingWorkflow )

