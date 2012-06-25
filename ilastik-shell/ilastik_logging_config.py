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
            'format': '%(levelname)s %(name)s:%(funcName)s:%(lineno)d %(message)s'
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
        # By convention, trace-level log statements are prefixed with 'TRACE' and are output at the DEBUG level.
        # To see trace statements, set this logger to DEBUG
        'TRACE': {
            'handlers':['console'],
            'propagate': False,
            'level':'DEBUG',
        },
        'lazyflow': {
            'handlers':['console','console_warn'],
            'propagate': False,
            'level':'DEBUG',
        },
        'lazyflow.graph.OperatorWrapper': {
            'handlers':['console', 'console_warn'],
            'propagate': False,
            'level':'INFO',
        },
    }
}

def init_default_config():
    logging.config.dictConfig(default_log_config)
