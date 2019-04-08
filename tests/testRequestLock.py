from __future__ import division
from builtins import range
from builtins import object
import time
import random
import logging
import threading
from lazyflow.request import Request, RequestLock
from test_utilities import fail_after_timeout

logger = logging.getLogger("tests.testRequestLock")


class ThreadRequest(object):
    """
    Just threading.Thread, but the API looks a bit like Request.
    """

    def __init__(self, fn):
        self.thr = threading.Thread(target=fn)

    def submit(self):
        self.thr.start()

    def wait(self):
        self.thr.join()


@fail_after_timeout(20)
def test_RequestLock():
    assert Request.global_thread_pool.num_workers > 0, "This test must be used with the real threadpool."

    lockA = RequestLock()
    lockB = RequestLock()

    def log_request_system_status():
        status = (
            "*************************\n"
            + "lockA.pending: {}\n".format(len(lockA._pendingRequests))
            + "lockB.pending: {}\n".format(len(lockB._pendingRequests))
            # + "suspended Requests: {}\n".format( len(Request.global_suspend_set) )
            + "global job queue: {}\n".format(len(Request.global_thread_pool.unassigned_tasks))
        )
        for worker in Request.global_thread_pool.workers:
            status += "{} queued tasks: {}\n".format(worker.name, len(worker.job_queue))
        status += "*****************************************************"
        logger.debug(status)

    running = [True]

    def periodic_status():
        while running[0]:
            time.sleep(0.5)
            log_request_system_status()

    # Uncomment these lines to print periodic status while the test runs...
    status_thread = threading.Thread(target=periodic_status)
    status_thread.daemon = True
    status_thread.start()

    try:
        _impl_test_lock(lockA, lockB, Request, 1000)
    except:
        log_request_system_status()
        running[0] = False
        status_thread.join()

        global paused
        paused = False

        Request.reset_thread_pool(Request.global_thread_pool.num_workers)

        if lockA.locked():
            lockA.release()
        if lockB.locked():
            lockB.release()

        raise

    log_request_system_status()
    running[0] = False
    status_thread.join()


def test_ThreadingLock():
    # As a sanity check that our test works properly,
    #  try running it with 'normal' locks.
    # The test should pass no matter which task & lock implementation we use.
    _impl_test_lock(threading.Lock(), threading.Lock(), ThreadRequest, 100)


paused = True


def _impl_test_lock(lockA, lockB, task_class, num_tasks):
    """
    Simple test to start a lot of tasks that acquire/release the same two locks.

    We want to make sure that the test itself has sound logic,
    so it is written to be agnostic to the lock/task type.

    This test should work for both Requests (with RequestLocks) or 'normal'
    threading.Threads and Locks (as long as the API is adapted a bit to look
    like Requests via ThreadRequest, above.)
    """
    global paused
    paused = True
    progressAB = [0, 0]

    # Prepare
    lockB.acquire()

    def f1():
        """
        A.acquire(); B.release()
        """
        time.sleep(random.random() / 1000.0)
        lockA.acquire()
        logger.debug("Acquired A. Progress: {}".format(progressAB[0]))
        while paused:
            pass
        assert lockB.locked()
        lockB.release()
        progressAB[0] += 1
        if isinstance(lockA, RequestLock):
            logger.debug("lockA.pending: {}".format(len(lockA._pendingRequests)))

    def f2():
        """
        B.acquire(); A.release()
        """
        time.sleep(random.random() / 1000.0)
        lockB.acquire()
        logger.debug("Acquired B. Progress: {}".format(progressAB[1]))
        while paused:
            pass
        assert lockA.locked()
        lockA.release()
        progressAB[1] += 1
        if isinstance(lockB, RequestLock):
            logger.debug("lockB.pending: {}".format(len(lockB._pendingRequests)))

    tasks = []
    for _ in range(num_tasks):
        tasks.append(task_class(f1))
        tasks.append(task_class(f2))

    for task in tasks:
        task.submit()

    logger.debug("Pause for tasks to finish queuing.....")
    time.sleep(0.1)
    paused = False

    for task in tasks:
        task.wait()

    lockA.acquire()  # A should be left in released state.
    lockB.release()
    logger.debug("DONE")


def test_cancellation_behavior():
    """
    If a request is cancelled while it was waiting on a lock,
    it should raise the CancellationException.
    """
    lock = RequestLock()
    lock.acquire()

    def f():
        try:
            with lock:
                assert False
        except Request.CancellationException:
            pass
        else:
            assert False

    finished = [False]
    cancelled = [False]
    failed = [False]

    def handle_finished(result):
        finished[0] = True

    def handle_cancelled():
        cancelled[0] = True

    def handle_failed(*args):
        failed[0] = True

    req = Request(f)
    req.notify_finished(handle_finished)
    req.notify_failed(handle_failed)
    req.notify_cancelled(handle_cancelled)

    req.submit()
    req.cancel()
    time.sleep(0.1)
    lock.release()
    time.sleep(0.1)
    assert not finished[0] and not failed[0] and cancelled[0]


if __name__ == "__main__":
    import sys

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.

    import nose

    # Logging is OFF by default when running from command-line nose, i.e.:
    # nosetests thisFile.py)
    # but ON by default if running this test directly, i.e.:
    # python thisFile.py
    formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logger.setLevel(logging.DEBUG)

    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
