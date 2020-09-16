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


class CancellationToken:
    @property
    def cancelled(self):
        ...


class CancellationTokenSource:
    class _CancellationTokenImpl(CancellationToken):
        def __init__(self):
            self._cancelled = False

        @property
        def cancelled(self):
            return self._cancelled

        def __repr__(self):
            return f"CancellationToken(id={id(self)}, cancelled={self._cancelled})"

    def __init__(self):
        self.__token = self._CancellationTokenImpl()

    @property
    def token(self):
        return self.__token

    def cancel(self):
        self.__token._cancelled = True
