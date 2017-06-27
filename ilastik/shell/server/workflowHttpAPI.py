"""Defines the external interface for workflow related stuff
"""
from __future__ import division, print_function
from flask import Blueprint, request, url_for, jsonify
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


workflowAPI = Blueprint('workflowAPI', __name__)


@workflowAPI.route('/current_workflow_name')
def get_current_workflow_name():
    logger.debug('getting current workflow name')
    workflow_name = app._ilastik_api.get_current_workflow_name()
    return jsonify(workflow_name=workflow_name)
