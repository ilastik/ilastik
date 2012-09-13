import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.gui.startShellGui import startShellGui
from trackingWorkflow import TrackingWorkflow


debug_testing = True
if debug_testing:
    def test(shell, workflow):
        import h5py

        #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
        projFilePath = '/home/bkausler/withLabelImageAndRegionCenters.ilp'

        shell.openProjectFile(projFilePath)
        
    
    startShellGui( TrackingWorkflow, test )

else:
    startShellGui( TrackingWorkflow )
