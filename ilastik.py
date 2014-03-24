#!/usr/bin/env python

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers


# Standard
import sys
import argparse

from ilastik.config import cfg as ilastik_config
import ilastik.monkey_patches

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

# Special command-line control over default tmp dir
ilastik.monkey_patches.extend_arg_parser(parser)

# Examples:
# python ilastik.py --headless --project=MyProject.ilp --output_format=hdf5 raw_input.h5/volumes/data
# python ilastik.py --playback_speed=2.0 --exit_on_failure --exit_on_success --debug --playback_script=my_recording.py

parsed_args, workflow_cmdline_args = parser.parse_known_args()
init_funcs = []

# Force debug mode
if parsed_args.debug or parsed_args.start_recording or parsed_args.playback_script:
    ilastik_config.set('ilastik', 'debug', 'true')
    parsed_args.debug = True

# Initialize logging before anything else
from ilastik.ilastik_logging import default_config
if ilastik_config.getboolean('ilastik', 'debug'):
    default_config.init(output_mode=default_config.OutputMode.BOTH)
else:
    default_config.init(output_mode=default_config.OutputMode.LOGFILE_WITH_CONSOLE_ERRORS)
    ilastik.ilastik_logging.startUpdateInterval(10) # 10 second periodic refresh
import logging
logger = logging.getLogger(__name__)

# Monkey-patch thread starts if this special logger is active
thread_start_logger = logging.getLogger("thread_start")
if thread_start_logger.isEnabledFor(logging.DEBUG):
    import threading
    ordinary_start = threading.Thread.start
    def logged_start(self):
        ordinary_start(self)
        thread_start_logger.debug( "Started thread: id={:x}, name={}".format( self.ident, self.name ) )
    threading.Thread.start = logged_start

if parsed_args.start_recording or parsed_args.playback_script:
    # Disable the opengl widgets during recording and playback.
    # Somehow they can cause random segfaults if used during recording playback.
    import volumina
    volumina.NO3D = True

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
    from lazyflow.utility.pathHelpers import PathComponents
    path = PathComponents(parsed_args.project).totalPath()
    
    def loadProject(shell):
        # This should work for both the IlastikShell and the HeadlessShell
        shell.openProjectFile(path)
    init_funcs.append(loadProject)

# Auto-create new project
if parsed_args.new_project is not None:
    #convert path to convenient format
    from lazyflow.utility.pathHelpers import PathComponents
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

# Enable test-case recording?
eventcapture_mode = None
playback_args = {}
if parsed_args.start_recording:
    assert not parsed_args.playback_script is False, "Can't record and play back at the same time!  Choose one or the other"
    eventcapture_mode = 'record'
elif parsed_args.playback_script is not None:
    eventcapture_mode = 'playback'
    # See EventRecordingApp.create_app() for details
    playback_args['playback_script'] = parsed_args.playback_script
    playback_args['playback_speed'] = parsed_args.playback_speed
    # Auto-exit on success?
    if parsed_args.exit_on_success:
        playback_args['finish_callback'] = QApplication.quit        

# Initialize global exception handling behavior
import ilastik.excepthooks
if parsed_args.exit_on_failure:
    # Auto-exit on uncaught exceptions (useful for testing)
    ilastik.excepthooks.init_early_exit_excepthook()
elif not ilastik_config.getboolean('ilastik', 'debug') and not parsed_args.headless:
    # Show most uncaught exceptions to the user (default behavior)
    ilastik.excepthooks.init_user_mode_excepthook()
else:
    # Log all exceptions as errors
    ilastik.excepthooks.init_developer_mode_excepthook()

if ilastik_config.getboolean("ilastik", "debug"):
    logger.info("Starting ilastik in debug mode.")
    # Enable full stack trace printout in case of a segfault
    # (Requires the faulthandler module from PyPI)
    import faulthandler
    faulthandler.enable()
else:
    logger.info("Starting ilastik.")

# Headless launch
if parsed_args.headless:
    from ilastik.shell.headless.headlessShell import HeadlessShell
    shell = HeadlessShell( workflow_cmdline_args )
    for f in init_funcs:
        f(shell)
# Normal launch
else:
    from ilastik.shell.gui.startShellGui import startShellGui
    sys.exit(startShellGui(workflow_cmdline_args, eventcapture_mode, playback_args, *init_funcs))


