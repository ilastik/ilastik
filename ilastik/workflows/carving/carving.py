#!/usr/bin/env python

import os 
import functools
from carvingWorkflow import CarvingWorkflow
import h5py

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

if __name__ == "__main__":
    import lazyflow
    import numpy
    from ilastik.shell.gui.startShellGui import startShellGui
    import socket
    import logging
    logging.basicConfig(level=logging.INFO)
    
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
    
    if len(args)==0:
        workflowKwargs={'hintoverlayFile' : options.hintoverlayFile,
                        'pmapoverlayFile' : options.pmapoverlayFile }
        
        def loadProject(shell):
        #   shell.openProjectFile("C:/Users/Ben/Desktop/carvingData/test3.ilp")
			pass
        
        startShellGui(functools.partial(CarvingWorkflow, **workflowKwargs),loadProject)
        
    elif len(args)==1:
        projectFilename = args[0]
        
        def loadProject(shell):
            shell.openProjectFile(projectFilename)
        
        workflowKwargs={'hintoverlayFile' : options.hintoverlayFile,
                        'pmapoverlayFile' : options.pmapoverlayFile }
        startShellGui( functools.partial(CarvingWorkflow, **workflowKwargs), loadProject)
        
    elif len(args) == 2:
        carvingGraphFilename = args[0]
        projectFilename = args[1]
        def loadProject(shell):
            if not os.path.exists(projectFilename):
                shell.createAndLoadNewProject(projectFilename)
            else:
                shell.openProjectFile(projectFilename)
            
            workflow = shell.projectManager.workflow
            # Add a file
            from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
            info = DatasetInfo()
            info.filePath = carvingGraphFilename + "/graph/raw"
            opDataSelection = workflow.dataSelectionApplet.topLevelOperator
            preprocessingApplet = workflow.preprocessingApplet
            
            preprocessingApplet.ThorbenWantsToAddAlreadyPreprocessedFilesDirectly(carvingGraphFilename)
            opDataSelection.Dataset.resize(1)
            opDataSelection.Dataset[0].setValue(info)

        workflowKwargs={'carvingGraphFile': carvingGraphFilename,
                        'hintoverlayFile' : options.hintoverlayFile,
                        'pmapoverlayFile' : options.pmapoverlayFile }
        startShellGui( functools.partial(CarvingWorkflow, **workflowKwargs), loadProject)
    else:
        parser.error("incorrect number of arguments %d, expected at most 2" % len(args))
