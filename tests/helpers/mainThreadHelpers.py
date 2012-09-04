import threading

mainThreadPauseEvent = threading.Event()
mainFunc = None

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