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
            "__main__":                             {  "level":"DEBUG", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow":                             {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow.graph":                       {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow.graph.Slot":                  {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow.operators":                   {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow.operators.ioOperators":       {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow.operators.obsolete.vigraOperators":         { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "lazyflow.operators.obsolete.classifierOperators":    { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "ilastik":                              {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "ilastik.clusterOps":                   {  "level":"DEBUG", "handlers":["console","console_warn"], "propagate": False },
            "ilastik.applets":                      {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "ilastik.applets.pixelClassification":  {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "ilastik.shell":                        {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "ilastik.widgets":                      {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            "volumina":                             {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
            # Python doesn't provide a trace log level, so we use a workaround.
            # By convention, trace loggers have the same hierarchy as the regular loggers, but are prefixed with 'TRACE' and always emite DEBUG messages
            # To enable trace messages, change one or more of these to use level DEBUG
            "TRACE":                                                        { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.graph.Slot":                                    { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.graph.Operator":                                { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.graph.OperatorWrapper":                         { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.ioOperators":                         { "level":"INFO", "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.obsolete":                            { "level":"INFO", "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.obsolete.operators":                  { "level":"INFO", "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.obsolete.generic":                    { "level":"INFO", "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.obsolete.classifierOperators":        { "level":"INFO", "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.obsolete.operators.OpArrayCache":     { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.lazyflow.operators.obsolete.valueProviders.OpValueCache":{ "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.ilastik.applets":                                        { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.ilastik.shell":                                          { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.volumina":                                               { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False },
            "TRACE.volumina.imageScene2D":                                  { "level":"INFO",  "handlers":["console_trace","console_warn"], "propagate": False }
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
    
