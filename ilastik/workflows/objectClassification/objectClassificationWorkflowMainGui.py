from ilastik.shell.gui.startShellGui import startShellGui
from objectClassificationWorkflow import ObjectClassificationWorkflowPixel as pixel_workflow
from objectClassificationWorkflow import ObjectClassificationWorkflowBinary as binary_workflow
from objectClassificationWorkflow import ObjectClassificationWorkflowPrediction as prediction_workflow

def debug_with_existing(shell):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"
    #projFilePath = "/magnetic/best_v4_imported_snapshot.ilp"
    #projFilePath = "/home/bergs/MyProject.ilp"
    #projFilePath = '/magnetic/gigacube.ilp'
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
    #projFilePath = '/magnetic/250-2.ilp'
    # Open a project
    shell.openProjectFile(projFilePath)

    # Select a default drawer
    shell.setSelectedAppletDrawer(5)

def debug_with_new(shell):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    workflow = shell.projectManager.workflow

    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo

    rawInfo = DatasetInfo()
    rawInfo.filePath = '/magnetic/synapse_small.npy'
    opDataSelection = workflow.rawDataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(rawInfo)
    
    binaryInfo = DatasetInfo()
    binaryInfo.filePath = '/magnetic/synapse_small_binary.npy'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(binaryInfo)
    
    #shell.setSelectedAppletDrawer(2)

if __name__=="__main__":

    from optparse import OptionParser
    usage = "%prog [options] filename"
    parser = OptionParser(usage)
    parser.add_option("-b", "--binary",
                      action="store_true",
                      dest="binary",
                      default=False,
                      help="start workflow from segmentation")
    parser.add_option("-p", "--prediction",
                      action="store_true",
                      dest="prediction",
                      default=False,
                      help="start workflow from predictions")

    (options, args) = parser.parse_args()

    #options.binary = True

    if options.binary:
        workflow = binary_workflow
    elif options.prediction:
        workflow = prediction_workflow
    else:
        workflow = pixel_workflow

    # Start the GUI
    if len(args) == 1:
        def loadProject(shell):
            shell.openProjectFile(args[0])
        startShellGui(workflow, loadProject)
    elif len(args) == 0:
        startShellGui(workflow)
        #startShellGui(workflow, debug_with_new)
        #startShellGui(workflow, debug_with_existing)
    else:
        parser.error("incorrect number of arguments")
