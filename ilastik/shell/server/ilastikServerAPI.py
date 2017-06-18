"""Defines the external interface
"""
from __future__ import division, print_function
from flask import Blueprint, request
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


ilastikServerAPI = Blueprint('ilastikServerAPI', __name__)


@ilastikServerAPI.route('/')
def print_hello():
    logger.debug('Reached ilastikServerAPI')
    app._ilastikServer.a
    return app._ilastikServer.a


@ilastikServerAPI.route('/api/workflow/current_workflow_name')
def get_current_workflow_name():
    logger.debug('getting current workflow name')
    workflow_name = app._ilastikServer.get_current_workflow_name()
    return workflow_name


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running werkzeug')
    func()


@ilastikServerAPI.route('/shutdown')
def shutdown():
    shutdown_server()
    return ('shutting down')
