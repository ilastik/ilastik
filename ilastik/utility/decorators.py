from functools import wraps, partial
from operator import attrgetter


def lazy(function):
    """
    Decorates a function/method

    e.g.

    @lazy
    def f(*args, **kvargs): ...

    f( ... ) -> returns partial object to be called later
    f( ... )() -> normal execution

    f( ... , lazy=False) -> normal execution
    """
    @wraps(function)
    def decoree(*args, **kvargs):
        if "lazy" in kvargs:
            is_lazy = kvargs.pop("lazy")
        else:
            is_lazy = True
        if is_lazy:
            return partial(function, *args, **kvargs)
        return function(*args, **kvargs)
    return decoree


def require(*attrs, **keyvalue):
    """
    Prevents the execution of the function if any of the attrs is None
    or any of the keys does not have the given value

    :param attrs: the attributes that may not be None
    :param keyvalue: (key, value) => self.key must equal value

    e.g.

    @require("server")
    def f( ... ): ...

    calling f will only succeed if self.server is not None

    @require(running=True)
    def f( ...): ...

    calling f will only succeed if self.running == True

    """
    def inner(method):
        @wraps(method)
        def decoree(self, *args, **kvargs):
            for attr in attrs:
                if attrgetter(attr)(self) is None:
                    return
            for key, value in keyvalue.iteritems():
                if attrgetter(key)(self) != value:
                    return
            return method(self, *args, **kvargs)
        return decoree
    return inner
