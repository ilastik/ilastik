import ilastik.utility.monkey_patches # Must be the first import

from ilastik.shell.gui.startShellGui import startShellGui
from trackingWorkflow import TrackingWorkflow
from trackingWorkflowNN import TrackingWorkflowNN


debug_testing = True
#method = 'chaingraph'
method = 'nearest_neighbor'

if debug_testing:
    def test(shell, workflow):
        import h5py

        #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
        #projFilePath = '/home/bkausler/withLabelImageAndRegionCenters.ilp'
        #projFilePath = '/home/mschiegg/hufnagel2012-08-03/375-386_classification.ilp'        
        projFilePath = '/home/mschiegg/hufnagel2012-08-03/segmentation/375-386_tracking.ilp'
        
        #shell.createAndLoadNewProject(projFilePath)
        shell.openProjectFile(projFilePath)        
        #from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
        #info = DatasetInfo()
        #info.filePath = '/magnetic/gigacube.h5'
        #info.filePath = '/home/mschiegg/hufnagel2012-08-03/375-386diff_results_rgb.h5'
        #info.filePath = '/magnetic/synapse_small.npy'
        #info.filePath = '/magnetic/singleslice.h5'
        #opDataSelection = workflow.dataSelectionApplet.topLevelOperator
        #opDataSelection.Dataset.resize(1)
        #opDataSelection.Dataset[0].setValue(info)
        shell.setSelectedAppletDrawer(1)
    
    if method == 'nearest_neighbor':
        startShellGui( TrackingWorkflowNN, test )
    elif method == 'chaingraph':
        startShellGui( TrackingWorkflow, test )

else:
    if method == 'nearest_neighbor':
        startShellGui( TrackingWorkflowNN )
    elif method == 'chaingraph':
        startShellGui( TrackingWorkflow )
