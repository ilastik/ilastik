from apistar import Route
from ..views import workflow

routes = [
    Route('/get-structured-info', 'GET', workflow.get_structured_info)
]
