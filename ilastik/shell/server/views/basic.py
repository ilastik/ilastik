from ..tools import time_function_call, log_function_call

import logging


logger = logging.getlogger(__name__)


@time_function_call
@log_function_call
def welcome(name: str=None):
    """Just some api landing page
    """
    ret_dict = {}
    if name is None:
        ret_dict['message'] = 'Welcome to Ilastik API!'
    else:
        ret_dict['message'] = f'Welcome to Ilastik API, {name}!'

    return ret_dict
