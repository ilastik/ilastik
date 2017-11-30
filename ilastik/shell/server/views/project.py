import os

from apistar import get_current_app, Response
from ..tools import log_function_call, time_function_call
from ..ilastikAPItypes import LocalProject, NewLocalProject

import logging

logger = logging.getLogger(__name__)


@time_function_call(logger)
def get_project_list():
    projects_path = get_current_app()._ilastik_config.projects_path
    print(projects_path)
    return {'projects': os.listdir(projects_path)}


@time_function_call(logger)
def new_project(project: NewLocalProject):
    app = get_current_app()
    project_name = project['project_name']
    project_type = project['project_type']
    projects_path = app._config.projects_path
    project_file_name = os.path.join(
        projects_path,
        "{project_name}.ilp".format(project_name=project_name))
    app._ilastik_api.create_project(project_file_name, project_type)
    return {
        'project_name': project_name,
        'project_type': project_type,
        'message': 'Project created.'
    }


@time_function_call(logger)
@log_function_call(logger)
def load_project(project: LocalProject):
    project_name = project['project_name']
    if project_name not in get_project_list()['projects']:
        return Response(
            content={
                'message': 'Project could not be found.',
            },
            status=404
        )

    get_current_app()._ilastik_api.load_project_file(
        os.path.join(
            get_current_app()._ilastik_config.projects_path,
            project_name
        )
    )

    return {
        'project_loaded': project,
        'message': 'Project loaded successfully.'
    }
