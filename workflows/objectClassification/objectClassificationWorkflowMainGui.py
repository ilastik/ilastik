from ilastik.shell.gui.startShellGui import startShellGui
from objectClassificationWorkflow import ObjectClassificationWorkflow as pixel_workflow
from objectClassificationWorkflowBinary import ObjectClassificationWorkflowBinary as binary_workflow

    rawInfo = DatasetInfo()
    rawInfo.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/singleslice.h5'

    opDataSelection = workflow.rawDataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(rawInfo)

    binaryInfo = DatasetInfo()
    #info.filePath = '/magnetic/gigacube.h5'
    binaryInfo.filePath = '/magnetic/synapse_small_binary.npy'
    opDataSelection.Dataset[0].setValue(binaryInfo)
    #featureGui = workflow.featureSelectionApplet._gui
    #opFeatures = workflow.featureSelectionApplet.topLevelOperator
    #opFeatures.SelectionMatrix.setValue(selections)
    #shell.setSelectedAppletDrawer(2)
    #shell.setSelectedAppletDrawer(3)

if __name__=="__main__":

    from optparse import OptionParser
    usage = "%prog [options] filename"
    parser = OptionParser(usage)
    parser.add_option("-b", "--binary",
                      action="store_true",
                      dest="binary",
                      default=False,
                      help="use binary workflow")

    (options, args) = parser.parse_args()

    #options.binary = True

    if options.binary:
        workflow = binary_workflow
    else:
        workflow = pixel_workflow

    # Start the GUI
    if len(args) == 1:
        def loadProject(shell):
            shell.openProjectFile(args[0])
        startShellGui(workflow, loadProject)
    elif len(args) == 0:
        startShellGui(workflow)
    else:
        parser.error("incorrect number of arguments")
