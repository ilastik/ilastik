#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Main entry-point to get a running ilastik-server


"""
from __future__ import division, print_function
import os
from flask import Flask
from ilastik.shell.server.ilastikHttpAPI import ilastikHttpAPI
from ilastik.shell.server.appletHttpAPI import appletAPI
from ilastik.shell.server.workflowHttpAPI import workflowAPI
from ilastik.shell.server.projectHttpAPI import projectAPI
from ilastik.shell.server.ilastikAPI import IlastikAPI
from ilastik.shell.server.dataHttpAPI import dataAPI
from functools import partial

import logging


logger = logging.getLogger(__name__)


class IlastikServerConfig(object):
    def __init__(self, *args, **kwargs):
        super(IlastikServerConfig, self).__init__(*args, **kwargs)
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
            logger.info('Created project path %s', projects_path)

        data_path = self.data_path
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            logger.info('Created project path %s', data_path)


class DefaultConfig(object):
    DEBUG = True
    TESTING = False


def create_app(config=DefaultConfig):
    """
    """
    # TODO: command line handling

    app = Flask(__name__)
    app.config.from_object(config)
    ilastik_config = IlastikServerConfig()
    ilastik_api = IlastikAPI()
    app._ilastik_api = ilastik_api
    app._ilastik_config = ilastik_config
    app.register_blueprint(ilastikHttpAPI, url_prefix='/api/ilastik')
    app.register_blueprint(appletAPI, url_prefix='/api/applet')
    app.register_blueprint(workflowAPI, url_prefix='/api/workflow')
    app.register_blueprint(projectAPI, url_prefix='/api/project')
    app.register_blueprint(dataAPI, url_prefix='/api/data')
    return app


def create_interactive_app():
    from threading import Thread
    app = create_app()

    def run_until_stop(some_flask_app):
        print('Running flask server. navigate to ".../shutdown" to stop.')
        some_flask_app.run()
        print('app must have exited')

    t = Thread(target=partial(run_until_stop, app))
    t.start()
    return (t, app)


def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()
