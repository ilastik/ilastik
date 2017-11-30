from apistar import Route
from ..views import project


routes = [
    Route('/', 'GET', project.get_project_list),
    Route('/now-project', 'POST', project.new_project),
]
