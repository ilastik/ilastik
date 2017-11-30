from apistar import Route
from ..views import data

routes = [
    Route('/data-list', 'GET', data.list_available_data),
]
