###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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

import os
import logging.config
import warnings

import appdirs
from . import loggingHelpers
from ilastik.config import cfg as ilastik_config

DEFAULT_LOGFILE_PATH = os.path.join(appdirs.user_log_dir(appname="ilastik", appauthor=False), "log.txt")


class OutputMode(object):
    CONSOLE = 0
    LOGFILE = 1
    BOTH = 2
    LOGFILE_WITH_CONSOLE_ERRORS = 3


def get_logfile_path():
    root_handlers = logging.getLogger().handlers
    for handler in root_handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return None


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
        root_handlers = ["rotating_file"]
        warnings_module_handlers = ["rotating_file"]

    if output_mode == OutputMode.BOTH:
        root_handlers = ["console", "console_warn", "rotating_file"]
        warnings_module_handlers = ["console_warnings_module", "rotating_file"]

    if output_mode == OutputMode.LOGFILE_WITH_CONSOLE_ERRORS:
        root_handlers = ["rotating_file", "console_errors_only"]
        warnings_module_handlers = ["rotating_file"]

    default_log_config = {
        "version": 1,
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
            "rotating_file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logfile_path,
                "maxBytes": 50e6,  # 20 MB
                "backupCount": 5,
                "formatter": "verbose",
            },
        },
        "root": {"handlers": root_handlers, "level": root_log_level},
        "loggers": {
            # This logger captures warnings module warnings
            "py.warnings": {"level": "WARN", "handlers": warnings_module_handlers, "propagate": False},
            "PyQt5": {"level": "INFO"},
            "requests": {"level": "WARN"},  # Lots of messages at INFO
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
        os.makedirs(os.path.dirname(DEFAULT_LOGFILE_PATH), exist_ok=True)

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
