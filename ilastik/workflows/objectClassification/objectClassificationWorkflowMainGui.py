from ilastik.shell.gui.startShellGui import startShellGui
from objectClassificationWorkflow import ObjectClassificationWorkflowPixel as pixel_workflow
from objectClassificationWorkflow import ObjectClassificationWorkflowBinary as binary_workflow
from objectClassificationWorkflow import ObjectClassificationWorkflowPrediction as prediction_workflow
import os

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
    parser.add_option("-i", "--input",
                      dest="input",
                      default='pixel',
                      help="may be 'pixel', 'binary', or 'prediction'")
    parser.add_option("--fillmissing",
                      action="store_true",
                      dest="fill_missing",
                      default=False,
                      help="use 'fill missing' applet")
    parser.add_option("--filter",
                      dest="filter",
                      default='Original',
                      help="pixel feature filter implementation. 'Original', 'Refactored', or 'Interpolated'")


    (options, args) = parser.parse_args()

    inputs = {'pixel' : pixel_workflow,
              'binary' : binary_workflow,
              'prediction' : prediction_workflow}

    if options.input not in inputs:
        raise Exception("unknown input: '{}'".format(options.input))

    workflow = inputs[options.input]
    workflow_kwargs = {}
    workflow_kwargs['fillMissing'] = options.fill_missing
    workflow_kwargs['filterImplementation'] = options.filter

    # Start the GUI
    if len(args) != 1:
        parser.error("no project file name provided")

    filename = args[0]

    loadProject =  os.path.exists(filename)
    if loadProject:
        workflow = None

    def startProject(shell):
        if loadProject:
            shell.openProjectFile(filename)
        else:
            shell.createAndLoadNewProject(filename)

    startShellGui(workflow, startProject, **workflow_kwargs)
