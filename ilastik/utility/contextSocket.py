from contextlib import contextmanager
import socket as socket_api


@contextmanager
def socket(*args, **kvargs):
    s = socket_api.socket(*args, **kvargs)
    yield s
    s.close()

socket_error = socket_api.error
