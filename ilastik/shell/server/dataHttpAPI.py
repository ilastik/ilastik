"""Data access stuff
"""
from __future__ import division, print_function

import os
import io

import numpy
import zlib

from flask import Blueprint, request, url_for, jsonify, redirect, send_file
from flask import current_app as app
import StringIO

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


@dataAPI.route('/voxels/<dataset_name>/<source_name>', methods=['POST'])
def get_voxels(dataset_name, source_name):
    start = map(int, request.json.get('extents_min').split('_'))
    stop = map(int, request.json.get('extents_max').split('_'))
    slot = app._ilastik_api.slot_tracker.get_slot(dataset_name, source_name)

    format = 'raw'
    if 'format' in request.json:
        format = str(request.json['format'])


    data = slot(start, stop).wait()
    assert format == 'raw', "only raw for now"

    content_type = 'application/octet-stream'
    if format == 'raw':
        stream = StringIO.StringIO(encode_raw(data))
        return send_file(stream, mimetype=content_type)

    if format == 'npz':
        data = numpy.asarray(data, order='C')
        stream = encode_npz(data)
        return send_file(stream, mimetype=content_type)


def encode_npz(subvol):
    fileobj = io.BytesIO()
    if len(subvol.shape) == 3:
        subvol = numpy.expand_dims(subvol, 0)
    numpy.save(fileobj, subvol)
    cdz = zlib.compress(fileobj.getvalue())
    return cdz

def encode_raw(subvol):
    return subvol.tostring('C')
