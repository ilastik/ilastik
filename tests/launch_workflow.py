import sys
from functools import partial
from PyQt4.QtGui import QApplication

import threading
# This function was copied from: http://bugs.python.org/issue1230540
# It is necessary because sys.excepthook doesn't work for unhandled exceptions in other threads.
def install_thread_excepthook():
    """
    Workaround for sys.excepthook thread bug
    (https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470).
    Call once from __main__ before creating any threads.
    If using psyco, call psycho.cannotcompile(threading.Thread.run)
    since this replaces a new-style class method.
    """
    import sys
    run_old = threading.Thread.run
    def run(*args, **kwargs):
        try:
            run_old(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            sys.excepthook(*sys.exc_info())
    threading.Thread.run = run

#sys.argv.append( "/Users/bergs/MyProject.ilp" )

## EXAMPLE PLAYBACK TESTING ARGS
#sys.argv.append( "--playback_script=/Users/bergs/Documents/workspace/ilastik-meta/ilastik/tests/event_based/recording-20130450-2111.py" )
#sys.argv.append( "--playback_speed=3" )
#sys.argv.append( "--exit_on_failure" )
sys.argv.append( "--workflow=PixelClassificationWorkflow" )

import argparse
parser = argparse.ArgumentParser( description="Ilastik Pixel Classification Workflow" )
parser.add_argument('--playback_script', help='An event recording to play back after the main window has opened.', required=False)
parser.add_argument('--playback_speed', help='Speed to play the playback script.', default=0.5, type=float)
parser.add_argument('--exit_on_failure', help='Immediately call exit(1) if an unhandled exception occurs.', action='store_true', default=False)
parser.add_argument('--exit_on_success', help='Quit the app when the playback is complete.', action='store_true', default=False)
parser.add_argument('--project', nargs='?', help='A project file to open on startup.')
parser.add_argument('--workflow', help='A project file to open on startup.')

parsed_args = parser.parse_args()

init_funcs = []

# Start the GUI
if parsed_args.project is not None:
    def loadProject(shell):
        shell.openProjectFile(parsed_args.project)
    init_funcs.append( loadProject )

onfinish = None
if parsed_args.exit_on_success:
    onfinish = QApplication.quit

if parsed_args.playback_script is not None:
    from ilastik.utility.gui.eventRecorder import EventPlayer
    def play_recording(shell):
        player = EventPlayer(parsed_args.playback_speed)
        player.play_script(parsed_args.playback_script, onfinish)
    init_funcs.append( partial(play_recording) )

if parsed_args.exit_on_failure:
    old_excepthook = sys.excepthook
    def print_exc_and_exit(*args):
        old_excepthook(*args)
        sys.stderr.write("Exiting early due to an unhandled exception.  See error output above.\n")
        QApplication.exit(1)
    sys.excepthook = print_exc_and_exit
    install_thread_excepthook()

# Import all possible workflows so they are registered with the base class
import ilastik.workflows

# Ask the base class to give us the workflow type
from ilastik.workflow import Workflow
workflowClass = Workflow.getSubclass(parsed_args.workflow)

# Launch the GUI
from ilastik.shell.gui.startShellGui import startShellGui
sys.exit( startShellGui( workflowClass, *init_funcs ) )
