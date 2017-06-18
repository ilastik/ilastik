#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Main entry-point to get a running ilastik-server


"""
from __future__ import division, print_function
from flask import Flask
from ilastik.shell.server.ilastikServerAPI import ilastikServerAPI
from ilastik.shell.server.appletAPI import appletAPI
from ilastik.shell.server.workflowAPI import workflowAPI
from ilastik.shell.server.projectAPI import projectAPI
from ilastik.shell.server.ilastikServer import IlastikServer
from functools import partial


def create_app():
    """
    """
    # TODO: command line handling
    app = Flask(__name__)
    ilastikServer = IlastikServer()
    app._ilastikServer = ilastikServer
    app.register_blueprint(ilastikServerAPI)
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
