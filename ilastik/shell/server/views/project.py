import os

from apistar import get_current_app


def get_project_list():
    projects_path = get_current_app()._ilastik_config.projects_path
    print(projects_path)
    return {'projects': os.listdir(projects_path)}


def new_project():
    app = get_current_app()
    project_name = request.json.get('project_name')
    project_type = request.json.get('project_type')
    projects_path = app._config.projects_path
    project_file_name = os.path.join(
        projects_path,
        "{project_name}.ilp".format(project_name=project_name))
    app._ilastik_api.create_project(project_file_name, project_type)
    return jsonify(project_name=project_name, project_type=project_type)
