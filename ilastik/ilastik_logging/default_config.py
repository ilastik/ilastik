import os
import logging.config
import warnings
import loggingHelpers

def get_default_config(prefix=""):
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
                #"class":"logging.StreamHandler",
                "class":"ilastik.ilastik_logging.loggingHelpers.StdOutStreamHandler",
                "formatter": "location",
                "filters":["no_warn"]
            },
            "console_timestamp":{
                "level":"DEBUG",
                #"class":"logging.StreamHandler",
                "class":"ilastik.ilastik_logging.loggingHelpers.StdOutStreamHandler",
                "formatter": "timestamped",
                "filters":["no_warn"]
            },
            "console_warn":{
                "level":"WARN",
                "class":"logging.StreamHandler", # Defaults to sys.stderr
                "formatter":"verbose"
            },
            "console_warning_module":{
                "level":"WARN",
                "class":"logging.StreamHandler", # Defaults to sys.stderr
                "formatter":"simple"
            },
            "console_trace":{
                "level":"DEBUG",
                #"class":"logging.StreamHandler",
                "class":"ilastik.ilastik_logging.loggingHelpers.StdOutStreamHandler",
                "formatter": "verbose"
            },
        },
        "root": {
            "handlers": ["console", "console_warn"],
            "level": "INFO",
        },
        "loggers": {
            # This logger captures warnings module warnings
            "py.warnings":                             {  "level":"WARN", "handlers":["console_warning_module"], "propagate": False },
    
            # When copying to a json file, remember to remove comments and change True/False to true/false
            "__main__":                                                         { "level":"INFO" },
            "lazyflow":                                                         { "level":"INFO" },
            "lazyflow.graph":                                                   { "level":"INFO" },
            "lazyflow.graph.Slot":                                              { "level":"INFO" },
            "lazyflow.operators":                                               { "level":"INFO" },
            "lazyflow.operators.ioOperators":                                   { "level":"INFO" },
            "lazyflow.operators.ioOperators.opRESTfulVolumeReader":             { "level":"INFO" },
            "lazyflow.operators.obsolete.operators.OpArrayCache":               { "level":"INFO" },
            "lazyflow.operators.obsolete.operators.ArrayCacheMemoryMgr":        { "level":"INFO" },
            "lazyflow.operators.obsolete.vigraOperators":                       { "level":"INFO" },
            "lazyflow.operators.obsolete.vigraOperators.OpH5WriterBigDataset":  { "level":"INFO" },
            "lazyflow.operators.obsolete.classifierOperators":                  { "level":"INFO" },
            "lazyflow.utility.io.RESTfulVolume":                                           { "level":"INFO" },
            "ilastik":                                                          { "level":"INFO" },
            "ilastik.clusterOps":                                               { "level":"INFO" },
            "ilastik.applets":                                                  { "level":"INFO" },
            "ilastik.applets.pixelClassification":                              { "level":"INFO" },
            "ilastik.shell":                                                    { "level":"INFO" },
            "ilastik.widgets":                                                  { "level":"INFO" },
            "volumina":                                                         { "level":"INFO" },
            "volumina.imageScene2D":                                            { "level":"INFO" },
            # Python doesn't provide a trace log level, so we use a workaround.
            # By convention, trace loggers have the same hierarchy as the regular loggers, but are prefixed with 'TRACE' and always emit DEBUG messages
            # To enable trace messages, change one or more of these to use level DEBUG
            "TRACE": { "level":"INFO", "handlers":["console_trace","console_warn"] },
            "TRACE.lazyflow.graph.Slot":                                        { "level":"INFO" },
            "TRACE.lazyflow.graph.Operator":                                    { "level":"INFO" },
            "TRACE.lazyflow.graph.OperatorWrapper":                             { "level":"INFO" },
            "TRACE.lazyflow.operators.ioOperators":                             { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete":                                { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete.operators":                      { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete.generic":                        { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete.classifierOperators":            { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete.operators.OpArrayCache":         { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete.operators.ArrayCacheMemoryMgr":  { "level":"INFO" },
            "TRACE.lazyflow.operators.obsolete.valueProviders.OpValueCache":    { "level":"INFO" },
            "TRACE.ilastik.clusterOps":                                         { "level":"INFO" },
            "TRACE.ilastik.applets":                                            { "level":"INFO" },
            "TRACE.ilastik.shell":                                              { "level":"INFO" },
            "TRACE.volumina":                                                   { "level":"INFO" },
            "TRACE.volumina.imageScene2D":                                      { "level":"INFO" }
        }
    }
    return default_log_config

def init(format_prefix=""):
    # Start with the default
    logging.config.dictConfig( get_default_config( format_prefix ) )
    
    # Update from the user's customizations
    loggingHelpers.updateFromConfigFile()
    
    # Capture warnings from the warnings module
    logging.captureWarnings(True)
    
    # Warnings module warnings are shown only once
    warnings.filterwarnings("once")

    # Don't warn about pending deprecations (PyQt generates some of these)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    
    # Custom format for warnings
    def simple_warning_format(message, category, filename, lineno, line=None):
        filename = os.path.split(filename)[1]
        return filename + "(" + str(lineno) + "): " + category.__name__ + ": " + message[0]

    warnings.formatwarning = simple_warning_format
    
