from ilastik.shell.gui.startShellGui import startShellGui
from ilastik.shell.gui.eventRecorder import EventRecorder
from thresholdMaskingWorkflow import ThresholdMaskingWorkflow

debug_testing = False
if debug_testing:
    
    def test(shell):
        projFilePath = '/Users/bergs/MyProject.ilp'
        shell.openProjectFile(projFilePath)
        eventRecorder = EventRecorder( parent=shell )
        eventRecorder.start()
    
    startShellGui( ThresholdMaskingWorkflow, test )
else:
    startShellGui( ThresholdMaskingWorkflow )

