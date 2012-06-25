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
    def __init__(self, logger, level=logging.DEBUG, msg=''):
        if type(logger) == str:
            self._logger = logging.getLogger(logger)
        else:
            self._logger = logger
        self._level = level
        self._msg = msg

    def __enter__(self):
        if self._logger.isEnabledFor( self._level ):
            stack = inspect.stack()
            self._caller = stack[1][3]
            stackDepth = len(stack) - 1
            self._logger.log(self._level, '({})'.format(stackDepth) + self._caller + ' ' + self._msg)

    def __exit__(self, *args):
        if self._logger.isEnabledFor( self._level ):
            self._logger.log(self._level, self._caller)
