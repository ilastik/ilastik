#!/usr/bin/env python

# Standard
import sys
import argparse
import threading
import logging
from functools import partial

# Third-party
from PyQt4.QtGui import QApplication
from ilastik.config import cfg as ilastik_config

# Initialize logging before anything else
from ilastik.ilastik_logging import default_config
default_config.init()

# Ilastik
from ilastik.utility.pathHelpers import PathComponents
from ilastik.utility.gui.eventRecorder import EventPlayer
from ilastik.shell.gui.startShellGui import startShellGui

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
parser.add_argument('--project', nargs='?', help='A project file to open on startup.')
parser.add_argument('--debug', help='Start ilastik in debug mode.', action='store_true', default=False)

# Example:
# python ilastik.py --playback_speed=2.0 --exit_on_failure --exit_on_success --debug --playback_script=my_recording.py

parsed_args = parser.parse_args()
init_funcs = []

if parsed_args.start_recording:
    assert not parsed_args.playback_script is False, "Can't record and play back at the same time!  Choose one or the other"
    parsed_args.debug = True # Auto-enable debug mode
    def startRecording(shell):
        shell._recorderGui.openInPausedState()
    init_funcs.append(startRecording)

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
    parsed_args.debug = True # Auto-enable debug mode
    def play_recording(shell):
        player = EventPlayer(parsed_args.playback_speed)
        player.play_script(parsed_args.playback_script, onfinish)
    init_funcs.append( partial(play_recording) )

if parsed_args.debug:
    ilastik_config.set('ilastik', 'debug', 'true')
    
if parsed_args.exit_on_failure:
    old_excepthook = sys.excepthook
    def print_exc_and_exit(*args):
        old_excepthook(*args)
        sys.stderr.write("Exiting early due to an unhandled exception.  See error output above.\n")
        QApplication.exit(1)
    sys.excepthook = print_exc_and_exit
    install_thread_excepthook()
elif not ilastik_config.getboolean('ilastik', 'debug'):
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

sys.exit(startShellGui(None,*init_funcs))

    
