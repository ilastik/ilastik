from concurrent.futures import CancelledError, Future
from typing import Callable, Generic, TypeVar


T = TypeVar("T")
S = TypeVar("S")


class MappableFuture(Future, Generic[T]):
    """
    Future class with helper methods to simplify combining and transforming underlying value
    """
    def map(self, func: Callable[[T], S]) -> "MappableFuture[S]":
        return map_future(self, func)


def map_future(future: Future, func: Callable[[T], S]) -> "MappableFuture[S]":
    """
    Apply function to underlying value preserving Future interface
    :param future:
    :param func:
    :return: new future which will be resolved once original future completes
    >>> fut = Future()
    >>> mapped = map_future(fut, lambda val: val + 10)
    >>> fut.set_result(32)
    >>> mapped.result()
    42
    """
    new_fut: S = MappableFuture()

    def _do_map(f):
        try:
            if f.cancelled():
                new_fut.cancel()
                return

            res = func(f.result())
            new_fut.set_result(res)
        except Exception as e:
            new_fut.set_exception(e)

    future.add_done_callback(_do_map)
    return new_fut
