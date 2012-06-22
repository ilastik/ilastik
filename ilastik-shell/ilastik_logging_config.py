import logging.config

log_config = {
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
            'class':'logging.StreamHandler',
            'formatter': 'location'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'lazyflow': {
            'handlers':['console'],
            'propagate': False,
            'level':'DEBUG',
        },
        'lazyflow.graph.OperatorWrapper': {
            'handlers':['console'],
            'propagate': False,
            'level':'INFO',
        },
    }
}

def init_logging():
    logging.config.dictConfig(log_config)
