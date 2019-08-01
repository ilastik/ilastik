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

import atexit
import logging
import queue
import threading
from typing import Callable, List

logger = logging.getLogger(__name__)


class ThreadPool:
    """Manages a set of worker threads and dispatches tasks to them.

    Attributes:
        num_workers: The number of worker threads.
    """

    def __init__(self, num_workers: int):
        """Start all workers."""
        self.unassigned_tasks = queue.PriorityQueue()

        self.workers = {_Worker(self, i) for i in range(num_workers)}
        for w in self.workers:
            w.start()

        atexit.register(self.stop)

    @property
    def num_workers(self):
        return len(self.workers)

    def wake_up(self, task: Callable[[], None]) -> None:
        """Schedule the given task on the worker that is assigned to it.

        If it has no assigned worker yet, assign it to the first worker that becomes available.
        """
        if hasattr(task, "assigned_worker") and task.assigned_worker is not None:
            task.assigned_worker.wake_up(task)
        else:
            self.unassigned_tasks.put_nowait(task)
            for worker in self.workers:
                with worker.job_queue_condition:
                    worker.job_queue_condition.notify()

    def stop(self) -> None:
        """Stop all threads in the pool, and block for them to complete.

        Postcondition: All worker threads have stopped, unfinished tasks are simply dropped.
        """
        for w in self.workers:
            w.stop()

        for w in self.workers:
            w.join()

    def get_states(self) -> List[str]:
        return [w.state for w in self.workers]


class _Worker(threading.Thread):
    """Run in a loop until stopped.

    The loop pops one task from the threadpool and executes it.
    """

    def __init__(self, thread_pool, index):
        super().__init__(name=f"Worker #{index}", daemon=True)
        self.thread_pool = thread_pool
        self.stopped = False
        self.job_queue_condition = threading.Condition()
        self.job_queue = queue.PriorityQueue()
        self.state = "initialized"

    def run(self):
        """Keep executing available tasks until we're stopped."""
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
        """Tell this worker to stop running.

        Does not block for thread completion.
        """
        self.stopped = True
        # Wake up the thread if it's waiting for work
        with self.job_queue_condition:
            self.job_queue_condition.notify()

    def wake_up(self, task):
        """Add this task to the queue of tasks that are ready to be processed.

        The task may or not be started already.
        """
        assert task.assigned_worker is self
        with self.job_queue_condition:
            self.job_queue.put_nowait(task)
            self.job_queue_condition.notify()

    def _get_next_job(self):
        """Get the next available job to perform.

        If necessary, block until a task is available (return it) or the worker has been stopped (might return None).
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
        """If possible, get a job from our own job queue; otherwise, get one from the global job queue.

        Return None if neither queue has work to do.

        Non-blocking.
        """
        try:
            return self.job_queue.get_nowait()
        except queue.Empty:
            try:
                task = self.thread_pool.unassigned_tasks.get_nowait()
            except queue.Empty:
                return None
            else:
                # If this fails, then your callable is some built-in that doesn't allow arbitrary
                # members (e.g. .assigned_worker) to be "monkey-patched" onto it.
                # You may have to wrap it in a custom class first.
                task.assigned_worker = self
                return task
