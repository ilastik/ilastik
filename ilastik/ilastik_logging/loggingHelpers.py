###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#		   http://ilastik.org/license.html
###############################################################################
import os
import sys
import logging
import logging.config
import json
import atexit

import threading
from functools import partial

logger = logging.getLogger(__name__)

import ilastik

def updateFromConfigFile():
    # Import changes from a file    
   
    configFilePath = None
    try:
        configFilePath = ilastik.config.cfg.get("ilastik", "logging_config")
    except:
        configFilePath = os.path.split(__file__)[0]+"/logging_config.json"
        
    configFilePath = os.path.expanduser(configFilePath)
    if not os.path.exists(configFilePath):
        raise RuntimeError("Could not find config file at '%s'" % configFilePath)
        
    f = open(configFilePath)
    try:
        updates = json.load(f)
        logging.config.dictConfig(updates)
    except:
        import traceback
        traceback.print_exc()
        logging.error("Failed to load logging config file: " + configFilePath)

class NoWarnFilter(logging.Filter):
    """
    Filter out any records that are warnings or errors.
    (This is useful if your warnings and errors are sent to their own handler, e.g. stderr.)
    """
    def filter(self, record):
        return not (record.levelno == logging.WARN or record.levelno == logging.ERROR)

# Globals for the update timer thread
interval = 0
current_tag = 0
timer = None
timer_cancelled = False

def periodicUpdate( tag ):
    # Start a new timer if another one hasn't been started in the meantime
    global timer_cancelled
    if tag == current_tag and not timer_cancelled:
        global timer
        updateFromConfigFile()
        timer = threading.Timer( interval, partial(periodicUpdate, tag) )
        timer.daemon = True # Don't let this thread prevent application shutdown
        timer.start()

def startUpdateInterval(nseconds):
    global interval
    global current_tag
    current_tag += 1
    interval = nseconds
    periodicUpdate(current_tag)

@atexit.register
def stopUpdates():
    global current_tag
    global timer
    global timer_cancelled
    current_tag = -1
    timer_cancelled = True
    if timer:
        timer.cancel()
