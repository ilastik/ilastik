from concurrent.futures import CancelledError, Future
from typing import Callable, Generic, TypeVar


T = TypeVar("T")
S = TypeVar("S")


class MappableFuture(Future, Generic[T]):
    def map(self, func: Callable[[T], S]) -> "MappableFuture[S]":
        return map_future(self, func)


def map_future(future: Future, func: Callable[[T], S]) -> "MappableFuture[S]":
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
