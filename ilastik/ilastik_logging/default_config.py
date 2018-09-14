from __future__ import absolute_import
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
#		   http://ilastik.org/license.html
###############################################################################
import os
import logging.config
import warnings
from . import loggingHelpers
from ilastik.config import cfg as ilastik_config

DEFAULT_LOGFILE_PATH = os.path.expanduser("~/ilastik_log.txt")

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
    
def get_default_config( prefix="", 
                        output_mode=OutputMode.LOGFILE_WITH_CONSOLE_ERRORS, 
                        logfile_path=DEFAULT_LOGFILE_PATH):

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
        #"incremental" : False,
        #"disable_existing_loggers": True,
        "formatters": {
            "verbose": {
                "format": "{}%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s".format(prefix)
            },
            "location": {
                #"format": "%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s"
                "format": "{}%(levelname)s %(name)s: %(message)s".format(prefix)
            },
            "timestamped": {
                #"format": "%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s"
                "format": "{}%(levelname)s %(name)s: [%(asctime)s] %(message)s".format(prefix)
            },
            "simple": {
                "format": "{}%(levelname)s %(message)s".format(prefix)
            },
        },
        "filters" : {
            "no_warn" : {
                "()":"ilastik.ilastik_logging.loggingHelpers.NoWarnFilter"
            }
        },
        "handlers": {
            "console":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stdout",
                "formatter": "location",
                "filters":["no_warn"] # This handler does NOT show warnings (see below)
            },
            "console_timestamp":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stdout",
                "formatter": "timestamped",
                "filters":["no_warn"] # Does not show warnings
            },
            "console_warn":{
                "level":"WARN", # Shows ONLY warnings and errors, on stderr
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stderr",
                "formatter":"verbose"
            },
            "console_errors_only":{
                "level":"ERROR", # Shows ONLY errors, on stderr
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stderr",
                "formatter":"verbose"
            },
            "console_warnings_module":{
                "level":"WARN",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stderr",
                "formatter":"simple"
            },
            "console_trace":{
                "level":"DEBUG",
                "class":"logging.StreamHandler",
                "stream":"ext://sys.stdout",
                "formatter": "verbose"
            },
            "rotating_file":{
                "level":"DEBUG",
                "class":"logging.handlers.RotatingFileHandler",
                "filename" : logfile_path,
                "maxBytes":20e6, # 20 MB
                "backupCount":5,
                "formatter":"verbose",
            },
        },
        "root": {
            "handlers": root_handlers,
            "level": "INFO",
        },
        "loggers": {
            # This logger captures warnings module warnings
            "py.warnings":                             {  "level":"WARN", "handlers":warnings_module_handlers, "propagate": False },

            "PyQt5": {"level":"INFO"},
            
            # The requests module spits out a lot of INFO messages by default.
            "requests": {"level":"WARN"},

            "wsdt": { "level": "INFO" },
    
            # When copying to a json file, remember to remove comments and change True/False to true/false
            "__main__":                                                 { "level":"INFO" },
            "ilastik_main":                                             { "level":"INFO" },
            "thread_start":                                             { "level":"INFO" },
            "lazyflow":                                                 { "level":"INFO" },
            "lazyflow.request":                                         { "level":"INFO" },
            "lazyflow.request.RequestLock":                             { "level":"INFO" },
            "lazyflow.request.SimpleRequestCondition":                  { "level":"INFO" },
            "lazyflow.graph":                                           { "level":"INFO" },
            "lazyflow.graph.Slot":                                      { "level":"INFO" },
            "lazyflow.operators":                                       { "level":"INFO" },
            "lazyflow.classifiers":                                     { "level":"INFO" },
            "lazyflow.operators.ioOperators":                           { "level":"INFO" },
            "lazyflow.operators.ioOperators.opRESTfulVolumeReader":     { "level":"INFO" },
            "lazyflow.operators.cacheMemoryManager.CacheMemoryManager": { "level":"INFO" },
            "lazyflow.operators.filterOperators":                       { "level":"INFO" },
            "lazyflow.operators.ioOperators.ioOperators.OpH5WriterBigDataset":   { "level":"INFO" },
            "lazyflow.operators.classifierOperators":                   { "level":"INFO" },
            "lazyflow.operators.opCompressedCache":                     { "level":"INFO" },
            "lazyflow.operators.opRelabelConsecutive":                  { "level":"INFO" },
            "lazyflow.utility.io_util.RESTfulVolume":                        { "level":"INFO" },
            "lazyflow.utility.io_util.tiledVolume":                          { "level":"INFO" },
            "lazyflow.operators.opFeatureMatrixCache":                  { "level":"INFO" },
            "lazyflow.operators.opConcatenateFeatureMatrices":          { "level":"INFO" },
            "lazyflow.utility.roiRequestBatch":                         { "level":"INFO" },
            "lazyflow.utility.bigRequestStreamer":                      { "level":"INFO" },
            "ilastik":                                                  { "level":"INFO" },
            "ilastik.clusterOps":                                       { "level":"INFO" },
            "ilastik.applets":                                          { "level":"INFO" },
            "ilastik.applets.base.appletSerializer":                    { "level":"INFO" },
            "ilastik.applets.dataSelection":                            { "level":"INFO" },
            "ilastik.applets.featureSelection":                         { "level":"INFO" },
            "ilastik.applets.pixelClassification":                      { "level":"INFO" },
            "ilastik.applets.thresholdTwoLevels":                       { "level":"INFO" },
            "ilastik.applets.thresholdTwoLevels.ipht":                  { "level":"INFO" },
            "ilastik.applets.objectExtraction":                         { "level":"INFO" },
            "ilastik.applets.blockwiseObjectClassification":            { "level":"INFO" },
            "ilastik.applets.tracking.conservation":                    { "level":"INFO" },
            "ilastik.shell":                                            { "level":"INFO" },
            "ilastik.shell.projectManager":                             { "level":"INFO" },
            "ilastik.shell.gui.ipcManager":                             { "level":"INFO" },
            "ilastik.workflows":                                        { "level":"INFO" },
            "ilastik.widgets":                                          { "level":"INFO" },
            "ilastik.utility":                                          { "level":"INFO" },
            "ilastik.utility.exportingOperator":                        { "level":"INFO" },
            "ilastik.utility.exportFile":                               { "level":"INFO" },
            "workflows":                                                { "level":"INFO" },
            "volumina":                                                 { "level":"INFO" },
            "volumina.pixelpipeline":                                   { "level":"INFO" },
            "volumina.imageScene2D":                                    { "level":"INFO" },
            "volumina.utility.shortcutManager":                         { "level":"INFO" },
            # Python doesn't provide a trace log level, so we use a workaround.
            # By convention, trace loggers have the same hierarchy as the regular loggers, but are prefixed with 'TRACE' and always emit DEBUG messages
            # To enable trace messages, change one or more of these to use level DEBUG
            "TRACE": { "level":"INFO", "handlers":["console_trace","console_warn"] },
            "TRACE.lazyflow.graph.Slot":                                { "level":"INFO" },
            "TRACE.lazyflow.graph.Operator":                            { "level":"INFO" },
            "TRACE.lazyflow.graph.OperatorWrapper":                     { "level":"INFO" },
            "TRACE.lazyflow.operators.ioOperators":                     { "level":"INFO" },
            "TRACE.lazyflow.operators":                                 { "level":"INFO" },
            "TRACE.lazyflow.operators.operators":                       { "level":"INFO" },
            "TRACE.lazyflow.operators.generic":                         { "level":"INFO" },
            "TRACE.lazyflow.operators.classifierOperators":             { "level":"INFO" },
            "TRACE.lazyflow.operators.operators.ArrayCacheMemoryMgr":   { "level":"INFO" },
            "TRACE.lazyflow.operators.valueProviders.OpValueCache":     { "level":"INFO" },
            "TRACE.ilastik.clusterOps":                                 { "level":"INFO" },
            "TRACE.ilastik.applets":                                    { "level":"INFO" },
            "TRACE.ilastik.applets.blockwiseObjectClassification":      { "level":"INFO" },
            "TRACE.ilastik.shell":                                      { "level":"INFO" },
            "TRACE.volumina":                                           { "level":"INFO" },
            "TRACE.volumina.imageScene2D":                              { "level":"INFO" }
        }
    }
    return default_log_config

def init(format_prefix="", output_mode=OutputMode.LOGFILE_WITH_CONSOLE_ERRORS, logfile_path=DEFAULT_LOGFILE_PATH):
    if logfile_path == "/dev/null":
        assert output_mode != OutputMode.LOGFILE, "Must enable a logging mode."
        output_mode = OutputMode.CONSOLE

    # Preserve pre-existing handlers
    original_root_handlers = list(logging.getLogger().handlers)

    # Start with the default
    default_config = get_default_config( format_prefix, output_mode, logfile_path )
    logging.config.dictConfig( default_config )

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
    warnings.filterwarnings("ignore", message='.*to-Python converter for .*opengm.*', category=RuntimeWarning)

    # Hide all other python converter warnings unless we're in debug mode.
    if not ilastik_config.getboolean("ilastik", "debug"):
        warnings.filterwarnings("ignore", message='.*to-Python converter for .*second conversion method ignored.*', category=RuntimeWarning)
        
    
    # Custom format for warnings
    def simple_warning_format(message, category, filename, lineno, line=None):
        filename = os.path.split(filename)[1]
        return filename + "(" + str(lineno) + "): " + category.__name__ + ": " + message.args[0]

    warnings.formatwarning = simple_warning_format
    
