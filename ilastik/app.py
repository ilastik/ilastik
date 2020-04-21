###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2020, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import argparse
import faulthandler
import logging
import os
import sys
from typing import List, Optional, Sequence, Tuple

import ilastik.config
from ilastik.config import cfg as ilastik_config
from ilastik.utility.commandLineProcessing import str2bool

logger = logging.getLogger(__name__)


def _argparser() -> argparse.ArgumentParser:
    """Create ArgumentParser for the main entry point."""
    ap = argparse.ArgumentParser(description="start an ilastik workflow")
    ap.add_argument("--headless", help="Don't start the ilastik gui.", action="store_true")
    ap.add_argument("--project", help="A project file to open on startup.")
    ap.add_argument(
        "--readonly",
        nargs="?",
        default=None,
        const="true",
        type=str2bool,
        help=(
            "Open all projects in read-only mode, to ensure you don't accidentally make changes. "
            "Per default projects are opened with read access in GUI mode, without read access in headless mode."
        ),
    )
    ap.add_argument(
        "--new_project", help="Create a new project with the specified name. Must also specify " "--workflow."
    )
    ap.add_argument("--workflow", help="When used with --new_project, specifies the workflow to use.")
    ap.add_argument(
        "--clean_paths", help="Remove ilastik-unrelated directories from PATH and PYTHONPATH.", action="store_true"
    )
    ap.add_argument("--redirect_output", help="A filepath to redirect stdout to")
    ap.add_argument("--debug", help="Start ilastik in debug mode.", action="store_true")
    ap.add_argument("--logfile", help="A filepath to dump all log messages to.")
    ap.add_argument("--process_name", help="A process name (used for logging purposes).")
    ap.add_argument("--configfile", help="A custom path to a user config file for expert ilastik settings.")
    ap.add_argument("--fullscreen", help="Show Window in fullscreen mode.", action="store_true")
    ap.add_argument(
        "--exit_on_failure", help="Immediately call exit(1) if an unhandled exception occurs.", action="store_true"
    )
    ap.add_argument("--hbp", help="Enable HBP-specific functionality.", action="store_true")
    return ap


def _ensure_compatible_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """If args are invalid, print an error message to stderr and exit."""

    if args.workflow is not None and args.new_project is None:
        parser.error("The --workflow argument may only be used with the " "--new_project argument.")

    if args.workflow is None and args.new_project is not None:
        parser.error(
            "No workflow specified. The --new_project argument must "
            "be used in conjunction with the --workflow argument."
        )

    if args.project is not None and args.new_project is not None:
        parser.error("The --project and --new_project settings cannot be used " "together. Choose one (or neither).")

    if args.headless and (args.fullscreen or args.exit_on_failure):
        parser.error("Some of the command-line options you provided are not " "supported in headless mode.")

    if args.headless and not args.project and not (args.new_project and args.workflow):
        parser.error(
            "You have to supply at least --project, or --new_project "
            "and workflow when invoking ilastik in headless mode."
        )


def parse_args(
    args: Optional[Sequence[str]] = None, namespace: Optional[argparse.Namespace] = None
) -> argparse.Namespace:
    """Parse and validate command-line arguments for :func:`main`.

    See Also:
        :meth:`argparse.ArgumentParser.parse_args`.
    """
    parser = _argparser()
    known = parser.parse_args(args, namespace)
    _ensure_compatible_args(parser, known)
    return known


def parse_known_args(
    args: Optional[Sequence[str]] = None, namespace: Optional[argparse.Namespace] = None
) -> Tuple[argparse.Namespace, List[str]]:
    """Parse and validate command-line arguments for :func:`main`.

    See Also:
        :meth:`argparse.ArgumentParser.parse_known_args`.
    """
    parser = _argparser()
    known, unknown = parser.parse_known_args(args, namespace)
    _ensure_compatible_args(parser, known)
    return known, unknown


def main(parsed_args, workflow_cmdline_args=[], init_logging=True):
    """
    init_logging: Skip logging config initialization by setting this to False.
                  (Useful when opening multiple projects in a Python script.)
    """
    this_path = os.path.dirname(__file__)
    ilastik_dir = os.path.abspath(os.path.join(this_path, "..%s.." % os.path.sep))
    _import_h5py_with_utf8_encoding()
    _update_debug_mode(parsed_args)
    _update_hbp_mode(parsed_args)

    # If necessary, redirect stdout BEFORE logging is initialized
    _redirect_output(parsed_args)

    if init_logging:
        _init_logging(parsed_args)  # Initialize logging before anything else

    _init_configfile(parsed_args)

    _init_threading_logging_monkeypatch()

    # Extra initialization functions.
    # These are called during app startup, but before the shell is created.
    preinit_funcs = []
    # Must be first (or at least before vigra).
    preinit_funcs.append(_import_opengm)

    lazyflow_config_fn = _prepare_lazyflow_config(parsed_args)
    if lazyflow_config_fn:
        preinit_funcs.append(lazyflow_config_fn)

    # More initialization functions.
    # These will be called AFTER the shell is created.
    # The shell is provided as a parameter to the function.
    postinit_funcs = []
    load_fn = _prepare_auto_open_project(parsed_args)
    if load_fn:
        postinit_funcs.append(load_fn)

    create_fn = _prepare_auto_create_new_project(parsed_args)
    if create_fn:
        postinit_funcs.append(create_fn)

    faulthandler.enable()
    _init_excepthooks(parsed_args)

    if ilastik_config.getboolean("ilastik", "debug"):
        message = 'Starting ilastik in debug mode from "%s".' % ilastik_dir
        logging.basicConfig(level=logging.DEBUG)
        logger.info(message)
        print(message)  # always print the startup message
    else:
        message = 'Starting ilastik from "%s".' % ilastik_dir
        logger.info(message)
        print(message)  # always print the startup message

    # Headless launch
    if parsed_args.headless:
        # Run pre-init
        for f in preinit_funcs:
            f()

        from ilastik.shell.headless.headlessShell import HeadlessShell

        shell = HeadlessShell(workflow_cmdline_args)

        # Run post-init
        for f in postinit_funcs:
            f(shell)
        return shell
    # Normal launch
    else:
        from ilastik.shell.gui.startShellGui import startShellGui

        sys.exit(startShellGui(workflow_cmdline_args, preinit_funcs, postinit_funcs))


def _import_h5py_with_utf8_encoding():
    # This is a monkeypatch for windows in order to support utf-8 filenames.
    # Note: This works only with the patched version of hdf5-1.10.1 (forked at
    # ilastik)
    import h5py

    h5py._hl.compat.WINDOWS_ENCODING = "utf-8"


def _init_configfile(parsed_args):
    # If the user provided a custom config path to use instead of the default
    # .ilastikrc, re-initialize the config module for it.
    if parsed_args.configfile:
        ilastik.config.init_ilastik_config(parsed_args.configfile)


stdout_redirect_file = None
old_stdout = None
old_stderr = None


def _redirect_output(parsed_args):
    if parsed_args.redirect_output:
        global old_stdout, old_stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        global stdout_redirect_file
        stdout_redirect_file = open(parsed_args.redirect_output, "a")
        sys.stdout = stdout_redirect_file
        sys.stderr = stdout_redirect_file

        # Close the file when we exit...
        import atexit

        atexit.register(stdout_redirect_file.close)


def _update_debug_mode(parsed_args):
    # Force debug mode if any of these flags are active.
    if parsed_args.debug or ilastik_config.getboolean("ilastik", "debug"):
        # There are two places that debug mode can be checked.
        # Make sure both are set.
        ilastik_config.set("ilastik", "debug", "true")
        parsed_args.debug = True


def _update_hbp_mode(parsed_args):
    """enable HBP-specific functionality"""
    if parsed_args.hbp:
        ilastik_config.set("ilastik", "hbp", "true")


def _init_logging(parsed_args):
    from ilastik.ilastik_logging import default_config, startUpdateInterval, DEFAULT_LOGFILE_PATH

    logfile_path = parsed_args.logfile or DEFAULT_LOGFILE_PATH
    process_name = ""
    if parsed_args.process_name:
        process_name = parsed_args.process_name + " "

    if ilastik_config.getboolean("ilastik", "debug") or parsed_args.headless:
        default_config.init(process_name, default_config.OutputMode.BOTH, logfile_path)
    else:
        default_config.init(process_name, default_config.OutputMode.LOGFILE_WITH_CONSOLE_ERRORS, logfile_path)
        startUpdateInterval(10)  # 10 second periodic refresh

    if parsed_args.redirect_output:
        logger.info("All console output is being redirected to: {}".format(parsed_args.redirect_output))


def _init_threading_logging_monkeypatch():
    # Monkey-patch thread starts if this special logger is active
    thread_start_logger = logging.getLogger("thread_start")
    if thread_start_logger.isEnabledFor(logging.DEBUG):
        import threading

        ordinary_start = threading.Thread.start

        def logged_start(self):
            ordinary_start(self)
            thread_start_logger.debug(f"Started thread: id={self.ident:x}, name={self.name}")

        threading.Thread.start = logged_start


def _import_opengm():
    # Import opengm first if possible, to make sure it is included before
    # vigra.
    # Otherwise the import fails and we will not get access to GraphCut
    # thresholding
    try:
        import opengm  # noqa
    except ImportError:
        pass


def _prepare_lazyflow_config(parsed_args):
    # Check environment variable settings.
    n_threads = os.getenv("LAZYFLOW_THREADS", None)
    total_ram_mb = os.getenv("LAZYFLOW_TOTAL_RAM_MB", None)
    status_interval_secs = int(os.getenv("LAZYFLOW_STATUS_MONITOR_SECONDS", "0"))

    # Convert str -> int
    if n_threads is not None:
        n_threads = int(n_threads)
    total_ram_mb = total_ram_mb and int(total_ram_mb)

    # If not in env, check config file.
    if n_threads is None:
        n_threads = ilastik_config.getint("lazyflow", "threads")
        if n_threads == -1:
            n_threads = None
    total_ram_mb = total_ram_mb or ilastik_config.getint("lazyflow", "total_ram_mb")

    # Note that n_threads == 0 is valid and useful for debugging.
    if (n_threads is not None) or total_ram_mb or status_interval_secs:

        def _configure_lazyflow_settings():
            import lazyflow
            import lazyflow.request
            from lazyflow.utility import Memory
            from lazyflow.operators import cacheMemoryManager

            if status_interval_secs:
                memory_logger = logging.getLogger("lazyflow.operators.cacheMemoryManager")
                memory_logger.setLevel(logging.DEBUG)
                cacheMemoryManager.setRefreshInterval(status_interval_secs)

            if n_threads is not None:
                logger.info(f"Resetting lazyflow thread pool with {n_threads} " "threads.")
                lazyflow.request.Request.reset_thread_pool(n_threads)
            if total_ram_mb > 0:
                if total_ram_mb < 500:
                    raise Exception(
                        "In your current configuration, RAM is "
                        f"limited to {total_ram_mb} MB. Remember "
                        "to specify RAM in MB, not GB."
                    )
                ram = total_ram_mb * 1024 ** 2
                fmt = Memory.format(ram)
                logger.info("Configuring lazyflow RAM limit to {}".format(fmt))
                Memory.setAvailableRam(ram)

        return _configure_lazyflow_settings
    return None


def _prepare_auto_open_project(parsed_args):
    if parsed_args.project is None:
        return None

    from lazyflow.utility.pathHelpers import PathComponents, isUrl

    # Make sure project file exists.
    if not isUrl(parsed_args.project) and not os.path.exists(parsed_args.project):
        raise RuntimeError("Project file '" + parsed_args.project + "' does not exist.")

    parsed_args.project = os.path.expanduser(parsed_args.project)
    # convert path to convenient format
    path = PathComponents(parsed_args.project).totalPath()

    # readonly
    if parsed_args.readonly is None:
        parsed_args.readonly = parsed_args.headless

    def loadProject(shell):
        # This should work for both the IlastikShell and the HeadlessShell
        shell.openProjectFile(path, parsed_args.readonly)

    return loadProject


def _prepare_auto_create_new_project(parsed_args):
    if parsed_args.new_project is None:
        return None
    parsed_args.new_project = os.path.expanduser(parsed_args.new_project)
    # convert path to convenient format
    from lazyflow.utility.pathHelpers import PathComponents

    path = PathComponents(parsed_args.new_project).totalPath()

    def createNewProject(shell):
        import ilastik.workflows  # noqa
        from ilastik.workflow import getWorkflowFromName

        workflow_class = getWorkflowFromName(parsed_args.workflow)
        if workflow_class is None:
            raise Exception("'{parsed_args.workflow}' is not a valid workflow type.")
        # This should work for both the IlastikShell and the HeadlessShell
        shell.createAndLoadNewProject(path, workflow_class)

    return createNewProject


def _init_excepthooks(parsed_args):
    # Initialize global exception handling behavior
    import ilastik.excepthooks

    if parsed_args.exit_on_failure:
        # Auto-exit on uncaught exceptions (useful for testing)
        ilastik.excepthooks.init_early_exit_excepthook()
    elif not ilastik_config.getboolean("ilastik", "debug") and not parsed_args.headless:
        # Show most uncaught exceptions to the user (default behavior)
        ilastik.excepthooks.init_user_mode_excepthook()
    else:
        # Log all exceptions as errors
        ilastik.excepthooks.init_developer_mode_excepthook()
