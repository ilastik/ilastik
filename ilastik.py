#!/usr/bin/env python

# Standard
import sys
import argparse
import threading
import logging
from functools import partial

# Third-party
from ilastik.config import cfg as ilastik_config

# Initialize logging before anything else
from ilastik.ilastik_logging import default_config
default_config.init()

# Ilastik
logger = logging.getLogger(__name__)

def install_thread_excepthook():
    # This function was copied from: http://bugs.python.org/issue1230540
    # It is necessary because sys.excepthook doesn't work for unhandled exceptions in other threads.
    """
    Workaround for sys.excepthook thread bug
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psycho.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    run_old = threading.Thread.run
    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())
    threading.Thread.run = run

parser = argparse.ArgumentParser( description="start an ilastik workflow" )
parser.add_argument('--start_recording', help='Open the recorder controls and immediately start recording', action='store_true', default=False)
parser.add_argument('--playback_script', help='An event recording to play back after the main window has opened.', required=False)
parser.add_argument('--playback_speed', help='Speed to play the playback script.', default=1.0, type=float)
parser.add_argument('--exit_on_failure', help='Immediately call exit(1) if an unhandled exception occurs.', action='store_true', default=False)
parser.add_argument('--exit_on_success', help='Quit the app when the playback is complete.', action='store_true', default=False)
parser.add_argument('--project', help='A project file to open on startup.', required=False)
parser.add_argument('--new_project', help='Create a new project with the specified name.  Must also specify --workflow.', required=False)
parser.add_argument('--workflow', help='When used with --new_project, specifies the workflow to use.', required=False)
parser.add_argument('--debug', help='Start ilastik in debug mode.', action='store_true', default=False)
parser.add_argument('--fullscreen', help='Show Window in fullscreen mode.', action='store_true', default=False)
parser.add_argument('--headless', help="Don't start the ilastik gui.", action='store_true', default=False)

# Example:
# python ilastik.py --playback_speed=2.0 --exit_on_failure --exit_on_success --debug --playback_script=my_recording.py

# DEBUG
#sys.argv.append( '--split_tool_param_file=/magnetic/split-body-data/assignment980/assignment980_params.json' )

parsed_args, workflow_cmdline_args = parser.parse_known_args()
init_funcs = []

# DEBUG DEBUG
#parsed_args.project = '/magnetic/split-body-data/test_data2/full_proj2.ilp'
#parsed_args.project = '/magnetic/split-body-data/test_data2/small_proj2.ilp'
#parsed_args.project = '/home/bergs/MyProject.ilp'

# DEBUG
#parsed_args.headless = True
#parsed_args.new_project = '/home/bergs/MyProject.ilp'
#parsed_args.workflow = 'LayerViewerWorkflow'
#parsed_args.new_project = '/magnetic/split-body-data/assignment980/MyProject.ilp'
#parsed_args.workflow = 'SplitBodyCarvingWorkflow'


if parsed_args.start_recording:
    assert not parsed_args.playback_script is False, "Can't record and play back at the same time!  Choose one or the other"
    parsed_args.debug = True # Auto-enable debug mode
    def startRecording(shell):
        shell._recorderGui.openInPausedState()
    init_funcs.append(startRecording)

# Check for bad input options
if parsed_args.workflow is not None and parsed_args.new_project is None:
    sys.stderr.write("The --workflow argument may only be used with the --new_project argument.")
    sys.exit(1)
if parsed_args.workflow is None and parsed_args.new_project is not None:
    sys.stderr.write("No workflow specified.  The --new_project argument must be used in conjunction with the --workflow argument.")
    sys.exit(1)
if parsed_args.project is not None and parsed_args.new_project is not None:
    sys.stderr.write("The --project and --new_project settings cannot be used together.  Choose one (or neither).")
    sys.exit(1)

if not parsed_args.headless:
    # Only import GUI modules in non-headless mode.
    from PyQt4.QtGui import QApplication
elif parsed_args.start_recording or \
     parsed_args.playback_script or \
     parsed_args.fullscreen or \
     parsed_args.exit_on_failure or \
     parsed_args.exit_on_success:
    sys.stderr.write("Some of the command-line options you provided are not supported in headless mode.  Exiting.")
    sys.exit(1)

# Auto-open project
if parsed_args.project is not None:
    #convert path to convenient format
    from ilastik.utility.pathHelpers import PathComponents
    path = PathComponents(parsed_args.project).totalPath()
    
    def loadProject(shell):
        # This should work for both the IlastikShell and the HeadlessShell
        shell.openProjectFile(path)
    init_funcs.append(loadProject)

# Auto-create new project
if parsed_args.new_project is not None:
    #convert path to convenient format
    from ilastik.utility.pathHelpers import PathComponents
    path = PathComponents(parsed_args.new_project).totalPath()
    def createNewProject(shell):
        import ilastik.workflows
        from ilastik.workflow import getWorkflowFromName
        workflow_class = getWorkflowFromName(parsed_args.workflow)
        if workflow_class is None:
            raise Exception("'{}' is not a valid workflow type.".format( parsed_args.workflow ))
        # This should work for both the IlastikShell and the HeadlessShell
        shell.createAndLoadNewProject(path, workflow_class)
    init_funcs.append(createNewProject)

# Enable test-case recording
if parsed_args.playback_script is not None:
    # Auto-exit on success?
    onfinish = None
    if parsed_args.exit_on_success:
        onfinish = QApplication.quit

    parsed_args.debug = True # Auto-enable debug mode
    def play_recording(shell):
        from ilastik.utility.gui.eventRecorder import EventPlayer
        player = EventPlayer(parsed_args.playback_speed)
        player.play_script(parsed_args.playback_script, onfinish)
    init_funcs.append( partial(play_recording) )

# Force debug mode
if parsed_args.debug:
    ilastik_config.set('ilastik', 'debug', 'true')
    
# Auto-exit on uncaught exceptions (useful for testing)
if parsed_args.exit_on_failure:
    old_excepthook = sys.excepthook
    def print_exc_and_exit(*args):
        old_excepthook(*args)
        sys.stderr.write("Exiting early due to an unhandled exception.  See error output above.\n")
        QApplication.exit(1)
    sys.excepthook = print_exc_and_exit
    install_thread_excepthook()
# Show uncaught exceptions to the user (default behavior)
elif not ilastik_config.getboolean('ilastik', 'debug') and not parsed_args.headless:
    old_excepthook = sys.excepthook
    def exception_dialog(*args):
        old_excepthook(*args)
        try:
            from ilastik.shell.gui.startShellGui import shell
            shell.postErrorMessage(args[0].__name__, args[1].message)
        except:
            pass
    sys.excepthook = exception_dialog
    install_thread_excepthook()

if ilastik_config.getboolean("ilastik", "debug"):
    logger.info("Starting ilastik in debug mode.")

# Headless launch
if parsed_args.headless:
    from ilastik.shell.headless.headlessShell import HeadlessShell
    shell = HeadlessShell( workflow_cmdline_args )
    for f in init_funcs:
        f(shell)
# Normal launch
else:
    from ilastik.shell.gui.startShellGui import startShellGui
    sys.exit(startShellGui(workflow_cmdline_args, parsed_args.start_recording, *init_funcs))


