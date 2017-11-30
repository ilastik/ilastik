from apistar import Route
from ..views import project


routes = [
    Route('/project-list', 'GET', project.get_project_list),
    Route('/new-project', 'POST', project.new_project),
    Route('/load-project', 'POST', project.load_project)
]
