###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################
# Built-in
import atexit
import threading
import time
import ctypes
import logging

logger = logging.getLogger(__name__)


from lazyflow.utility.priorityQueue import PriorityQueue


class ThreadPool:
    """
    Manages a set of worker threads and dispatches tasks to them.
    """

    # _DefaultQueueType = FifoQueue
    # _DefaultQueueType = LifoQueue
    _DefaultQueueType = PriorityQueue

    def __init__(self, num_workers, queue_type=_DefaultQueueType):
        """
        Constructor.  Starts all workers.

        :param num_workers: The number of worker threads to create.
        :param queue_type: The type of queue to use for prioritizing tasks.  Possible queue types include :py:class:`PriorityQueue`,
                           :py:class:`FifoQueue`, and :py:class:`LifoQueue`, or any class with ``push()``, ``pop()``, and ``__len__()`` methods.
        """
        self.job_condition = threading.Condition()
        self.unassigned_tasks = queue_type()
        # self.memory = MemoryWatcher(self)
        # self.memory.start()
        self.num_workers = num_workers
        self.workers = self._start_workers(num_workers, queue_type)

        # ThreadPools automatically stop upon program exit
        atexit.register(self.stop)

    def wake_up(self, task):
        """
        Schedule the given task on the worker that is assigned to it.
        If it has no assigned worker yet, assign it to the first worker that becomes available.
        """
        # Once a task has been assigned, it must always be processed in the same worker
        if hasattr(task, "assigned_worker") and task.assigned_worker is not None:
            task.assigned_worker.wake_up(task)
        else:
            self.unassigned_tasks.push(task)
            # Notify all currently waiting workers that there's new work
            self._notify_all_workers()

    def stop(self):
        """
        Stop all threads in the pool, and block for them to complete.
        Postcondition: All worker threads have stopped.  Unfinished tasks are simply dropped.
        """
        # self.memory.stop()

        for w in self.workers:
            w.stop()

        for w in self.workers:
            w.join()

    def get_states(self):
        return [w.state for w in self.workers]

    def _start_workers(self, num_workers, queue_type):
        """
        Start a set of workers and return the set.
        """
        workers = set()
        for i in range(num_workers):
            w = _Worker(self, i, queue_type=queue_type)
            workers.add(w)
            w.start()
        return workers

    def _notify_all_workers(self):
        """
        Wake up all worker threads that are currently waiting for work.
        """
        for worker in self.workers:
            with worker.job_queue_condition:
                worker.job_queue_condition.notify()

    def _wait_for_idle(self):
        """
        Useful for testing only.
        Wait until there are no tasks left in the threadpool.
        """
        done = False
        while not done:
            while self.unassigned_tasks:
                time.sleep(0.1)

            for worker in self.workers:
                while worker.job_queue:
                    time.sleep(0.1)

            # Second pass: did any of those completing tasks launch new tasks?
            done = True
            for worker in self.workers:
                if len(worker.job_queue) > 0:
                    done = False
            if self.unassigned_tasks:
                done = False


class _Worker(threading.Thread):
    """
    Runs in a loop until stopped.
    The loop pops one task from the threadpool and executes it.
    """

    def __init__(self, thread_pool, index, queue_type):
        name = "Worker #{}".format(index)
        super(_Worker, self).__init__(name=name)
        self.daemon = True  # kill automatically on application exit!
        self.thread_pool = thread_pool
        self.stopped = False
        self.job_queue_condition = threading.Condition()
        self.job_queue = queue_type()
        self.state = "initialized"

    def run(self):
        """
        Keep executing available tasks until we're stopped.
        """
        # Try to get some work.
        self.state = "waiting"
        next_task = self._get_next_job()

        while not self.stopped:
            # Start (or resume) the work by switching to its greenlet
            self.state = "running task"
            try:
                next_task()
            except Exception:
                logger.exception("Exception during processing %s", next_task)

            # We're done with this request.
            # Free it immediately for garbage collection.
            self.state = "freeing task"
            next_task = None

            if self.stopped:
                return

            # Now try to get some work (wait if necessary).
            self.state = "waiting"
            next_task = self._get_next_job()

    def stop(self):
        """
        Tell this worker to stop running.
        Does not block for thread completion.
        """
        self.stopped = True
        # Wake up the thread if it's waiting for work
        with self.job_queue_condition:
            self.job_queue_condition.notify()

    def wake_up(self, task):
        """
        Add this task to the queue of tasks that are ready to be processed.
        The task may or not be started already.
        """
        assert task.assigned_worker is self
        with self.job_queue_condition:
            self.job_queue.push(task)
            self.job_queue_condition.notify()

    def _get_next_job(self):
        """
        Get the next available job to perform.
        If necessary, block until:
            - a task is available (return it) OR
            - the worker has been stopped (might return None)
        """
        # Keep trying until we get a job
        with self.job_queue_condition:
            if self.stopped:
                return None
            next_task = self._pop_job()

            while next_task is None and not self.stopped:
                # Wait for work to become available
                self.job_queue_condition.wait()
                if self.stopped:
                    return None
                next_task = self._pop_job()

        if not self.stopped:
            assert next_task is not None
            assert next_task.assigned_worker is self

        return next_task

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
            # task = self.thread_pool.memory.filter(self.thread_pool.unassigned_tasks.pop())
            task = self.thread_pool.unassigned_tasks.pop()
        except IndexError:
            return None
        else:
            task.assigned_worker = (
                self
            )  # If this fails, then your callable is some built-in that doesn't allow arbitrary
            #  members (e.g. .assigned_worker) to be "monkey-patched" onto it.  You may have to wrap it in a custom class first.
            return task

    def raise_exc(self, excobj):
        """
        I HAVEN'T TESTED THIS YET.  (But it looks useful.)
        http://code.activestate.com/recipes/496960-thread2-killable-threads

        Debugging method.
        Asynchronously raise an exception in this thread.
        See docstring for _async_raise() for more details.
        """
        assert self.isAlive(), "thread must be started"
        for tid, tobj in list(threading._active.items()):
            if tobj is self:
                _Worker._async_raise(tid, excobj)
                return

    @staticmethod
    def _async_raise(tid, excobj):
        """
        Raise an exception in the thread with the given id.
        http://code.activestate.com/recipes/496960-thread2-killable-threads
        """
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(excobj))
        if res == 0:
            raise ValueError("nonexistent thread id")
        elif res > 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
            raise SystemError("PyThreadState_SetAsyncExc failed")
