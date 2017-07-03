#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Main entry-point to get a running ilastik-server


"""
from __future__ import division, print_function
from flask import Flask
from ilastik.shell.server.ilastikHttpAPI import ilastikHttpAPI
from ilastik.shell.server.appletHttpAPI import appletAPI
from ilastik.shell.server.workflowHttpAPI import workflowAPI
from ilastik.shell.server.projectHttpAPI import projectAPI
from ilastik.shell.server.ilastikAPI import IlastikAPI
from functools import partial


def create_app():
    """
    """
    # TODO: command line handling
    app = Flask(__name__)
    ilastik_api = IlastikAPI()
    app._ilastik_api = ilastik_api
    app.register_blueprint(ilastikHttpAPI)
    app.register_blueprint(appletAPI, url_prefix='/api/applet')
    app.register_blueprint(workflowAPI, url_prefix='/api/workflow')
    app.register_blueprint(projectAPI, url_prefix='/api/project')
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
    app.run()


if __name__ == '__main__':
    main()
