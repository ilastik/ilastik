import functools
import inspect

class bind(object):
    """
    Inspired by boost::bind (C++).
    Behaves like functools.partial, but discards any extra parameters it gets when called.
    """
    def __init__(self, f, *args):
        self.f = f
        self.bound_args = args
        self.numUnboundArgs = len(inspect.getargspec(self.f).args) - len(self.bound_args)
        if hasattr(f, 'im_self'):
            self.numUnboundArgs -= 1
    def __call__(self, *args):
        self.f(*(self.bound_args + args[0:self.numUnboundArgs]))

