###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import inspect

def getRootArgSpec(f):
    if hasattr( f, '__wrapped__' ):
        return getRootArgSpec(f.__wrapped__)
    else:
        return inspect.getfullargspec(f)

class bind(tuple):
    """Behaves like functools.partial, but discards any extra
    parameters it gets when called. Also, bind objects can be compared
    for equality and hashed.

    bind objects are immutable.

    Inspired by boost::bind (C++).

    """
    def __new__(cls, f, *args):
        bound_args = args
        expected_args = getRootArgSpec(f).args
        numUnboundArgs = len(expected_args) - len(bound_args)
        if len(expected_args) > 0 and expected_args[0] == 'self':
            numUnboundArgs -= 1
        return tuple.__new__(cls, (f, bound_args, numUnboundArgs))

    @property
    def f(self):
        return self[0]

    @property
    def bound_args(self):
        return self[1]

    @property
    def numUnboundArgs(self):
        return self[2]

    def __call__(self, *args):
        """Execute the callback. If more args are provided than
        the callback accepts, silently discard the extra args.

        """
        self.f(*(self.bound_args + args[0:self.numUnboundArgs]))
