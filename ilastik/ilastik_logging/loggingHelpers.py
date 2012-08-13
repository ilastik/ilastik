import os
import sys
import logging
import logging.config
import json
import atexit

import threading
from functools import partial

logger = logging.getLogger(__name__)

class StdOutStreamHandler(logging.StreamHandler):
    """
    Stream Handler that defaults to sys.stdout instead of sys.stderr.
    """
    def __init__(self):
        super( StdOutStreamHandler, self ).__init__(stream=sys.stdout)

def updateFromConfigFile():
    # Import changes from a file    
    configFilePath = os.path.split(__file__)[0]+"/../logging_config.json"
    f = open(configFilePath)
    try:
        updates = json.load(f)
        logging.config.dictConfig(updates)
    except:
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
