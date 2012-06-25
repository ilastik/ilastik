import logging
import logging.config
import sys

class StdOutStreamHandler(logging.StreamHandler):
    """
    Stream Handler that defaults to sys.stdout instead of sys.stderr.
    """
    def __init__(self):
        super( StdOutStreamHandler, self ).__init__(stream=sys.stdout)

default_log_config = {
    'version': 1,
    #'incremental' : False,
    #'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'location': {
            'format': '%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            #'class':'logging.StreamHandler',
            'class':'ilastik_logging_config.StdOutStreamHandler',
            'formatter': 'location'
        },
        'console_warn':{
            'level':'WARN',
            'class':'logging.StreamHandler', # Defaults to sys.stderr
            'formatter':'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        # Regular loggers
        'lazyflow': {
            'handlers':['console','console_warn'],
            'propagate': False,
            'level':'INFO',
        },
        'lazyflow.graph': {
            'handlers':['console', 'console_warn'],
            'propagate': False,
            'level':'INFO',
        },
        'lazyflow.graph.Slot': {
            'handlers':['console', 'console_warn'],
            'propagate': False,
            'level':'INFO',
        },
        'lazyflow.operators': {
            'handlers':['console', 'console_warn'],
            'propagate': False,
            'level':'INFO',
        },
        'volumina': {
            'handlers':['console', 'console_warn'],
            'propagate': False,
            'level':'INFO',
        },
        'applets': {
            'handlers':['console', 'console_warn'],
            'propagate': False,
            'level':'INFO',
        },
        # TRACE LOGGERS
        # The python logging module doesn't provide a separate trace logging level, so we use a workaround.
        # By convention, trace statements go to a special logger named with a TRACE prefix.
        # To see such trace statements, set these loggers to the DEBUG level.
        'TRACE': {
            'handlers':['console'],
            'propagate': False,
            'level':'INFO',
        },
        'TRACE.lazyflow.graph.Operator': {
            'handlers':['console'],
            'propagate': False,
            'level':'INFO',
        },
        'TRACE.lazyflow.graph.OperatorWrapper': {
            'handlers':['console'],
            'propagate': False,
            'level':'INFO',
        },
        'TRACE.applets': {
            'handlers':['console'],
            'propagate': False,
            'level':'INFO',
        },
    }
}

def init_default_config():
    logging.config.dictConfig(default_log_config)
