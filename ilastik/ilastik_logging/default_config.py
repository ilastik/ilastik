###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################
import platformdirs
import os
import re
import logging.config
import warnings

from datetime import datetime
from typing import Optional
from pathlib import Path
from . import loggingHelpers
from ilastik.config import cfg as ilastik_config

SESSION_FILEHANDLER_NAME = "session_file"
SESSION_LOGFILE_NAME = "log_%Y%m%d_%H%M%S.txt"
SESSION_LOGFILE_NAME_PATTERN = re.compile(r"^log_\d{8}_\d{6}\.txt$")  # For deleting old ones, must correspond to _NAME
SESSION_LOGFILE_PATH = os.path.join(
    platformdirs.user_log_dir(appname="ilastik", appauthor=False), datetime.now().strftime(SESSION_LOGFILE_NAME)
)
KEEP_SESSION_LOGS = 10
DEFAULT_FILEHANDLER_NAME = "rotating_file"
DEFAULT_LOG_NAME = "log.txt"
DEFAULT_LOGFILE_PATH = os.path.join(platformdirs.user_log_dir(appname="ilastik", appauthor=False), DEFAULT_LOG_NAME)


class OutputMode(object):
    CONSOLE = 0
    LOGFILE = 1
    BOTH = 2
    LOGFILE_WITH_CONSOLE_ERRORS = 3


def get_logfile_path() -> Optional[str]:
    root_handlers = logging.getLogger().handlers
    file_handlers = [h for h in root_handlers if isinstance(h, logging.FileHandler)]
    for handler in file_handlers:
        if handler.name == DEFAULT_FILEHANDLER_NAME:
            return handler.baseFilename
    if file_handlers:
        return file_handlers[0].baseFilename
    return None


def get_session_logfile_path() -> Optional[str]:
    root_handlers = logging.getLogger().handlers
    for handler in root_handlers:
        if isinstance(handler, logging.FileHandler) and handler.name == SESSION_FILEHANDLER_NAME:
            return handler.baseFilename
    return None


def _delete_old_session_logs(*, log_dir: Path):
    """Delete all but the last n=KEEP_SESSION_LOGS log files in log_dir."""
    if not log_dir.exists():
        return
    log_files = sorted(
        [child for child in log_dir.iterdir() if re.match(SESSION_LOGFILE_NAME_PATTERN, child.name)], reverse=True
    )
    for log_file in log_files[KEEP_SESSION_LOGS:]:
        log_file.unlink()


def get_default_config(
    prefix="", output_mode=OutputMode.LOGFILE_WITH_CONSOLE_ERRORS, logfile_path=DEFAULT_LOGFILE_PATH
):
    root_log_level = "INFO"

    if ilastik_config.getboolean("ilastik", "debug"):
        root_log_level = "DEBUG"

    if output_mode == OutputMode.CONSOLE:
        root_handlers = ["console", "console_warn"]
        warnings_module_handlers = ["console_warnings_module"]

    if output_mode == OutputMode.LOGFILE:
        root_handlers = [DEFAULT_FILEHANDLER_NAME]
        warnings_module_handlers = [DEFAULT_FILEHANDLER_NAME]
        if logfile_path == DEFAULT_LOGFILE_PATH:
            root_handlers.append(SESSION_FILEHANDLER_NAME)
            warnings_module_handlers.append(SESSION_FILEHANDLER_NAME)

    if output_mode == OutputMode.BOTH:
        root_handlers = ["console", "console_warn", DEFAULT_FILEHANDLER_NAME]
        warnings_module_handlers = ["console_warnings_module", DEFAULT_FILEHANDLER_NAME]
        if logfile_path == DEFAULT_LOGFILE_PATH:
            root_handlers.append(SESSION_FILEHANDLER_NAME)
            warnings_module_handlers.append(SESSION_FILEHANDLER_NAME)

    if output_mode == OutputMode.LOGFILE_WITH_CONSOLE_ERRORS:
        root_handlers = [DEFAULT_FILEHANDLER_NAME, "console_errors_only"]
        warnings_module_handlers = [DEFAULT_FILEHANDLER_NAME]
        if logfile_path == DEFAULT_LOGFILE_PATH:
            root_handlers.append(SESSION_FILEHANDLER_NAME)
            warnings_module_handlers.append(SESSION_FILEHANDLER_NAME)

    default_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{}%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s".format(prefix)
            },
            "location": {"format": "{}%(levelname)s %(name)s: %(message)s".format(prefix)},
            "timestamped": {"format": "{}%(levelname)s %(name)s: [%(asctime)s] %(message)s".format(prefix)},
            "simple": {"format": "{}%(levelname)s %(message)s".format(prefix)},
        },
        "filters": {"no_warn": {"()": "ilastik.ilastik_logging.loggingHelpers.NoWarnFilter"}},
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "location",
                "filters": ["no_warn"],  # This handler does NOT show warnings (see below)
            },
            "console_timestamp": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "timestamped",
                "filters": ["no_warn"],  # Does not show warnings
            },
            "console_warn": {
                "level": "WARN",  # Shows ONLY warnings and errors, on stderr
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "verbose",
            },
            "console_errors_only": {
                "level": "ERROR",  # Shows ONLY errors, on stderr
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "verbose",
            },
            "console_warnings_module": {
                "level": "WARN",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "simple",
            },
            "console_trace": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "verbose",
            },
            DEFAULT_FILEHANDLER_NAME: {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logfile_path,
                "maxBytes": 50e6,  # 20 MB
                "backupCount": 5,
                "formatter": "verbose",
                "encoding": "utf-8",
            },
            SESSION_FILEHANDLER_NAME: {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": SESSION_LOGFILE_PATH,
                "maxBytes": 1048576,  # 1 MiB
                "backupCount": 1,
                "formatter": "verbose",
                "encoding": "utf-8",
            },
        },
        "root": {"handlers": root_handlers, "level": root_log_level},
        "loggers": {
            # This logger captures warnings module warnings
            "py.warnings": {"level": "WARN", "handlers": warnings_module_handlers, "propagate": False},
            "PyQt5": {"level": "INFO"},
            "requests": {"level": "WARN"},  # Lots of messages at INFO
            "botocore.httpchecksum": {"level": "WARN"},
            "wsdt": {"level": "INFO"},
            "OpenGL": {"level": "INFO"},
            "yapsy": {"level": "INFO"},
            # Loglevels for our own modules (ilastik, lazyflow, volumina) are in ./logging_config.json.
        },
    }
    return default_log_config


_LOGGING_CONFIGURED = False


def init(format_prefix="", output_mode=OutputMode.LOGFILE_WITH_CONSOLE_ERRORS, logfile_path=DEFAULT_LOGFILE_PATH):
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        warnings.warn("logging has been already initialized; skipping further initialization calls", RuntimeWarning)
        return

    if logfile_path == "/dev/null":
        assert output_mode != OutputMode.LOGFILE, "Must enable a logging mode."
        output_mode = OutputMode.CONSOLE

    if output_mode != OutputMode.CONSOLE:
        log_dir = Path(logfile_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        _delete_old_session_logs(log_dir=log_dir)

    # Preserve pre-existing handlers
    original_root_handlers = list(logging.getLogger().handlers)

    # Start with the default
    default_config = get_default_config(format_prefix, output_mode, logfile_path)
    logging.config.dictConfig(default_config)

    # Preserve pre-existing handlers
    for handler in original_root_handlers:
        logging.getLogger().addHandler(handler)

    # Update from the user's customizations
    loggingHelpers.updateFromConfigFile()

    # Capture warnings from the warnings module
    logging.captureWarnings(True)

    # Don't warn about pending deprecations (PyQt generates some of these)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

    # Don't warn about duplicate python bindings for opengm
    # (We import opengm twice, as 'opengm' 'opengm_with_cplex'.)
    warnings.filterwarnings("ignore", message=".*to-Python converter for .*opengm.*", category=RuntimeWarning)

    # Hide all other python converter warnings unless we're in debug mode.
    if not ilastik_config.getboolean("ilastik", "debug"):
        warnings.filterwarnings(
            "ignore", message=".*to-Python converter for .*second conversion method ignored.*", category=RuntimeWarning
        )

    # Custom format for warnings
    def simple_warning_format(message, category, filename, lineno, line=None):
        filename = os.path.split(filename)[1]
        return f"{filename}:({lineno}): {category.__name__}: {message!r}"

    warnings.formatwarning = simple_warning_format

    _LOGGING_CONFIGURED = True
