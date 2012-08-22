import greenlet
from collections import deque
import multiprocessing
import threading
from functools import partial

import sys
import logging
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#handler = logging.StreamHandler(sys.stdout)
#formatter = logging.Formatter('%(levelname)s %(name)s %(message)s')
#handler.setFormatter(formatter)
#logger.addHandler(handler)

class RequestGreenlet(greenlet.greenlet):
    def __init__(self, owning_request, fn):
        super(RequestGreenlet, self).__init__(fn)
        self.owning_request = owning_request

class SimpleSignal(object):
    """
    Simple callback mechanism. Not synchronized.  No unsubscribe function.
    """
    def __init__(self):
        self.callbacks = set()

    def subscribe(self, fn):
        self.callbacks.add(fn)

    def __call__(self, *args, **kwargs):
        """Emit the signal."""
        for f in self.callbacks:
            f(*args, **kwargs)

class Worker(threading.Thread):
    """
    Runs in a loop until stopped.
    The loop pops one request from the threadpool and starts (or resumes) it.
    """
    def __init__(self, thread_pool, index ):
        name = "Worker #{}".format(index)
        super(Worker, self).__init__( name=name )
        self.daemon = True # kill automatically on application exit!
        self.thread_pool = thread_pool
        self.stopped = False
        self.job_queue_condition = threading.Condition()
        self.job_queue = deque() # Threadsafe for append/pop
        
        loggerName = __name__ + '.Worker{}'.format(index)
        self.logger = logging.getLogger(loggerName)
        self.logger.debug("Created.")
    
    def run(self):
        """
        Keep executing available jobs (requests) until we're stopped.
        """
        # Try to get some work.
        current_request = self._get_next_job()

        while not self.stopped:
            # Start (or resume) the work by switching to its greenlet
            current_request.switch_to()

            # Try to get some work.
            current_request = self._get_next_job()

    def stop(self):
        """
        Tell this worker to stop running.
        Does not block for thread completion.
        """
        self.stopped = True
        # Wake up the thread if it's waiting for work
        with self.job_queue_condition:
            self.job_queue_condition.notify()

    def wake_up(self, request):
        """
        Add this request to the queue of requests that are ready to be processed.
        The request may or not be started already.
        """
        assert request.assigned_worker is self
        with self.job_queue_condition:
            self.job_queue.append(request)
            self.job_queue_condition.notify()

    def _get_next_job(self):
        """
        Get the next available job to perform.
        If necessary, block until:
            - a job is available (return the next request) OR
            - the worker has been stopped (might return None)
        """
        next_request = None

        # Keep trying until we get a job        
        with self.job_queue_condition:
            next_request = self._pop_job()

            while next_request is None and not self.stopped:
                # Wait for work to become available
                self.logger.debug("Waiting for work...")
                self.job_queue_condition.wait()
                next_request = self._pop_job()

        if not self.stopped:
            assert next_request is not None
            assert next_request.assigned_worker is self
        
        if not self.stopped:
            self.logger.debug("Got work.")

        return next_request
    
    def _pop_job(self):
        """
        Non-blocking.
        If possible, get a job from our own job queue.
        Otherwise, get one from the global job queue.
        Return None if neither queue has work to do.
        """
        # Try our own queue first
        if len(self.job_queue) > 0:
            return self.job_queue.popleft()

        # Otherwise, try to claim a job from the global unassigned list            
        try:
            req = self.thread_pool.unassigned_requests.popleft()
        except IndexError:
            return None
        else:
            req.set_assigned_worker(self)
            return req
    
class Singleton(type):
    """
    simple implementation of meta class that implements the singleton pattern.
    """
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance

class ThreadPool(object):
    """
    Manages a set of worker threads and dispatches requests to them.
    """
    
    # Thread pool is unique
    __metaclass__ = Singleton

    def __init__(self):
        self.job_condition = threading.Condition()
        self.immediate_work = deque() # Threadsafe for append and pop
        
        self.unassigned_requests = deque()

        num_workers = multiprocessing.cpu_count()
        self.workers = self._start_workers( num_workers )

    def wake_up(self, request):
        """
        Schedule the given request on the worker that is assigned to it.
        If necessary, first assign a worker to it.
        """
        # Once a request has been assigned, it must always be processed in the same worker
        if request.assigned_worker is not None:
            request.assigned_worker.wake_up( request )
        else:
            self.unassigned_requests.append(request)
            # Notify all currently waiting workers that there's new work
            logger.debug("Notifying workers of new work")
            self._notify_all_workers()

    def stop(self):
        """
        Stop all threads in the pool, and block for them to complete.
        Postcondition: All worker threads have stopped.  Unfinished requests are simply dropped.
        """
        for w in self.workers:
            w.stop()
        
        for w in self.workers:
            w.join()
    
    def _start_workers(self, num_workers):
        """
        Start a set of workers and return the set.
        """
        workers = set()
        for i in range(num_workers):
            w = Worker(self, i)
            workers.add( w )
            w.start()
            logger.debug("Started " + w.name)
        return workers

    def _notify_all_workers(self):
        """
        Wake up all worker threads that are currently waiting for work.
        """
        for worker in self.workers:
            with worker.job_queue_condition:
                worker.job_queue_condition.notify()

global_thread_pool = ThreadPool()
            

class Request( object ):
    
    logger = logging.getLogger(__name__ + '.Request')

    class CancellationException(Exception):
        """
        This is thrown when the whole request has been cancelled.
        If you catch this exception from within a request, clean up and return immediately.
        If you have nothing to clean up, you are not required to handle this exception.
        
        Implementation details:
        This exception is thrown when the cancel flag is checked in the wait() function:
            - immediately before the request is suspended OR
            - immediately after the request is woken up from suspension
        """
        pass

    class InvalidRequestException(Exception):
        """
        This is thrown when calling wait on a request that has already been cancelled,
        which can only happen if the request you're waiting for was spawned elsewhere 
        (i.e. you are waiting for someone else's request to avoid duplicate work).
        When this occurs, you will typically want to restart the request yourself.
        """
        pass

    def __init__(self, fn):
        """
        Constructor.
        Postconditions: The request has the same cancelled status as its parent
        """
        # Workload
        self.fn = fn
        self.result = None

        # State
        self.started = False
        self.cancelled = False
        self.uncancellable = False
        self.finished = False
        self.finished_event = threading.Event()

        # Execution
        self.greenlet = None # Not created until assignment to a worker
        self.assigned_worker = None

        # Request relationships
        self.pending_requests = set()  # Requests that are waiting for this one
        self.blocking_requests = set() # Requests that this one is waiting for (currently one at most since wait() can only be called on one request at a time)
        self.child_requests = set()    # Requests that were created from within this request (NOT the same as pending_requests)
        
        current_request = Request.current_request()
        self.parent_request = current_request
        if current_request is not None:
            with current_request._lock:
                current_request.child_requests.add(self)
                self.cancelled = current_request.cancelled

        self._lock = threading.Lock()
        self._sig_finished = SimpleSignal()
        self._sig_cancelled = SimpleSignal()
        
        self.logger.debug("Created request")
        
        # FIXME: Can't auto-submit here because the writeInto() function gets called AFTER request construction.
        #self.submit()
        
    def set_assigned_worker(self, worker):
        """
        Assign this request to the given worker thread.  (A request cannot switch between threads.)
        Must be called from the worker thread.
        """
        self.assigned_worker = worker

        # Create our greenlet now (so the greenlet has the correct parent, i.e. the worker)
        self.greenlet = RequestGreenlet(self, self.execute)

    def execute(self):
        """
        Do the real work of this request.
        """
        self.logger.debug("Executing in " + threading.current_thread().name)

        # Did someone cancel us before we even started?
        if not self.cancelled:
            try:
                # Do the actual work
                self.result = self.fn()
            except Request.CancellationException:
                # Don't propagate cancellations back to the worker thread,
                # even if the user didn't catch them.
                pass

        with self._lock:
            self.finished = True

        # Notify callbacks (one or the other, not both)
        if self.cancelled:
            self._sig_cancelled()
        else:
            self._sig_finished(self.result)

        # Notify non-request-based threads
        self.finished_event.set()

        self.logger.debug("Finished")
    
    def submit(self):
        """
        If this request isn't started yet, schedule it to be started.
        """
        with self._lock:
            if not self.started:
                self.started = True
                self._wake_up()
    
    def _wake_up(self):
        """
        Resume this request's execution (put it back on the worker's job queue).
        """
        self.logger.debug("Waking up")
        global_thread_pool.wake_up(self)
 
    def switch_to(self):
        """
        Switch to this request's greenlet
        """
        self.greenlet.switch()
        
    def _suspend(self):
        """
        Suspend this request so another one can be woken up by the worker.
        """
        # Switch back to the worker that we're currently running in.
        self.greenlet.parent.switch()
        
    def wait(self):
        """
        Start this request if necessary, then wait for it to complete.  Return the request's result.
        """
        self.submit()
        
        # Identify the request that is waiting for us (the current context)
        current_request = Request.current_request()

        if current_request is None:
            # Don't allow this request to be cancelled, since a real thread is waiting for it.
            self.uncancellable = True

            # This is a non-worker thread, so just block the old-fashioned way
            self.finished_event.wait()
            
            # It turns out this request was already cancelled.
            if self.cancelled:
                raise Request.InvalidRequestException()
        else:
            # We're running in the context of a request.
            # If we have to wait, suspend the current request instead of blocking the thread.

            # Before we suspend the current request, check to see if it's been cancelled since it last blocked
            if current_request.cancelled:
                raise Request.CancellationException()

            with self._lock:                
                # If the current request isn't cancelled but we are,
                # then the current request is trying to wait for a request (i.e. self) that was spawned elsewhere and already cancelled.
                # If they really want it, they'll have to spawn it themselves.
                if self.cancelled:
                    raise Request.InvalidRequestException()

                suspend_needed = not self.finished
                if suspend_needed:
                    current_request.blocking_requests.add(self)
                    self.pending_requests.add(current_request)
                    # No matter what, we need to be notified when this request stops.
                    # (Exactly one of these callback signals will fire.)
                    self._notify_finished_unlocked( partial(current_request._handle_finished_request, self) )
                    self._notify_cancelled_unlocked( partial(current_request._handle_finished_request, self) )

            if suspend_needed:
                current_request._suspend()

                # Now we're back (no longer suspended)
                # Were we cancelled in the meantime?
                if current_request.cancelled:
                    raise Request.CancellationException()    

        assert self.finished
        return self.result

    def _handle_finished_request(self, request, *args):
        """
        Called when a request that we were waiting for has completed.
        Wake ourselves up so we can resume execution.
        """
        with self._lock:
            # We're not waiting for this one any more
            self.blocking_requests.remove(request)
            if len(self.blocking_requests) == 0:
                self._wake_up()
    
    def notify_finished(self, fn):
        """
        Register a callback function to be called when this request is finished.
        If we're already finished, call it now.
        """
        self.submit()
        
        with self._lock:
            finished = self.finished
            if not finished:
                # Call when we eventually finish
                self._sig_finished.subscribe(fn)

        if finished:
            # Call immediately
            fn(self.result)

    def _notify_finished_unlocked(self, fn):
        """
        Same as notify_finished, but doesn't obtain the lock.
        Lock must be held before calling.
        """
        finished = self.finished
        if not finished:
            # Call when we eventually finish
            self._sig_finished.subscribe(fn)

        if finished:
            # Call immediately
            fn(self.result)

    def notify_cancelled(self, fn):
        """
        Register a callback function to be called when this request is finished due to cancellation.
        If we're already finished and cancelled, call it now.
        """
        with self._lock:
            finished = self.finished
            cancelled = self.cancelled
            if not finished:
                # Call when we eventually finish
                self._sig_cancelled.subscribe(fn)

        if finished and cancelled:
            # Call immediately
            fn()

    def _notify_cancelled_unlocked(self, fn):
        """
        Same as notify_cancelled, but doesn't obtain the lock.
        Lock must be held before calling.
        """
        finished = self.finished
        cancelled = self.cancelled
        if not finished:
            # Call when we eventually finish
            self._sig_cancelled.subscribe(fn)

        if finished and cancelled:
            # Call immediately
            fn()
        
    def cancel(self):
        # We can only be cancelled if: 
        # (1) There are no foreign threads blocking for us (flagged via self.uncancellable) AND
        # (2) our parent request (if any) is already cancelled AND
        # (3) all requests that are pending for this one are already cancelled
        with self._lock:
            cancelled = not self.uncancellable
            cancelled &= (self.parent_request is None or self.parent_request.cancelled)
            for r in self.pending_requests:
                cancelled &= r.cancelled

            self.cancelled = cancelled
            if cancelled:
                # Any children added after this point will receive our same cancelled status
                child_requests = self.child_requests
                self.child_requests = set()

        if self.cancelled:
            # Cancel all requests that were spawned from this one.
            for child in child_requests:
                child.cancel()
    
    @classmethod
    def current_request(cls):
        """
        Inspect the current greenlet/thread and return the request object associated with it, if any.
        """
        current_greenlet = greenlet.getcurrent()
        # Greenlets in worker threads have a monkey-patched 'owning-request' member
        if hasattr(current_greenlet, 'owning_request'):
            return current_greenlet.owning_request
        else:
            # There is no request associated with this greenlet.
            # It must be a regular (foreign) thread.
            return None

    ##########################################
    #### Backwards-compatible API support ####
    ##########################################

    class PartialWithAppendedArgs(object):
        """
        Like functools.partial, but any kwargs provided are given last when calling the target.
        """
        def __init__(self, fn, *args, **kwargs):
            self.func = fn
            self.args = args
            self.kwargs = kwargs
        
        def __call__(self, *args):
            totalargs = args + self.args
            return self.func( *totalargs, **self.kwargs)
    
    def onFinish(self, fn, **kwargs):
        f = Request.PartialWithAppendedArgs( fn, **kwargs )
        # Technically, this submits the request, which the old api didn't do,
        # but the old api never guaranteed when the request would be submitted, anyway...
        self.notify_finished( f )

    def onCancel(self, fn, *args, **kwargs):
        # Cheating here: The only operator that uses this old api function is OpArrayCache,
        # which doesn't do anything except return False to say "don't cancel me"
        
        # We'll just call it right now and set our flag with the result
        self.uncancellable = not fn(self, *args, **kwargs)

    def notify(self, fn, **kwargs):
        f = Request.PartialWithAppendedArgs( fn, **kwargs )
        self.notify_finished( f )

    def allocate(self, priority = 0):
        return self

    def writeInto(self, destination):
        self.fn = Request.PartialWithAppendedArgs( self.fn, destination=destination )
        return self

    def getResult(self):
        return self.result

    def __call__(self):
        return self.wait()











