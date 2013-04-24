#import visvis as vv
from ilastik.shell.gui.startShellGui import startShellGui
from countingWorkflow import CountingWorkflow
import logging
logger = logging.getLogger("lazyflow.operators.operators.ArrayCacheMemoryMgr")
logger.setLevel('CRITICAL')

if __name__=="__main__":

    from optparse import OptionParser
    usage = "%prog [options] filename"
    parser = OptionParser(usage)

    (options, args) = parser.parse_args()

    # Start the GUI
    if len(args) == 1:
        def loadProject(shell):
            shell.openProjectFile(args[0])
        startShellGui(CountingWorkflow, loadProject)
    elif len(args) == 0:
        startShellGui(CountingWorkflow)
    else:
        parser.error("incorrect number of arguments")
