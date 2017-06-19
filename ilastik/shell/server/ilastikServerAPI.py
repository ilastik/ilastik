"""Defines the external interface
"""
from __future__ import division, print_function
from flask import Blueprint, request, url_for, jsonify
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


ilastikServerAPI = Blueprint('ilastikServerAPI', __name__)


@ilastikServerAPI.route('/')
def print_hello():
    logger.debug('Reached ilastikServerAPI')
    r = ['<a href=%s>api</a>' % url_for('.get_GET_map')]
    r.append(str(app._ilastik_server))
    return "\n".join(r)


def has_no_empty_params(rule):
    """http://stackoverflow.com/a/13318415
    """
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)


@ilastikServerAPI.route('/api-map')
def get_GET_map():
    links = []
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))

    return "<br>".join("<a href={url:s}>{endpoint:s}</a>".format(url=url, endpoint=endpoint)
                       for url, endpoint in links)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running werkzeug')
    func()


@ilastikServerAPI.route('/shutdown')
def shutdown():
    shutdown_server()
    return ('shutting down')
