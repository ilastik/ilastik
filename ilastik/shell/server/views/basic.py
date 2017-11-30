from apistar import typesystem
from ..tools import time_function_call, log_function_call
from ..ilastikAPItypes import Test
import logging


# local type definitions, just for the purpose of playing around
Name = typesystem.string(description='Enter your name if you like')

logger = logging.getLogger(__name__)


@time_function_call(logger)
@log_function_call(logger)
def welcome(name: Name=None):
    """Just some api landing page
    """
    ret_dict = {}
    if name is None:
        ret_dict['message'] = 'Welcome to Ilastik API!'
    else:
        ret_dict['message'] = f'Welcome to Ilastik API, {name}!'

    return ret_dict


@time_function_call(logger)
@log_function_call(logger)
def test(param3: Test) -> Test:
    logger.debug(param3)
    return param3
