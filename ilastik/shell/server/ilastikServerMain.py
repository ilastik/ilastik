#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Main entry-point to get a running ilastik-server


"""
from __future__ import division, print_function
from flask import Flask
from ilastik.shell.server.ilastikServerAPI import ilastikServerAPI
from ilastik.shell.server.ilastikServer import IlastikServer


def create_app():
    """
    """
    # TODO: command line handling
    app = Flask(__name__)
    ilastikServer = IlastikServer()
    app._ilastikServer = ilastikServer
    app.register_blueprint(ilastikServerAPI)
    return app


def create_interactive_app():
    from threading import Thread
    app = create_app()
    t = Thread(target=app.run)
    return (t, app)


def main():
    app = create_app()
    app.run()


if __name__ == '__main__':
    main()
