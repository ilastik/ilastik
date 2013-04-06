from time import sleep
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
        """
        Creates a paused timer.  Call `unpause()` to start the timer.
        """
        self.paused = True
        self.start_time = None
        self.stop_time = None

        self._last_start = None
        self._total_time = datetime.timedelta()
    
    def __enter__(self):
        self.unpause()
        return self
    
    def __exit__(self, *args):
        self.pause()

    def unpause(self):
        assert self.paused
        self._last_start = datetime.datetime.now()
        self.paused = False
        if self.start_time is None:
            self.start_time = self._last_start

    def pause(self):
        assert not self.paused
        self.paused = True
        self._last_stop = datetime.datetime.now()
        self._total_time += self._last_stop - self._last_start
        self.stop_time = self._last_stop
    
    def seconds(self):
        """
        Return the total elapsed time of the timer, not counting the time spent while paused.
        """
        timedelta = self._total_time
        if not self.paused:
            timedelta +=  datetime.datetime.now() - self._last_start
        return timedelta.seconds + timedelta.microseconds / 1000000.0

    def sleep_until(self, seconds):
        assert not self.paused
        remaining = seconds - self.seconds()
        if remaining > 0:
            sleep( remaining )

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
    import time
    
    t = Timer()
    for _ in range(10):
        with t:
            t.sleep_until(1)
        print t.seconds()        
    
    @timeLogged(logger, logging.INFO)
    def myfunc(x):
        time.sleep(0.2)

    print "Calling..."
    
    myfunc(2)
    print "Finished."
    