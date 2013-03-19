from ilastik.shell.gui.startShellGui import startShellGui
from deviationFromMeanWorkflow import DeviationFromMeanWorkflow

debug_testing = False
if debug_testing:
    def test(shell):
        #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
        projFilePath = '/home/bergs/MyProject.ilp'

        shell.openProjectFile(projFilePath)
    
    startShellGui( DeviationFromMeanWorkflow, test )

else:
    startShellGui( DeviationFromMeanWorkflow )
