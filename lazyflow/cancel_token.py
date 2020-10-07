"""
Utility classes/interfaces to simplify cancellation procedure
Usage example:

>>> def foo(token):
        while not token.cancelled:
            ...

>>> token_source = CancellationTokenSource()
>>> foo(token_source.token)
>>> token_source.cancel()

Idea behind a concept to separate client code that can cancel request (owner of CancellationTokenSource)
and cancellable procedure that only can query state of cancellation token
"""
import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

Thunk = Callable[[], None]


class CancellationToken:
    @property
    def cancelled(self):
        ...

    def add_callback(self, fn: Thunk) -> None:
        pass


class CancellationTokenSource:
    class _CancellationTokenImpl(CancellationToken):
        _callbacks: List[Thunk]

        def __init__(self):
            self._cancelled = False
            self._callbacks = []

        @property
        def cancelled(self):
            return self._cancelled

        def add_callback(self, fn: Thunk) -> None:
            self._callbacks.append(fn)

        def __repr__(self):
            return f"CancellationToken(id={id(self)}, cancelled={self._cancelled})"

    def __init__(self):
        self.__token = self._CancellationTokenImpl()

    @property
    def token(self):
        return self.__token

    def cancel(self):
        self.__token._cancelled = True

        for cb in self.__token._callbacks:
            try:
                cb()
            except Exception:
                logger.exception("Failed to invoke callback %s", cb)
