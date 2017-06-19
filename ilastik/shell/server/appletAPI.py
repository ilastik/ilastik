"""Defines the external interface for applet related stuff
"""
from __future__ import division, print_function
from flask import Blueprint, request, url_for, jsonify
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


appletAPI = Blueprint('appletAPI', __name__)


class IndexOutOfBounds(Exception):
    status_code = 404

    def __init__(self, message, status_code=None, payload=None):
        super(IndexOutOfBounds, self).__init__()
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        if self.payload is not None:
            ret_dict = dict(self.payload)
        else:
            ret_dict = dict()
        ret_dict['message'] = self.message
        return ret_dict


@appletAPI.route('/get-applet-names', methods=['GET'])
def get_applet_names():
    """Return list of names of applets
    """
    applet_names = app._ilastik_server.get_applet_names()
    return jsonify(applet_names=applet_names)


@appletAPI.route('/get-applet-information/<applet_index>', methods=['GET'])
def get_applet_information(applet_index):
    """Return json-representation of applets
    """
    try:
        applet_information = app._ilastik_server.get_applet_information(applet_index)
    except IndexError, e:
        raise IndexOutOfBounds(
            'No applet found at provided index {applet_index}'.format(applet_index=applet_index),
            payload={'error_message': str(e)})

    return jsonify(applet_information)


@appletAPI.errorhandler(IndexOutOfBounds)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
