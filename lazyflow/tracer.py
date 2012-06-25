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
    def __init__(self, logger, level=logging.DEBUG):
        if type(logger) == str:
            self._logger = logging.getLogger(logger)
        else:
            self._logger = logger
        self._level = level
        self._caller = inspect.stack()[1][3]
    def __enter__(self):
        self._logger.log(self._level, self._caller)

    def __exit__(self, *args):
        self._logger.log(self._level, self._caller)
