"""Defines the external interface for applet related stuff
"""
from __future__ import division, print_function
from flask import Blueprint, request, url_for, jsonify
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


projectAPI = Blueprint('projectAPI', __name__)


@projectAPI.route('/new-project', methods=['POST'])
def new_project():
    project_name = request.json.get('project_name')
    project_type = request.json.get('project_type')
    app._ilastik_api.create_project(project_name, project_type)
    return jsonify(project_name=project_name, project_type=project_type)
