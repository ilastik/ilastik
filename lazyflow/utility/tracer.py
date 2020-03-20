from __future__ import print_function
from builtins import object
import sys

if sys.version_info.major >= 3:
    unicode = str
###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################
import logging
import inspect


class Tracer(object):
    """
    Context manager to simplify function entry/exit logging trace statements.

    Examples:

        Example Usage::

            # Create a TRACE logger
            import sys, logging
            traceLogger = logging.getLogger("TRACE.examplemodule1")
            traceLogger.addHandler( logging.StreamHandler(sys.stdout) )

            # Use the context manager
            def f():
                with Tracer(traceLogger):
                    print("Function f is running...")

            # If TRACE logging isn't enabled, there's no extra output
            f()
            > Function f is running...

            # Enable TRACE logging to see enter/exit log statements.
            traceLogger.setLevel(logging.DEBUG)
            f()
            > (enter) f
            > Function f is running...
            > (exit) f

            # Disable TRACE logging by setting the level above DEBUG.
            traceLogger.setLevel(logging.INFO)
    """

    def __init__(self, logger, level=logging.DEBUG, msg="", determine_caller=True, caller_name=""):
        if isinstance(logger, (str, unicode)):
            self._logger = logging.getLogger(logger)
        else:
            self._logger = logger
        self._level = level
        self._determine_caller = determine_caller
        self._msg = msg
        self._caller = caller_name

    def __enter__(self):
        if self._logger.isEnabledFor(self._level):
            if self._determine_caller and self._caller == "":
                stack = inspect.stack()
                self._caller = stack[1][3]
            self._logger.log(self._level, "(enter) " + self._caller + " " + self._msg)

    def __exit__(self, *args):
        if self._logger.isEnabledFor(self._level):
            self._logger.log(self._level, "(exit) " + self._caller)


from functools import wraps


def traceLogged(logger, level=logging.DEBUG, msg="", caller_name=""):
    """
    Returns a decorator that logs the entry and exit of its target function.
    Uses the the :py:class:`Tracer` context manager internally.

    Examples:

        Example Usage::

            # Create a TRACE logger
            import sys, logging
            traceLogger = logging.getLogger("TRACE.examplemodule2")
            traceLogger.addHandler( logging.StreamHandler(sys.stdout) )

            # Decorate a function to allow entry/exit trace logging.
            @traceLogged(traceLogger)
            def f():
                print("Function f is running...")

            # If TRACE logging isn't enabled, there's no extra output
            f()
            > Function f is running...

            # Enable TRACE logging to see enter/exit log statements.
            traceLogger.setLevel(logging.DEBUG)
            f()
            > (enter) f
            > Function f is running...
            > (exit) f

            # Disable TRACE logging by setting the level above DEBUG.
            traceLogger.setLevel(logging.INFO)
    """

    def decorator(func):
        """A closure that logs the entry and exit of func using the logger."""

        if caller_name != "":
            name = caller_name
        elif hasattr(func, "im_func"):
            name = func.__func__.__name__
        else:
            name = func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            with Tracer(logger, level=level, msg=msg, determine_caller=False, caller_name=name):
                return func(*args, **kwargs)

        wrapper.__wrapped__ = func  # Emulate python 3 behavior of @wraps
        return wrapper

    return decorator


if __name__ == "__main__":
    import sys

    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(levelname)s %(thread)d %(name)s:%(funcName)s:%(lineno)d %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    def func1():
        with Tracer(logger):
            print("I'm func 1")

    @traceLogged(logger)
    def func2():
        print("I'm func 2")

    func1()
    func2()

    # Execute doctests
    import doctest

    doctest.testmod()
