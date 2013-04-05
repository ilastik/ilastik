#!/usr/bin/env python

import os 
import functools
from carvingWorkflow import CarvingWorkflow
from ilastik.applets.base.appletSerializer import getOrCreateGroup, deleteIfPresent # ilp-File-Management
import h5py

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

if __name__ == "__main__":
    import lazyflow
    from ilastik.shell.gui.startShellGui import startShellGui
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
        
        carvingGraphFilename = os.path.abspath(args[0]).replace("\\","/")
        projectFilename = args[1]
        
        projectFile = h5py.File(projectFilename)
        
        preproc = getOrCreateGroup(projectFile,"preprocessing")
        
        deleteIfPresent(preproc, "sigma")
        deleteIfPresent(preproc, "filter")
        deleteIfPresent(preproc, "StorageVersion")
        deleteIfPresent(preproc, "graph")
        deleteIfPresent(preproc, "graphfile")
        
        preproc.create_dataset("sigma",data= 1.6)
        preproc.create_dataset("filter",data= 0)
        preproc.create_dataset("graphfile",data = carvingGraphFilename)
        preproc.create_dataset("StorageVersion",data = 0.1)
        
        preproc = getOrCreateGroup(projectFile,"preprocessing")
        dataSelect = getOrCreateGroup(projectFile,"Input Data")
        dataInfo = getOrCreateGroup(dataSelect,"infos")
        dataThisInfo = getOrCreateGroup(dataInfo,"info0000")
        deleteIfPresent(dataThisInfo,"filePath")
        deleteIfPresent(dataThisInfo,"location")
        deleteIfPresent(dataThisInfo,"datasetId")
        
        deleteIfPresent(dataThisInfo,"allowLabels")
        dataThisInfo.create_dataset("filePath",data = carvingGraphFilename+"/graph/raw")
        dataThisInfo.create_dataset("location",data = "FileSystem")
        dataThisInfo.create_dataset("datasetId",data = "E42")
        dataThisInfo.create_dataset("allowLabels",data = True)
        
        def loadProject(shell):
            shell.openProjectFile(projectFilename)

        workflowKwargs={'carvingGraphFile': carvingGraphFilename,
                        'hintoverlayFile' : options.hintoverlayFile,
                        'pmapoverlayFile' : options.pmapoverlayFile }
        startShellGui( functools.partial(CarvingWorkflow, **workflowKwargs), loadProject)
    else:
        parser.error("incorrect number of arguments %d, expected at most 2" % len(args))
