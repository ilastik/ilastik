from functools import partial

def debug_with_existing(shell):
    """
    (Function for debug and testing.)
    """
    #projFilePath = "/magnetic/test_project.ilp"
    #projFilePath = "/magnetic/best_v4_imported_snapshot.ilp"
    projFilePath = "/home/bergs/MyProject.ilp"
    #projFilePath = '/magnetic/gigacube.ilp'
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
    #projFilePath = '/magnetic/250-2.ilp'
    # Open a project
    shell.openProjectFile(projFilePath)

    # Select a default drawer
    shell.setSelectedAppletDrawer(5)

def debug_with_new(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/magnetic/test_project.ilp"

    # New project
    shell.createAndLoadNewProject(projFilePath)

    # Add a file
    from ilastik.applets.dataSelection.opDataSelection import DatasetInfo
    info = DatasetInfo()
    info.filePath = '/magnetic/gigacube.h5'
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
#    selections = numpy.array( [[True, True, True,  True, True, True, True],
#                               [True, True, True,  True, True, True, True],
#                               [True, True, True,  True, True, True, True],
#                               [True, True, True,  True, True, True, True],
#                               [True, True, True,  True, True, True, True],
#                               [True, True, True,  True, True, True, True]] )
    selections = numpy.array( [[True, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False],
                               [False, False, False, False, False, False, False]] )
    opFeatures.SelectionMatrix.setValue(selections)

    # Select the feature drawer
    shell.setSelectedAppletDrawer(2)

    # Save the project
    shell.onSaveProjectActionTriggered()

def debug_with_imported(shell, workflow):
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

if __name__ == "__main__":

    # Special hack for Janelia: 
    # In some old versions of 0.5, the data was stored in tyxzc order.
    # We have no way of inspecting the data to determine this, so we allow 
    #  users to specify that their ilp is very old using the 
    #  assume_old_ilp_axes command-line flag
    import ilastik.utility.globals
    ilastik.utility.globals.ImportOptions.default_axis_order = 'tyxzc'

    import sys

    #sys.argv.append( "/Users/bergs/MyProject.ilp" )
    
    ## EXAMPLE PLAYBACK TESTING ARGS
    #sys.argv.append( "--playback_script=/Users/bergs/Documents/workspace/ilastik-meta/ilastik/tests/event_based/recording-20130450-2111.py" )
    #sys.argv.append( "--playback_speed=3" )
    #sys.argv.append( "--exit_on_failure" )

    import argparse
    parser = argparse.ArgumentParser( description="Ilastik Pixel Classification Workflow" )
    parser.add_argument('--playback_script', help='An event recording to play back after the main window has opened.', required=False)
    parser.add_argument('--playback_speed', help='Speed to play the playback script.', default=0.5, type=float)
    parser.add_argument('--exit_on_failure', help='Immediately call exit(1) if an unhandled exception occurs.', action='store_true', default=False)
    parser.add_argument('project', nargs='?', help='A project file to open on startup.')

    parsed_args = parser.parse_args()

    init_funcs = []

    # Start the GUI
    if parsed_args.project is not None:
        def loadProject(shell):
            shell.openProjectFile(parsed_args.project)
        init_funcs.append( loadProject )

    if parsed_args.playback_script is not None:
        from ilastik.utility.gui.eventRecorder import EventPlayer
        def play_recording(shell):
            player = EventPlayer(parsed_args.playback_speed)
            player.play_script(parsed_args.playback_script)
        init_funcs.append( partial(play_recording) )

    if parsed_args.exit_on_failure:
        old_excepthook = sys.excepthook
        def print_exc_and_exit(*args):
            old_excepthook(*args)
            sys.stderr.write("Exiting early due to an unhandled exception.  See error output above.\n")
            from PyQt4.QtGui import QApplication
            QApplication.exit(1)
        sys.excepthook = print_exc_and_exit

    from ilastik.shell.gui.startShellGui import startShellGui
    from pixelClassificationWorkflow import PixelClassificationWorkflow
    startShellGui( PixelClassificationWorkflow, *init_funcs )

    # Start the GUI with a debug project    

    #startShellGui( PixelClassificationWorkflow )    
    #startShellGui( PixelClassificationWorkflow, debug_with_existing )
    #startShellGui( PixelClassificationWorkflow, debug_with_new )

    # Test special transpose-on-import feature
    #startShellGui( PixelClassificationWorkflow, debug_with_imported )
