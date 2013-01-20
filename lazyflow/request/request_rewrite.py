# Built-in
import sys
import functools
import itertools
import collections
import threading
import multiprocessing

# Third-party
import greenlet

# lazyflow
import threadPool

class RequestGreenlet(greenlet.greenlet):
    def __init__(self, owning_request, fn):
        super(RequestGreenlet, self).__init__(fn)
        self.owning_requests = [owning_request]

class SimpleSignal(object):
    """
    Simple callback mechanism. Not synchronized.  No unsubscribe function.
    """
    def __init__(self):
        self.callbacks = []

    def subscribe(self, fn):
        self.callbacks.append(fn)

    def __call__(self, *args, **kwargs):
        """Emit the signal."""
        for f in self.callbacks:
            f(*args, **kwargs)
        
    def clean(self):
        self.callbacks = []

class Request( object ):
    
    # One thread pool shared by all requests.
    global_thread_pool = threadPool.ThreadPool( num_workers = multiprocessing.cpu_count() )
    
    class CancellationException(Exception):
        """
        This is raised when the whole request has been cancelled.
        If you catch this exception from within a request, clean up and return immediately.
        If you have nothing to clean up, you are not required to handle this exception.
        
        Implementation details:
        This exception is raised when the cancel flag is checked in the wait() function:
            - immediately before the request is suspended OR
            - immediately after the request is woken up from suspension
        """
        pass

    class InvalidRequestException(Exception):
        """
        This is raised when calling wait on a request that has already been cancelled,
        which can only happen if the request you're waiting for was spawned elsewhere 
        (i.e. you are waiting for someone else's request to avoid duplicate work).
        When this occurs, you will typically want to restart the request yourself.
        """
        pass

    class CircularWaitException(Exception):
        """
        This exception is raised if a request calls wait() on itself.
        Currently, this only catches the most basic case.
        No attempt is made to detect indirect cycles
        (e.g. if req.wait() is called from within a req's own child.),
        so don't rely on it to catch tricky deadlocks due to indirect self-waiting.
        """
        pass
    
    class TimeoutException(Exception):
        """
        This is raised if a call to wait() times out in the context of a foreign thread.
        See ``Request.wait()`` for details.
        """
        pass
    
    _root_request_counter = itertools.count()

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
        self.execution_complete = False
        self.finished_event = threading.Event()
        self.exception = None

        # Execution
        self.greenlet = None # Not created until assignment to a worker
        self._assigned_worker = None

        # Request relationships
        self.pending_requests = set()  # Requests that are waiting for this one
        self.blocking_requests = set() # Requests that this one is waiting for (currently one at most since wait() can only be called on one request at a time)
        self.child_requests = set()    # Requests that were created from within this request (NOT the same as pending_requests)
        
        self._current_foreign_thread = None
        current_request = Request.current_request()
        self.parent_request = current_request
        if current_request is None:
            self._priority = [ Request._root_request_counter.next() ]
        else:
            with current_request._lock:
                current_request.child_requests.add(self)
                # We must ensure that we get the same cancelled status as our parent.
                self.cancelled = current_request.cancelled
                # We acquire the same priority as our parent, plus our own sub-priority
                self._priority = current_request._priority + [ len(current_request.child_requests) ]

        self._lock = threading.Lock() # NOT an RLock, since requests may share threads
        self._sig_finished = SimpleSignal()
        self._sig_cancelled = SimpleSignal()
        self._sig_failed = SimpleSignal()
        
        self._sig_execution_complete = SimpleSignal()
        
        # FIXME: Can't auto-submit here because the writeInto() function gets called AFTER request construction.
        #self.submit()

    def __lt__(self, other):
        """
        Request comparison is by priority.
        This allows us to store them in a heap.
        """
        return self._priority < other._priority

    def clean(self):
        self._sig_cancelled.clean()
        self._sig_finished.clean()
        self._sig_failed.clean()
        self.result = None
        
    @property
    def assigned_worker(self):
        return self._assigned_worker
    
    @assigned_worker.setter
    def assigned_worker(self, worker):
        """
        Assign this request to the given worker thread.  (A request cannot switch between threads.)
        Must be called from the worker thread.
        """
        self._assigned_worker = worker

        # Create our greenlet now (so the greenlet has the correct parent, i.e. the worker)
        self.greenlet = RequestGreenlet(self, self.execute)

    def execute(self):
        """
        Do the real work of this request.
        """

        # Did someone cancel us before we even started?
        if not self.cancelled:
            try:
                # Do the actual work
                self.result = self.fn()
            except Request.CancellationException:
                # Don't propagate cancellations back to the worker thread,
                # even if the user didn't catch them.
                pass
            except Exception as ex:
                # The workload raised an exception.
                # Save it so we can raise it in any requests that are waiting for us.
                self.exception = ex
                self.exception_tb = sys.exc_traceback # Documentation warns of circular references here,
                                                      #  but that should be okay for us.

        # Guarantee that self.finished doesn't change while wait() owns self._lock
        with self._lock:
            self.finished = True

        try:
            # Notify callbacks (one or the other, not both)
            if self.cancelled:
                self._sig_cancelled()
            elif self.exception is not None:
                self._sig_failed( self.exception )
            else:
                self._sig_finished(self.result)

            # Unconditionally signal (internal use only)
            with self._lock:
                self.execution_complete = True
                self._sig_execution_complete()

        finally:
            # Notify non-request-based threads
            self.finished_event.set()

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
        Request.global_thread_pool.wake_up(self)
 
    def _switch_to(self):
        """
        Switch to this request's greenlet
        """
        self.greenlet.switch()

    def __call__(self):
        """
        Resume (or start) the request execution.
        This is implemented in __call__ so that it can be used with the ThreadPool, which is designed for general callable tasks.
        
        .. note:: DO NOT use ``Request.__call__`` explicitly from your code.  It is called internally or from the ThreadPool.
        """
        self._switch_to()
        
    def _suspend(self):
        """
        Suspend this request so another one can be woken up by the worker.
        """
        # Switch back to the worker that we're currently running in.
        self.greenlet.parent.switch()
        
    def wait(self, timeout=None):
        """
        Start this request if necessary, then wait for it to complete.  Return the request's result.
        :param timeout: If running within a request, this parameter must be None.
                        If running within the context of a foreign (non-request) thread, 
                        a timeout may be specified in seconds (floating-point).
                        If the request does not complete within the timeout period, 
                        then a Request.TimeoutException is raised.
        """        
        # Quick shortcut:
        # If there's no need to wait, just return immediately.
        # This avoids some function calls and locks.
        # (If we didn't do this, the code below would still do the right thing.)
        # Note that this is only possible because self.execution_complete is set to True 
        #  AFTER self.cancelled and self.exception have their final values.  See execute().
        if self.execution_complete and not self.cancelled and self.exception is None:
            return self.result
        
        # Identify the request that is waiting for us (the current context)
        current_request = Request.current_request()

        if current_request is None:
            # 'None' means that this thread is not one of the request worker threads.
            self._wait_within_foreign_thread( timeout )
        else:
            assert timeout is None, "The timeout parameter may only be used when wait() is called from a foreign thread."
            self._wait_within_request( current_request )

        assert self.finished
        return self.result

    def _wait_within_foreign_thread(self, timeout):
        """
        This is the implementation of wait() when executed from a foreign (non-worker) thread.
        Here, we rely on an ordinary threading.Event primitive: ``self.finished_event``
        """
        # Don't allow this request to be cancelled, since a real thread is waiting for it.
        self.uncancellable = True

        with self._lock:
            direct_execute_needed = not self.started and (timeout is None)
            if direct_execute_needed:
                # This request hasn't been started yet
                # We can execute it directly in the current thread instead of submitting it to the request thread pool (big optimization).
                # Mark it as 'started' so that no other greenlet can claim it
                self.started = True

        if self._current_foreign_thread is not None and self._current_foreign_thread == threading.current_thread():
            # It's usually nonsense for a request to wait for itself,
            #  but we allow it if the request is already "finished"
            # (which can happen if the request is calling wait() from within a notify_finished callback)
            if self.finished:
                return
            else:
                raise Request.CircularWaitException()

        if direct_execute_needed:
            self._current_foreign_thread = threading.current_thread()
            self.execute()
        else:
            self.submit()

        # This is a non-worker thread, so just block the old-fashioned way
        completed = self.finished_event.wait(timeout)
        if not completed:
            raise Request.TimeoutException()
        
        if self.cancelled:
            # It turns out this request was already cancelled.
            raise Request.InvalidRequestException()
        
        if self.exception is not None:
            raise self.exception.__class__, self.exception, self.exception_tb 

    def _wait_within_request(self, current_request):
        """
        This is the implementation of wait() when executed from another request.
        If we have to wait, suspend the current request instead of blocking the whole worker thread.
        """
        # Before we suspend the current request, check to see if it's been cancelled since it last blocked
        if current_request.cancelled:
            raise Request.CancellationException()

        if current_request == self:
            # It's usually nonsense for a request to wait for itself,
            #  but we allow it if the request is already "finished"
            # (which can happen if the request is calling wait() from within a notify_finished callback)
            if self.finished:
                return
            else:
                raise Request.CircularWaitException()

        with self._lock:
            # If the current request isn't cancelled but we are,
            # then the current request is trying to wait for a request (i.e. self) that was spawned elsewhere and already cancelled.
            # If they really want it, they'll have to spawn it themselves.
            if self.cancelled:
                raise Request.InvalidRequestException()
            
            if self.exception is not None:
                # This request was already started and already failed.
                # Simply raise the exception back to the current request.
                raise self.exception.__class__, self.exception, self.exception_tb 

            direct_execute_needed = not self.started
            suspend_needed = self.started and not self.execution_complete
            if direct_execute_needed or suspend_needed:
                current_request.blocking_requests.add(self)
                self.pending_requests.add(current_request)
            
            if direct_execute_needed:
                # This request hasn't been started yet
                # We can execute it directly in the current greenlet instead of creating a new greenlet (big optimization)
                # Mark it as 'started' so that no other greenlet can claim it
                self.started = True
            elif suspend_needed:
                # This request is already started in some other greenlet.
                # We must suspend the current greenlet while we wait for this request to complete.
                # Here, we set up a callback so we'll wake up once this request is complete.
                self._sig_execution_complete.subscribe( functools.partial(current_request._handle_finished_request, self) )

        if suspend_needed:
            current_request._suspend()
        elif direct_execute_needed:
            # Optimization: Don't start a new greenlet.  Directly run this request in the current greenlet.
            self.greenlet = current_request.greenlet
            self.greenlet.owning_requests.append(self)
            self._assigned_worker = current_request._assigned_worker
            self.execute()
            assert self.greenlet.owning_requests.pop() == self
            current_request.blocking_requests.remove(self)

        # Now we're back (no longer suspended)
        # Was the current request cancelled while it was waiting for us?
        if current_request.cancelled:
            raise Request.CancellationException()
        
        # Are we back because we failed?
        if self.exception is not None:
            raise self.exception.__class__, self.exception, self.exception_tb 

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
        with self._lock:
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

    def notify_failed(self, fn):
        """
        Register a callback function to be called when this request is finished due to failure (an exception was raised).
        If we're already failed, call it now.
        
        This function obtains the lock.
        """
        with self._lock:
            finished = self.finished
            failed = self.exception is not None
            if not finished:
                # Call when we eventually finish
                self._sig_failed.subscribe(fn)

        if finished and failed:
            # Call immediately
            fn(self.exception)

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
        if hasattr(current_greenlet, 'owning_requests'):
            return current_greenlet.owning_requests[-1]
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
        self.notify_finished( f)

    def onCancel(self, fn, *args, **kwargs):
        # Cheating here: The only operator that uses this old api function is OpArrayCache,
        # which doesn't do anything except return False to say "don't cancel me"
        
        # We'll just call it right now and set our flag with the result
        self.uncancellable = not fn(self, *args, **kwargs)

    def notify(self, fn, **kwargs):
        f = Request.PartialWithAppendedArgs( fn, **kwargs )
        self.notify_finished( f )
        self.submit()

    def allocate(self, priority = 0):
        return self

    def writeInto(self, destination):
        self.fn = Request.PartialWithAppendedArgs( self.fn, destination=destination )
        return self

    def getResult(self):
        return self.result

# The __call__ method used to be a synonym for wait(), but now it is used by the worker to start/resume the request.
#    def __call__(self):
#        return self.wait()

class RequestLock(object):
    """
    Request-aware lock.  Implements the same interface as threading.Lock.
    If acquire() is called from a normal thread, the the lock blocks the thread as usual.
    If acquire() is called from a Request, then the request is suspended so that another Request can be resumed on the thread.
    
    Requests and normal threads can *share* access to a RequestLock.
    That is, they compete equally for access to the lock.
    
    Implementation detail:  Depends on the ability to call two *private* Request methods: _suspend() and _wake_up().
    """
    def __init__(self):
        # This member holds the state of this RequestLock
        self._modelLock = threading.Lock()

        # This member protects the _pendingRequests set from corruption
        self._selfProtectLock = threading.Lock()
        
        # This is a list of requests that are currently waiting for the lock.
        # Other waiting threads (i.e. non-request "foreign" threads) are each listed as a single "None" item. 
        self._pendingRequests = collections.deque()
    
    def acquire(self, blocking=True):
        """
        :param blocking: Same as in threading.Lock 
        """
        current_request = Request.current_request()
        if current_request is None:
            return self._acquire_from_within_thread(blocking)
        else:
            return self._acquire_from_within_request(current_request, blocking)

    def _acquire_from_within_request(self, current_request, blocking):
            with self._selfProtectLock:
                # Try to get it immediately.
                got_it = self._modelLock.acquire(False)
                if not blocking:
                    return got_it
                if not got_it:
                    # We have to wait.  Add ourselves to the list of waiters.
                    self._pendingRequests.append(current_request)

            if not got_it:
                # Suspend the current request.
                # When it is woken, it owns the _modelLock.
                current_request._suspend()

            # Guaranteed to own _modelLock now (see release()).
            return True
        
    def _acquire_from_within_thread(self, blocking):
        if not blocking:
            return self._modelLock.acquire(blocking)

        with self._selfProtectLock:
            # Append "None" to indicate that a real thread is waiting (not a request)
            self._pendingRequests.append(None)

        # Wait for the internal lock to become free
        got_it = self._modelLock.acquire(blocking)
    
        with self._selfProtectLock:
            # Search for a "None" to pull off the list of pendingRequests.
            # Don't take real requests from the queue
            r = self._pendingRequests.popleft()
            while r is not None:
                self._pendingRequests.append(r)
                r = self._pendingRequests.popleft()

        return got_it

    def release(self):
        assert self._modelLock.locked(), "Can't release a RequestLock that isn't already acquired!"
        with self._selfProtectLock:
            if len(self._pendingRequests) == 0:
                # There were no waiting requests or threads, so the lock is free to be acquired again.
                self._modelLock.release()
            else:
                # Instead of releasing the modelLock, just wake up a request that was waiting for it.
                # He assumes that the lock is his when he wakes up.
                r = self._pendingRequests[0]
                if r is not None:
                    self._pendingRequests.popleft()
                    r._wake_up()
                else:
                    # The pending "request" is a real thread.
                    # Release the lock to wake it up (he'll remove the _pendingRequest entry)
                    self._modelLock.release()

    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()

class RequestPool(object):
    """
    Convenience class for submitting a batch of requests and waiting until they are all complete.
    Requests can not be added to the pool after it has already started.
    Not threadsafe (don't add requests from more than one thread).
    """

    class RequestPoolError(Exception):
        pass

    def __init__(self):
        self._requests = set()
        self._started = False

    def __len__(self):
        return len(self._requests)

    def add(self, req):
        """
        Add a request to the pool.
        """
        if self._started:
            # For now, we forbid this because it would allow some corner cases that we aren't unit-testing yet.
            # If this exception blocks a desirable use case, then change this behavior and provide a unit test.
            raise RequestPool.RequestPoolError("Attempted to add a request to a pool that was already started!")
        self._requests.add(req)

    def submit(self):
        """
        Submit all the requests in the pool.
        """
        if self._started:
            raise RequestPool.RequestPoolError("Can't re-start a RequestPool that was already started.")
        for req in self._requests:
            req.submit()

    def wait(self):
        """
        Wait for all requests in the pool to complete.
        """
        if not self._started:
            self.submit()
        for req in self._requests:
            req.wait()

    def request(self, func):
        """
        Deprecated method.  Convenience function to construct a request for the given callable and add it to the pool.
        """
        self.add( Request(func) )
    
    def clean(self):
        self._requests = set()

# BACKWARDS COMPATIBILITY
Pool = RequestPool






