from ilastik.shell.gui.startShellGui import startShellGui
from thresholdMaskingWorkflow import ThresholdMaskingWorkflow

debug_testing = False
if debug_testing:
    def test(shell, workflow):
        import h5py

        #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
        projFilePath = '/magnetic/MyProject.ilp'

        shell.openProjectFile(projFilePath)
    
    startShellGui( ThresholdMaskingWorkflow, test )

else:
    startShellGui( ThresholdMaskingWorkflow )
