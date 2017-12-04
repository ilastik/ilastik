from apistar.frameworks.wsgi import WSGIApp as App
from apistar import Route, Include
from apistar.handlers import docs_urls, static_urls
import os

from .routes import basic, data, project, workflow
from .ilastikAPI import IlastikAPI
from .renderer import IlastikJSONRenderer


import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


routes = [
    Include('/docs', docs_urls),
    Include('/static', static_urls),
    Include('/project', project.routes),
    Include('/data', data.routes),
    Include('/workflow', workflow.routes)
]

# extend here in order to add them to site root
routes.extend(basic.routes)

settings = {
    'RENDERERS': [IlastikJSONRenderer()],
    'SCHEMA': {
        'TITLE': "ilastik-API",
        'DESCRIPTION': "ilastiks http intrerface for third party applications."
    }
}


app = App(routes=routes, settings=settings)


class IlastikServerConfig(object):
    def __init__(self, *args, **kwargs):
        super().__init__()
        default_config = {
            "projects_path": os.path.expanduser('~/ilastik_server/projects'),
            "data_path": os.path.expanduser('~/ilastik_server/data')
        }
        default_config.update(kwargs)

        self._config = default_config
        self.setup_paths()

    @property
    def config(self):
        return self._config

    @property
    def projects_path(self):
        return self._config['projects_path']

    @property
    def data_path(self):
        return self._config['data_path']

    def setup_paths(self):
        projects_path = self.projects_path
        if not os.path.exists(projects_path):
            os.makedirs(projects_path)
            logger.info(f'Created project path {projects_path}')
        logger.info(f'Using project path: {projects_path}')

        data_path = self.data_path
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            logger.info(f'Created data path {data_path}.')
        logger.info(f'Using data path: {data_path}')


ilastik_server_config = IlastikServerConfig()
ilastik_api = IlastikAPI()
app._ilastik_config = ilastik_server_config
app._ilastik_api = ilastik_api


if __name__ == '__main__':
    app.main()
