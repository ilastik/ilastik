from ilastik.shell.gui.startShellGui import startShellGui
from thresholdMaskingWorkflow import ThresholdMaskingWorkflow

debug_testing = True
if debug_testing:
    def test(shell):
        import h5py

        #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
        projFilePath = '/home/bergs/gigacube.ilp'        

        shell.openProjectFile(projFilePath)
    
    startShellGui( ThresholdMaskingWorkflow, test )

else:
    startShellGui( ThresholdMaskingWorkflow )
