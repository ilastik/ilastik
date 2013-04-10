#!/usr/bin/env python

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
    
    from ilastik.utility.pathHelpers import PathComponents
    
    #convert path to convenient format
    path = PathComponents(args[0]).totalPath()
    
    def loadProject(shell):
        shell.openProjectFile(path)
    workflowClass = getWorkflowFromName(options.workflow)
    startShellGui(workflowClass,loadProject)
else:
    raise TypeError("please pass either no argument for showing the start screen or one argument which is a ilastik project file for opening a project directly")
