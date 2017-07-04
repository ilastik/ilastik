"""Data access stuff
"""
from __future__ import division, print_function

import os

from flask import Blueprint, request, url_for, jsonify, redirect
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


dataAPI = Blueprint('dataHttpAPI', __name__)


def get_data_list():
    data_folder = app._ilastik_config.data_path
    file_list = os.listdir(data_folder)
    return file_list


@dataAPI.route('/available-data', methods=['GET'])
def list_available_data():
    file_list = get_data_list()
    return jsonify(available_data=file_list)
