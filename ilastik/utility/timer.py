import datetime
import functools
import logging

class Timer(object):
    """
    Context manager.
    Takes a START timestamp on __enter__ and takes a STOP timestamp on __exit__.
    Call ``seconds()`` to get the elapsed time so far, or the total time if the timer has already stopped.
    
    .. note:: This class provides WALL timing of long-running tasks, not cpu benchmarking for short tasks.
    """
    def __init__(self):
        self.startTime = None
        self.stopTime = None
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()

    def start(self):
        self.startTime = datetime.datetime.now()

    def stop(self):
        self.stopTime = datetime.datetime.now()
    
    def seconds(self):
        """
        If the timer has already been stopped, return elapsed time = (stop - start) in seconds.
        If the timer hasn't stopped yet, return the elapsed time SO FAR.
        It is an error to call this function on a timer that hasn't been started yet.
        """
        assert self.startTime is not None, "Timer hasn't started yet!"
        if self.stopTime is None:
            now = datetime.datetime.now()
            timedelta = now - self.startTime
        else:
            timedelta = self.stopTime - self.startTime
        return timedelta.seconds + timedelta.microseconds / 1000000.0

def timed(func):
    """
    Decorator.
    A Timer is created for the given function, and it is reset every time the function is called.
    The timer is created as an attribute on the function itself called prev_run_timer.

    For example:
    
    .. code-block:: python

       @timed
       def do_stuff(): pass
       
       do_stuff()
       print "Last run of do_stuff() took", do_stuff.prev_run_timer.seconds(), "seconds to run"
    """
    prev_run_timer = Timer()
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with prev_run_timer:
            return func(*args, **kwargs)    

    wrapper.prev_run_timer = prev_run_timer
    wrapper.__wrapped__ = func # Emulate python 3 behavior of @functools.wraps
    return wrapper

def timeLogged(logger, level=logging.DEBUG):
    """
    Decorator. Times the decorated function and logs a message to the provided logger.
    
    For Example:

    .. code-block:: python
    
        import sys
        import logging
        logger = logging.getLogger(__name__)
        logger.addHandler( logging.StreamHandler(sys.stdout) )
        logger.setLevel( logging.INFO )
        
        @timeLogged(logger, logging.INFO)
        def myfunc(x):
            print x**100
        
        myfunc(2)
        
        # Output:
        # 1267650600228229401496703205376
        # myfunc execution took 3.1e-05 seconds

    """
    def _timelogged(func):
        f = timed(func)
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            finally:
                logger.log( level, "{} execution took {} seconds".format( f.__name__, f.prev_run_timer.seconds() ) )
        return wrapper
    return _timelogged

if __name__ == "__main__":
    import sys    
    logger = logging.getLogger(__name__)
    logger.addHandler( logging.StreamHandler(sys.stdout) )
    logger.setLevel( logging.INFO )
    
    @timeLogged(logger, logging.INFO)
    def myfunc(x):
        print x**100

    print "Calling..."
    myfunc(2)
    print "Finished."
    