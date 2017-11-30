from functools import wraps
from time import time
import inspect

import logging

logger = logging.getLogger(__name__)


def time_function_call(logger=logger):
    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            t1 = time()
            ret = func(*args, **kwargs)
            t2 = time()

            logger.debug(f'Execution took {t2 - t1} seconds')
            return ret
        return wrapped
    return wrapper


def log_function_call(logger=logger):
    def wrapper(func):
        assert inspect.isfunction(func)

        @wraps(func)
        def wrapped(*args, **kwargs):
            arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
            args_accumulated = args[:len(arg_names)]
            defaults = func.__defaults__ or ()
            args_accumulated = (args_accumulated +
                                defaults[len(defaults) - (func.__code__.co_argcount - len(args_accumulated)):])
            params = list(zip(arg_names, args_accumulated))
            args_additional = args[len(arg_names):]
            if args_additional:
                params.append(('args', args_additional))
            if kwargs:
                params.append(('kwargs', kwargs))
            logger.debug(f"{func.__name__}: ({', '.join('%s = %r' % p for p in params)})")
            return func(*args, **kwargs)

        return wrapped
    return wrapper
