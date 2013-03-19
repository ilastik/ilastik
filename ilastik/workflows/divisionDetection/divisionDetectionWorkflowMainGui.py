from ilastik.shell.gui.startShellGui import startShellGui
from ilastik.workflows.divisionDetection.divisionDetectionWorkflow import DivisionDetectionWorkflow


if __name__=="__main__":

    from optparse import OptionParser
    usage = "%prog [options] filename"
    parser = OptionParser(usage)
#    parser.add_option("-b", "--binary",
#                      action="store_true",
#                      dest="binary",
#                      default=False,
#                      help="use binary workflow")
#
    (options, args) = parser.parse_args()
#
#    if options.binary:
#        workflow = binary_workflow
#    else:
    
    workflow = DivisionDetectionWorkflow

    # Start the GUI
    if len(args) == 1:
        def loadProject(shell):
            shell.openProjectFile(args[0])
        startShellGui(workflow, loadProject)
    elif len(args) == 0:
        startShellGui(workflow)
    else:
        parser.error("incorrect number of arguments")
