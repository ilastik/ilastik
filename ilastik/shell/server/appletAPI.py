"""Defines the external interface for applet related stuff
"""
from __future__ import division, print_function
from flask import Blueprint, request, url_for, jsonify
from flask import current_app as app

import logging


logger = logging.getLogger(__name__)


appletAPI = Blueprint('appletAPI', __name__)