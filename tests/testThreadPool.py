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

import threading

import pytest

from lazyflow.request.threadPool import ThreadPool


@pytest.fixture
def pool():
    p = ThreadPool(num_workers=4)
    yield p
    p.stop()


def test_basic(pool):
    f1_started = threading.Event()
    f2_started = threading.Event()
    f2_finished = threading.Event()

    def f1():
        f1_started.set()

    def f2():
        f2_started.set()
        f1_started.wait()
        f2_finished.set()

    pool.wake_up(f2)
    f2_started.wait()
    pool.wake_up(f1)

    f2_finished.wait()

    assert f1.assigned_worker != f2.assigned_worker


def test_function_executes_in_same_thread(pool):
    func_finished = threading.Event()
    thread_ids = []

    def func():
        thread_ids.append(threading.current_thread().ident)
        func_finished.set()

    for _i in range(pool.num_workers):
        func_finished.clear()
        pool.wake_up(func)
        func_finished.wait()

    assert len(set(thread_ids)) == 1


def test_generator_executes_in_same_thread(pool):
    gen_stepped = threading.Event()
    test_finished = threading.Event()
    thread_ids = []

    def make_gen():
        while True:
            thread_ids.append(threading.current_thread().ident)
            gen_stepped.set()
            yield

    class GenTask:
        def __init__(self, gen):
            self.gen = gen

        def __call__(self):
            return next(self.gen)

    gen_task = GenTask(make_gen())

    # Submit an infinite generator task and wait for it to be scheduled.
    # 1 worker is busy with gen_task, N-1 workers are free.
    pool.wake_up(gen_task)
    gen_stepped.wait()

    class WaitTask:
        def __init__(self, priority):
            self.priority = priority

        def __lt__(self, other):
            return self.priority < other.priority

        def __call__(self):
            test_finished.wait()

    # 1 worker is busy with gen_task, N-1 workers are busy with instances
    # of WaitTask, 1 instance of WaitTask is in the queue.
    for i in range(pool.num_workers):
        pool.wake_up(WaitTask(i))

    # Force the gen_task to take 1 more step.
    gen_stepped.clear()
    pool.wake_up(gen_task)
    gen_stepped.wait()

    # Ensure that both gen_task invocations have been executed in the same thread.
    assert len(thread_ids) == 2
    assert thread_ids[0] == thread_ids[1]

    # Release tasks that occupy workers, so that the thread pool can stop.
    test_finished.set()
