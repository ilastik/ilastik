import logging
import inspect

class Tracer(object):
    """
    Context manager to simplify function entry/exit logging trace statements.
    Example Usage:
    
    def f():
        with Tracer(logging.getLogger("TRACE." + mymodule)):
            print "Function f is running..."
    
    Example Output:
        DEBUG TRACE.mymodule:__enter__: f
        Function f is running...
        DEBUG TRACE.mymodule:__exit__: f
    """
    def __init__(self, logger, level=logging.DEBUG, msg='', determine_caller=True, caller_name=''):
        if type(logger) == str:
            self._logger = logging.getLogger(logger)
        else:
            self._logger = logger
        self._level = level
        self._determine_caller = determine_caller
        self._msg = msg
        self._caller = caller_name

    def __enter__(self):
        if self._logger.isEnabledFor( self._level ):
            if self._determine_caller and self._caller == '':
                stack = inspect.stack()
                self._caller = stack[1][3] + ' '
            self._logger.log(self._level, "(enter) " + self._caller + self._msg)

    def __exit__(self, *args):
        if self._logger.isEnabledFor( self._level ):
            self._logger.log(self._level, "(exit) " + self._caller)

from functools import wraps

def traceLogged(logger, suffix=''):
    """Returns a decorator that logs the entry and exit of its target function."""
    def decorator(func):
        """A closure that logs the entry and exit of func using the logger."""
        if hasattr(func, 'im_func'):
            name = func.im_func.func_name
        else:
            name = func.func_name
            
        @wraps(func)
        def wrapper(*args, **kwargs):
            with Tracer(logger, determine_caller=False, caller_name=name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__=='__main__':
    import sys
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter( logging.Formatter("%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s") )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    def func1():
        with Tracer(logger):
            print "I'm func 1"

    @traceLogged(logger)
    def func2():
        print "I'm func 2"

    func1()
    func2()

