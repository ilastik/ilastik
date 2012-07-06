import logging.config
import loggingHelpers

default_log_config = {
    "version": 1,
    #"incremental" : False,
    #"disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "location": {
            "format": "%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s"
        },
        "simple": {
            "format": "%(levelname)s %(message)s"
        },
    },
    "handlers": {
        "console":{
            "level":"DEBUG",
            #"class":"logging.StreamHandler",
            "class":"ilastik_logging.loggingHelpers.StdOutStreamHandler",
            "formatter": "location"
        },
        "console_warn":{
            "level":"WARN",
            "class":"logging.StreamHandler", # Defaults to sys.stderr
            "formatter":"verbose"
        },
    },
    "root": {
        "handlers": ["console", "console_warn"],
        "level": "INFO",
    },
    "loggers": {
        # When copying to a json file, remember to remove comments and change True/False to true/false
        "lazyflow":                             {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "lazyflow.graph":                       {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "lazyflow.graph.Slot":                  {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "lazyflow.operators":                   {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "lazyflow.operators.obsolete.vigraOperators":         { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "lazyflow.operators.obsolete.classifierOperators":    { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "volumina":                             {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "applets":                              {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "ilastikshell":                         {  "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        # Python doesn't provide a trace log level, so we use a workaround.
        # By convention, trace loggers have the same hierarchy as the regular loggers, but are prefixed with 'TRACE' and always emite DEBUG messages
        # To enable trace messages, change one or more of these to use level DEBUG
        "TRACE":                                                        { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.graph.Slot":                                    { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.graph.Operator":                                { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.graph.OperatorWrapper":                         { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.operators.obsolete":                            { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.operators.obsolete.operators":                  { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.operators.obsolete.generic":                    { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.operators.obsolete.classifierOperators":        { "level":"INFO", "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.operators.obsolete.operators.OpArrayCache":     { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.lazyflow.operators.obsolete.valueProviders.OpValueCache":{ "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.applets":                                                { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.ilastikshell":                                           { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.volumina":                                               { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False },
        "TRACE.volumina.imageScene2D":                                  { "level":"INFO",  "handlers":["console","console_warn"], "propagate": False }
    }
}

def init():
    # Start with the default
    logging.config.dictConfig(default_log_config)
    
    # Update from the user's customizations
    loggingHelpers.updateFromConfigFile()
    