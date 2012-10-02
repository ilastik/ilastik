import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.gui.startShellGui import startShellGui
from trackingWorkflow import TrackingWorkflow
from trackingWorkflowNN import TrackingWorkflowNN


debug_testing = False
if debug_testing:
    def test(shell, workflow):
        import h5py

        #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
        #projFilePath = '/home/bkausler/withLabelImageAndRegionCenters.ilp'
        projFilePath = '/home/mschiegg/hufnagel2012-08-03/375-386_classification.ilp'        

        shell.openProjectFile(projFilePath)        
        shell.setSelectedAppletDrawer(1)
        
    startShellGui( TrackingWorkflowNN, test )

else:
    startShellGui( TrackingWorkflowNN )
