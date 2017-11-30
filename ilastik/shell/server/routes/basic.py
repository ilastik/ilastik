from apistar import Route
from ..views import basic


routes = [
    Route('/', 'GET', basic.welcome),
    Route('/test', 'POST', basic.test)
]
