from ilastik.shell.gui.startShellGui import startShellGui
from optparse import OptionParser
import ilastik.workflows
from ilastik.workflow import getWorkflowFromName

usage = "%prog [options] <project file>"
parser = OptionParser(usage)
parser.add_option("--workflow",
              dest="workflow", default=None,
              help="specify a workflow that should be loaded")
options, args = parser.parse_args()

if len(args)==0:
    startShellGui(workflowClass=options.workflow)

elif len(args)==1:
    def loadProject(shell):
        shell.openProjectFile(args[0])
    workflowClass = getWorkflowFromName(options.workflow)
    startShellGui(workflowClass,loadProject)
