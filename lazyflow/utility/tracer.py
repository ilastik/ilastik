import logging
import inspect

class Tracer(object):
    """
    Context manager to simplify function entry/exit logging trace statements.
    
    Example Usage:

    >>> # Create a TRACE logger
    >>> import sys, logging
    >>> traceLogger = logging.getLogger("TRACE.examplemodule1")
    >>> traceLogger.addHandler( logging.StreamHandler(sys.stdout) )
    
    >>> # Use the context manager
    >>> def f():
    ...     with Tracer(traceLogger):
    ...         print "Function f is running..."
    
    >>> # If TRACE logging isn't enabled, there's no extra output
    >>> f()
    Function f is running...

    >>> # Enable TRACE logging to see enter/exit log statements.
    >>> traceLogger.setLevel(logging.DEBUG)
    >>> f()
    (enter) f 
    Function f is running...
    (exit) f
    
    >>> # Disable TRACE logging by setting the level above DEBUG.
    >>> traceLogger.setLevel(logging.INFO)
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
                self._caller = stack[1][3]
            self._logger.log(self._level, "(enter) " + self._caller + ' ' + self._msg)

    def __exit__(self, *args):
        if self._logger.isEnabledFor( self._level ):
            self._logger.log(self._level, "(exit) " + self._caller)

from functools import wraps

def traceLogged(logger, level=logging.DEBUG, msg='', caller_name=''):
    """
    Returns a decorator that logs the entry and exit of its target function.
    Uses the the :py:class:`Tracer` context manager internally.

    Example Usage:

    >>> # Create a TRACE logger
    >>> import sys, logging
    >>> traceLogger = logging.getLogger("TRACE.examplemodule2")
    >>> traceLogger.addHandler( logging.StreamHandler(sys.stdout) )

    >>> # Decorate a function to allow entry/exit trace logging.
    >>> @traceLogged(traceLogger)
    ... def f():
    ...     print "Function f is running..."
    
    >>> # If TRACE logging isn't enabled, there's no extra output
    >>> f()
    Function f is running...

    >>> # Enable TRACE logging to see enter/exit log statements.
    >>> traceLogger.setLevel(logging.DEBUG)
    >>> f()
    (enter) f 
    Function f is running...
    (exit) f

    >>> # Disable TRACE logging by setting the level above DEBUG.
    >>> traceLogger.setLevel(logging.INFO)
    """
    def decorator(func):
        """A closure that logs the entry and exit of func using the logger."""

        if caller_name != '':
            name = caller_name
        elif hasattr(func, 'im_func'):
            name = func.im_func.func_name
        else:
            name = func.func_name
            
        @wraps(func)
        def wrapper(*args, **kwargs):
            with Tracer(logger, level=level, msg=msg, determine_caller=False, caller_name=name):
                return func(*args, **kwargs)
        wrapper.__wrapped__ = func # Emulate python 3 behavior of @wraps
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

    # Execute doctests
    import doctest
    doctest.testmod()
