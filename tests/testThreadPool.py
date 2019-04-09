from builtins import next
from builtins import range
from builtins import object

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
import time
import threading
from lazyflow.request.threadPool import ThreadPool


class TestThreadPool(object):
    """
    The ThreadPool does not depend on any particular Request-specific interface; it can be used with any callable.
    This is a simple test to verify that it can execute regular functions.
    """

    @classmethod
    def setup_class(cls):
        cls.thread_pool = ThreadPool(num_workers=4)

    #     def testtest(self):
    #         for i in range(100):
    #             print i
    #             self.testBasic()

    def testBasic(self):
        f1_started = threading.Event()
        f2_started = threading.Event()
        f2_finished = threading.Event()

        def f1():
            f1_started.set()

        def f2():
            f2_started.set()
            f1_started.wait()
            f2_finished.set()

        TestThreadPool.thread_pool.wake_up(f2)
        f2_started.wait()
        TestThreadPool.thread_pool.wake_up(f1)

        f2_finished.wait()

        # This is just to make sure the test is doing what its supposed to.
        assert f1.assigned_worker != f2.assigned_worker, "{} == {}".format(f1.assigned_worker, f2.assigned_worker)

    def test(self):
        for _ in range(10):
            self._testAssignmentConsistency()

    def _testAssignmentConsistency(self):
        """
        If a callable is woken up (executed) more than once from the ThreadPool, it will execute on the same thread every time.
        (This is a useful guarantee for e.g. greenlet-based callables.)
        """
        e = threading.Event()
        f_thread_ids = []

        def f():
            f_thread_ids.append(threading.current_thread())
            e.set()

        # First time
        e.clear()
        self.thread_pool.wake_up(f)
        e.wait()

        # Second time, same callable
        e.clear()
        self.thread_pool.wake_up(f)
        e.wait()
        assert f_thread_ids[0] == f_thread_ids[1], "Callable should always execute on the same worker thread!"

        # Another example: Now do the same thing, but with a (wrapped) generator as the callable
        gen_thread_ids = []

        def gen():
            while True:
                gen_thread_ids.append(threading.current_thread())
                yield e.set()

        class WrappedGenerator(object):
            def __init__(self, generator):
                self.generator = generator

            def __call__(self):
                return next(self.generator)

        # First time
        g = WrappedGenerator(gen())
        e.clear()
        self.thread_pool.wake_up(g)
        e.wait()

        class TestTask:
            def __init__(self, f):
                self._f = f

            def __lt__(self, other):
                return id(self._f) < id(other)

            def __call__(self, *args, **kwargs):
                return self._f(*args, **kwargs)

        # Overload the threadpool with work,
        #  which should encourage random assignment of threads if something is broken
        def delay1():
            time.sleep(0.2)

        def delay2():
            time.sleep(0.2)

        def delay3():
            time.sleep(0.2)

        def delay4():
            time.sleep(0.2)

        def delay5():
            time.sleep(0.2)

        self.thread_pool.wake_up(TestTask(delay1))
        self.thread_pool.wake_up(TestTask(delay2))
        self.thread_pool.wake_up(TestTask(delay3))
        self.thread_pool.wake_up(TestTask(delay4))
        self.thread_pool.wake_up(TestTask(delay5))

        # Second time, same callable
        e.clear()
        self.thread_pool.wake_up(g)
        e.wait()
        assert gen_thread_ids[0] == gen_thread_ids[1], "Callable should always execute on the same worker thread!"

        # Ensure that all tasks have been processed
        # (avoid interfering with other tests in this suite).
        self.thread_pool._wait_for_idle()


if __name__ == "__main__":
    import sys
    import nose

    sys.argv.append("--nocapture")  # Don't steal stdout.  Show it on the console as usual.
    sys.argv.append("--nologcapture")  # Don't set the logging level to DEBUG.  Leave it alone.
    ret = nose.run(defaultTest=__file__)
    if not ret:
        sys.exit(1)
