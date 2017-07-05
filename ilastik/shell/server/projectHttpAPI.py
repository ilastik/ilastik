"""Defines the external interface for applet related stuff
"""
from __future__ import division, print_function

import os

from flask import Blueprint, request, url_for, jsonify, redirect
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


projectAPI = Blueprint('projectAPI', __name__)

ALLOWED_EXTENSIONS = ['ilp']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@projectAPI.route('/new-project', methods=['POST'])
def new_project():
    project_name = request.json.get('project_name')
    project_type = request.json.get('project_type')
    projects_path = app._config.projects_path
    project_file_name = os.path.join(
        projects_path,
        "{project_name}.ilp".format(project_name=project_name))
    app._ilastik_api.create_project(project_file_name, project_type)
    return jsonify(project_name=project_name, project_type=project_type)


@projectAPI.route('/upload-project', methods=['GET', 'POST'])
def upload_project():
    # TODO: how to upload files
    # TODO: how to maintain a global config.. through app I guess
    if request.method == 'GET':
        # if get, return a list
        return jsonify(project_list=get_project_list())
    elif request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        # flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        # do some checking, renaming
        filename = file.filename
        file.save(os.path.join(app._ilastik_config.projects_path, filename))
        return redirect(jsonify(get_project_list()))


def get_project_list():
    project_path = app._ilastik_config.projects_path
    return os.listdir(project_path)


@projectAPI.route('/load-project', methods=['GET'])
@projectAPI.route('/load-project/<project>', methods=['GET'])
def load_project(project=None):
    if project is None:
        return jsonify(project_list=get_project_list())
    else:
        if project not in get_project_list():
            return jsonify(
                message='Project could not be found.',
                status_code=404
                )
        app._ilastik_api.load_project_file(
            os.path.join(
                app._ilastik_config.projects_path,
                project
                ))
        return jsonify(project_loaded=project)
