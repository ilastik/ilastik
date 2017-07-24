"""Defines the external interface for workflow related stuff
"""
from __future__ import division, print_function

import os

from lazyflow.utility.pathHelpers import PathComponents

from flask import Blueprint, request, url_for, jsonify
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


workflowAPI = Blueprint('workflowAPI', __name__)


@workflowAPI.route('/current_workflow_name')
def get_current_workflow_name():
    logger.debug('getting current workflow name')
    workflow_name = app._ilastik_api.workflow_name
    return jsonify(workflow_name=workflow_name)


@workflowAPI.route('/add-input-data', methods=['POST'])
def add_input_to_current_workflow():
    data_name = str(request.json.get('data_name'))
    data_path = app._ilastik_config.data_path
    image_file = os.path.join(data_path, data_name)
    pc = PathComponents(image_file)
    if not os.path.exists(pc.externalPath):
        ret = jsonify(message='Could not find image file. Is it on the server?')
        ret.status_code = 404
        return ret

    app._ilastik_api.add_dataset(image_file)
    return jsonify(data_loaded=data_name)

@workflowAPI.route('/structured-info')
def get_structured_info():
    dataset_names, json_states = app._ilastik_api.get_structured_info()
    resp = jsonify(states=json_states, image_names=dataset_names)
    resp.status_code = 200
    return resp
