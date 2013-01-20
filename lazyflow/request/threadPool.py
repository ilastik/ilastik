# Built-in
import atexit
import collections
import heapq
import threading
import multiprocessing

# lazyflow
import lazyflow

class PriorityQueue(object):
    """
    Simple threadsafe heap based on the python heapq module.
    """
    def __init__(self):
        self._heap = []
        self._lock = threading.Lock()

    def push(self, item):
        with self._lock:
            heapq.heappush(self._heap, item)
    
    def pop(self):
        with self._lock:
            return heapq.heappop(self._heap)
    
    def __len__(self):
        return len(self._heap)

class FifoQueue(object):
    """
    Simple FIFO queue based on collections.deque.
    """
    def __init__(self):
        self._deque = collections.deque() # Documentation says this is threadsafe for push and pop

    def push(self, item):
        self._deque.append(item)
    
    def pop(self):
        return self._deque.popleft()
    
    def __len__(self):
        return len(self._deque)

class LifoQueue(object):
    """
    Simple LIFO queue based on collections.deque.
    """
    def __init__(self):
        self._deque = collections.deque() # Documentation says this is threadsafe for push and pop

    def push(self, item):
        self._deque.append(item)
    
    def pop(self):
        return self._deque.pop()
    
    def __len__(self):
        return len(self._deque)

#_QueueType = FifoQueue
#_QueueType = LifoQueue
_QueueType = PriorityQueue

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
        self.job_queue = _QueueType()
        
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
            self.job_queue.push(request)
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
                self.job_queue_condition.wait()
                next_request = self._pop_job()

        if not self.stopped:
            assert next_request is not None
            assert next_request.assigned_worker is self

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
            return self.job_queue.pop()

        # Otherwise, try to claim a job from the global unassigned list            
        try:
            req = self.thread_pool.unassigned_requests.pop()
        except IndexError:
            return None
        else:
            req.set_assigned_worker(self)
            return req
    
class ThreadPool(object):
    """
    Manages a set of worker threads and dispatches requests to them.
    """
    
    # Thread pool is unique
    __metaclass__ = lazyflow.utility.Singleton

    def __init__(self):
        self.job_condition = threading.Condition()
        self.unassigned_requests = _QueueType()

        num_workers = multiprocessing.cpu_count()
        #num_workers = (multiprocessing.cpu_count() + 1) / 2
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
            self.unassigned_requests.push(request)
            # Notify all currently waiting workers that there's new work
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
        return workers

    def _notify_all_workers(self):
        """
        Wake up all worker threads that are currently waiting for work.
        """
        for worker in self.workers:
            with worker.job_queue_condition:
                worker.job_queue_condition.notify()

global_thread_pool = ThreadPool()

@atexit.register
def stop_thread_pool():
    global_thread_pool.stop()

