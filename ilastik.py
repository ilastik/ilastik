#!/usr/bin/env python

# Standard
import sys
import argparse
import threading
from functools import partial

# Third-party
from PyQt4.QtGui import QApplication

# Initialize logging before anything else
from ilastik.ilastik_logging import default_config
default_config.init()

# Ilastik
from ilastik.utility.pathHelpers import PathComponents
from ilastik.utility.gui.eventRecorder import EventPlayer
from ilastik.shell.gui.startShellGui import startShellGui

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
parser.add_argument('--playback_script', help='An event recording to play back after the main window has opened.', required=False)
parser.add_argument('--playback_speed', help='Speed to play the playback script.', default=0.5, type=float)
parser.add_argument('--exit_on_failure', help='Immediately call exit(1) if an unhandled exception occurs.', action='store_true', default=False)
parser.add_argument('--exit_on_success', help='Quit the app when the playback is complete.', action='store_true', default=False)
parser.add_argument('--project', nargs='?', help='A project file to open on startup.')

# Example:
# python ilastik.py --playback_speed=2.0 --exit_on_failure --exit_on_success --playback_script=my_recording.py

parsed_args = parser.parse_args()
init_funcs = []

if parsed_args.project is not None:    
    #convert path to convenient format
    path = PathComponents(parsed_args.project).totalPath()
    
    def loadProject(shell):
        shell.openProjectFile(path)
    init_funcs.append(loadProject)

onfinish = None
if parsed_args.exit_on_success:
    onfinish = QApplication.quit

if parsed_args.playback_script is not None:
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

sys.exit(startShellGui(None,*init_funcs))

    
