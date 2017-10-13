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

import argparse
import logging


logger = logging.getLogger(__name__)


class ExpandPaths(argparse.Action):
    """Generate full paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        """"""
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


def parse_args():
    p = argparse.ArgumentParser(
        description="",
        usage="",
        epilog="",
    )

    p.add_argument(
        '--n-threads',
        default=8,
        type=int,
        help=('Set to 0 when using deep nets!'),
    )
    p.add_argument(
        '--projects-path',
        default="~/ilastik_server/projects",
        type=str,
        help=('Path with write permissions, to save and load projects.'),
        action=ExpandPaths,
    )
    p.add_argument(
        '--data-path',
        default="~/ilastik_server/data",
        type=str,
        help=('Path with write permissions, to save and load data'),
        action=ExpandPaths,
    )

    args = p.parse_args()
    return args


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


class DefaultConfig(object):
    DEBUG = False
    TESTING = False


def create_app(ilastik_config, config=DefaultConfig):
    """
    """
    # TODO: command line handling
    app = Flask(__name__)
    app.config.from_object(config)
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


def _init_logging():
    from ilastik.ilastik_logging import default_config, DEFAULT_LOGFILE_PATH

    logfile_path = DEFAULT_LOGFILE_PATH
    process_name = ""

    default_config.init(process_name, default_config.OutputMode.BOTH, logfile_path)


def _configure_lazyflow_settings(n_threads=None):
    import lazyflow
    import lazyflow.request
    from lazyflow.utility import Memory
    from lazyflow.operators.cacheMemoryManager import CacheMemoryManager

    if n_threads is not None:
        logger.info("Resetting lazyflow thread pool with {} threads.".format( n_threads ))
        lazyflow.request.Request.reset_thread_pool(n_threads)


def main():
    args = parse_args()
    _configure_lazyflow_settings(n_threads=args.n_threads)
    _init_logging()
    ilastik_kwargs = {}
    if args.projects_path != "":
        ilastik_kwargs['projects_path'] = args.projects_path
    if args.data_path != "":
        ilastik_kwargs['data_path'] = args.data_path
    ilastik_config = IlastikServerConfig(**ilastik_kwargs)
    app = create_app(ilastik_config=ilastik_config)
    app.run(host='0.0.0.0', port=5000, threaded=True)


if __name__ == '__main__':
    main()
