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
import pytest
import threading
from functools import partial

from PyQt5.QtCore import Qt, QEvent, QPoint, QTimer, Qt
from PyQt5.QtWidgets import QApplication, qApp
from PyQt5.QtGui import QPixmap, QMouseEvent

mainThreadPauseEvent = threading.Event()
mainFunc = None

def run_tests_in_separate_thread(filename):
    assert threading.current_thread().getName() == "MainThread"

    def emptyFunc():
        pass

    result = [False]
    def run_test():
        result[0] = pytest.main([filename])

        # If the test didn't push his own work to the main thread,
        #   then just push an empty function so we can proceed.        
        # (Only GUI tests actually use the main thread.)
        if mainFunc is None:
            run_in_main_thread( emptyFunc )
    
    testThread = threading.Thread( target=run_test )
    testThread.start()

    wait_for_main_func()
    testThread.join()
    return result[0]

def run_in_main_thread( f ):
    global mainFunc
    mainFunc = f
    mainThreadPauseEvent.set()

def wait_for_main_func():
    # Must be called from main thread
    assert threading.current_thread().getName() == "MainThread"
    
    # Wait until someone has given us a function to run.
    mainThreadPauseEvent.wait()
    mainFunc()
    mainThreadPauseEvent.clear()
