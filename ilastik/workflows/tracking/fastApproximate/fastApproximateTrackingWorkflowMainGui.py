from ilastik.shell.gui.startShellGui import startShellGui
from fastApproximateTrackingWorkflow import FastApproximateTrackingWorkflow


debug_testing = False

if debug_testing:
    def test(shell, workflow):
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
        shell.setSelectedAppletDrawer(2)
    
    startShellGui( FastApproximateTrackingWorkflow, test )

else:
    startShellGui( FastApproximateTrackingWorkflow )
