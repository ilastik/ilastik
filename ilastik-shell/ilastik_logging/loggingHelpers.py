import os
import sys
import logging
import logging.config
import json
import atexit

import threading
from functools import partial

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
    updates = json.load(f)
    logging.config.dictConfig(updates)

interval = 0
current_tag = 0
timer = None

def periodicUpdate( tag ):
    # Start a new timer if another one hasn't been started in the meantime
    if tag == current_tag:
        global timer
        updateFromConfigFile()
        timer = threading.Timer( interval, partial(periodicUpdate, tag) )
        timer.start()

def startUpdateInterval(nseconds):
    global interval
    global current_tag
    current_tag += 1
    interval = nseconds
    periodicUpdate(current_tag)

@atexit.register
def stopUpdates():
    print "Stopping log config updates"
    global current_tag
    global timer
    current_tag = -1
    if timer:
        timer.cancel()
