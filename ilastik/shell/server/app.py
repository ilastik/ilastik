from apistar import Include, Route
from apistar.frameworks.wsgi import WSGIApp as App
from apistar.handlers import docs_urls, static_urls

from functools import wraps
import logging

from time import time

logger = logging.getLogger(__name__)


def time_function_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t1 = time()
        ret = func(*args, **kwargs)
        t2 = time()

        print(f'Execution took {t2 - t1} seconds')
        return ret
    return wrapper


def log_function_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
        args_accumulated = args[:len(arg_names)]
        defaults = func.__defaults__ or ()
        args_accumulated = args_accumulated + defaults[len(defaults) - (func.__code__.co_argcount - len(args_accumulated)):]
        params = list(zip(arg_names, args_accumulated))
        args_additional = args[len(arg_names):]
        if args_additional:
            params.append(('args', args_additional))
        if kwargs:
            params.append(('kwargs', kwargs))
        print(f"{func.__name__}: ({', '.join('%s = %r' % p for p in params)})")
        return func(*args, **kwargs)

    return wrapper

@time_function_call
@log_function_call
def welcome(name=None) -> dict:
    if name is None:
        return {'message': 'Welcome to API Star!'}
    return {'message': 'Welcome to API Star, %s!' % name}


routes = [
    Route('/', 'GET', welcome),
    Include('/docs', docs_urls),
    Include('/static', static_urls)
]

app = App(routes=routes)


if __name__ == '__main__':
    app.main()
