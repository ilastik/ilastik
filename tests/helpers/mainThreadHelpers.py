import nose
import threading
from functools import partial

from PyQt4.QtCore import Qt, QEvent, QPoint, QTimer, Qt
from PyQt4.QtGui import QMouseEvent, QApplication, QPixmap, qApp

mainThreadPauseEvent = threading.Event()
mainFunc = None

def run_nosetests_in_separate_thread(filename):
    assert threading.current_thread() == threading.enumerate()[0]

    def emptyFunc():
        pass

    result = [False]
    def run_nose():
        result[0] = nose.run(defaultTest=filename)

        # If the test didn't push his own work to the main thread,
        #   then just push an empty function so we can proceed.        
        # (Only GUI tests actually use the main thread.)
        if mainFunc is None:
            run_in_main_thread( emptyFunc )
    
    noseThread = threading.Thread( target=run_nose )
    noseThread.start()

    wait_for_main_func()
    noseThread.join()
    if result[0] is True:
        return 0
    else:
        return 1

def run_in_main_thread( f ):
    global mainFunc
    mainFunc = f
    mainThreadPauseEvent.set()

def wait_for_main_func():
    # Must be called from main thread
    mainThread = threading.enumerate()[0]
    assert threading.current_thread() == mainThread
    
    # Wait until someone has given us a function to run.
    mainThreadPauseEvent.wait()
    mainFunc()
