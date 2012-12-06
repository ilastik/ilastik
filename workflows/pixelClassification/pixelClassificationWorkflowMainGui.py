from ilastik.shell.gui.startShellGui import startShellGui
from pixelClassificationWorkflow import PixelClassificationWorkflow

import argparse

def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    #projFilePath = "/magnetic/test_project.ilp"
    projFilePath = "/magnetic/best_v4_imported_snapshot.ilp"
    #projFilePath = '/magnetic/gigacube.ilp'
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
    #projFilePath = '/magnetic/250-2.ilp'
    # Open a project
    shell.openProjectFile(projFilePath)

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(3)

def debug_with_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/home/mschiegg/debugging_proj.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    #info.filePath = '/magnetic/gigacube.h5'
    info.filePath = '/home/mschiegg/hufnagel2012-08-03/derived/raw/375-386.h5/volume/data'
    #info.filePath = '/magnetic/synapse_small.npy'
    #info.filePath = '/magnetic/singleslice.h5'
    opDataSelection = workflow.dataSelectionApplet.topLevelOperator
    opDataSelection.Dataset.resize(1)
    opDataSelection.Dataset[0].setValue(info)
    
    # Set some features
    import numpy
    featureGui = workflow.featureSelectionApplet.gui
    opFeatures = workflow.featureSelectionApplet.topLevelOperator
    #                    sigma:   0.3    0.7    1.0    1.6    3.5    5.0   10.0
    selections = numpy.array( [[True, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [True, False, False, False, True, False, False],   # tempDiff
                               [True, False, False, False, True, False, False]] ) # crossCorr
    opFeatures.SelectionMatrix.setValue(selections)

    # Select the feature drawer
    shell.setSelectedAppletDrawer(2)

    # Save the project
    shell.onSaveProjectActionTriggered()

def debug_with_imported(shell, workflow):
    import os
    import ilastik.utility.globals
    ilastik.utility.globals.ImportOptions.default_axis_order = 'tyxzc'
    
    importedFilePath = "/magnetic/best_v4_orig.ilp"
    
    # Create a blank project file
#    base = os.path.splitext(importedFilePath)[0]
#    newProjectFilePath = base + "_imported.ilp"
    #newProjectFilePath = "/groups/flyem/data/medulla-FIB-Z1211-25/ilp/best_v4_imported.ilp"
    newProjectFilePath = "/magnetic/best_v4_imported.ilp"

    # Import the project    
    shell.importProject(importedFilePath, newProjectFilePath)

    # Select the labeling drawer
    shell.setSelectedAppletDrawer(3)

def getArgParser():
    parser = argparse.ArgumentParser(description = "Pixel Classiflication Prediction GUI")
    parser.add_argument('--project', help='Path to an .ilp file to be loaded. If not specified, start with an empty proejct', default = '')
    parser.add_argument('--screen', help='Select screen to be displayed on startup', default = '0')
    return parser

def loadProject(shell, workflow):
            print "Opening existing project '" + project + "'"
            shell.openProjectFile(project)
            shell.setSelectedAppletDrawer(screen)

def loadNew(shell, worfklow):
            shell.setSelectedAppletDrawer(screen)

if __name__ == "__main__":
    
    usage = "%prog [options] [filename]"
    parser = getArgParser()
    options = vars(parser.parse_args())
    screen = int(options['screen'])
    project = options['project']

    # Start the GUI
#    if len(args) == 1:
#        def loadProject(shell, workflow):
#            shell.openProjectFile(args[0])
#        startShellGui( PixelClassificationWorkflow, loadProject )
#    elif len(args) == 0:
#        startShellGui( PixelClassificationWorkflow )
#    else:
#        parser.error("incorrect number of arguments")

    # Start the GUI with a debug project    
    #startShellGui( PixelClassificationWorkflow )    
    #startShellGui( PixelClassificationWorkflow, debug_with_existing )
    #startShellGui( PixelClassificationWorkflow, debug_with_new )

    # Test special transpose-on-import feature
    #startShellGui( PixelClassificationWorkflow, debug_with_imported )
    

    # Start GUI with command line arguments. To extend the options, edit getArgParser
    startupFunct = None
    if project != '':
        startupFunct = loadProject
    else:
        startupFunct = loadNew
    startShellGui( PixelClassificationWorkflow, startupFunct )
        

    # Test special transpose-on-import feature
    #startShellGui( PixelClassificationWorkflow, debug_with_imported )
 
