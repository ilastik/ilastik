#!/usr/bin/env python

import os 
import functools
from carvingWorkflow import CarvingWorkflow

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

if __name__ == "__main__":
    import lazyflow
    import numpy
    from ilastik.shell.gui.startShellGui import startShellGui
    import socket
    import logging
    logging.basicConfig(level=logging.INFO)

#    import sys
#    sys.argv.append( "/magnetic/denk.h5" )
#    sys.argv.append( "/magnetic/carving_test.ilp" )

    graph = lazyflow.graph.Graph()
    
    from optparse import OptionParser
    usage = "%prog [options] <carving graph filename> <project filename to be created>"
    parser = OptionParser(usage)
    parser.add_option("--hintoverlay",
                  dest="hintoverlayFile", default=None,
                  help="specify a file which adds a hint overlay")
    
    parser.add_option("--pmapoverlay",
                  dest="pmapoverlayFile", default=None,
                  help="specify a file which adds a pmap overlay")

    options, args = parser.parse_args()
    print options,args
    
    if len(args) == 2:
        carvingGraphFilename = args[0]
        projectFilename = args[1]
        def loadProject(shell):
            if not os.path.exists(projectFilename):
                shell.createAndLoadNewProject(projectFilename)
            else:
                shell.openProjectFile(projectFilename)
            
            workflow = shell.projectManager.workflow
            workflow.setCarvingGraphFile(carvingGraphFilename)
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = carvingGraphFilename + "/graph/raw"
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            opDataSelection.Dataset.resize(1)
            opDataSelection.Dataset[0].setValue(info)
            shell.setSelectedAppletDrawer(2)

        workflowKwargs={'carvingGraphFile': carvingGraphFilename,
                        'hintoverlayFile' : options.hintoverlayFile,
                        'pmapoverlayFile' : options.pmapoverlayFile }
        startShellGui( functools.partial(CarvingWorkflow, **workflowKwargs), loadProject)
    else:
        parser.error("incorrect number of arguments %d, expected 2" % len(args))
