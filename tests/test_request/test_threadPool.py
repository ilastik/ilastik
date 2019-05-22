import threading
import time
import random
import itertools

from unittest import mock

import pytest

from lazyflow.request.threadPool import ThreadPool


NUM_WORKERS = 4


class Task:
    _counter = itertools.count()

    def __init__(self, fn):
        self.fn = fn
        self.assigned_worker = None
        self.priority = next(self._counter)

    def __lt__(self, other):
        return self.priority > self.priority

    def __call__(self):
        self.fn()


@pytest.fixture
def pool():
    return ThreadPool(NUM_WORKERS)


def test_thread_pool_starts_workers(pool: ThreadPool):
    assert pool.num_workers == len(pool.workers) == NUM_WORKERS

    for w in pool.workers:
        assert isinstance(w, threading.Thread)


def test_initial_state_of_workers(pool: ThreadPool):
    assert pool.get_states() == ["waiting"] * NUM_WORKERS


def test_stop_stops_all_workers(pool: ThreadPool):
    pool.stop()
    for w in pool.workers:
        w.join()


def test_wake_task_executes_task_on_idle_worker(pool: ThreadPool):
    start = threading.Event()
    stop = threading.Event()

    def task():
        start.set()
        time.sleep(0.2)
        stop.set()

    pool.wake_up(task)
    assert start.wait(timeout=1)
    assert pool.get_states().count("running task") == 1
    assert stop.wait(timeout=1)


def test_wake_task_executes_task_on_assigned_worker(pool: ThreadPool):
    stop = threading.Event()
    worker = None

    def task():
        nonlocal worker
        worker = threading.current_thread()
        time.sleep(0.2)
        stop.set()

    task.assigned_worker = random.choice(list(pool.workers))
    pool.wake_up(task)
    assert stop.wait(timeout=1)
    assert worker == task.assigned_worker


def test_exception_does_not_kill_worker():
    pool = ThreadPool(1)
    stop = threading.Event()
    order = []

    def task1():
        order.append(1)
        raise Exception()

    def task2():
        order.append(2)
        stop.set()

    pool.wake_up(Task(task1))
    pool.wake_up(Task(task2))

    assert stop.wait(timeout=1)
    assert order == [1, 2]


def test_exception_in_task_logged(caplog, pool):
    stop = threading.Event()

    class MyExc(Exception):
        pass

    def task1():
        try:
            raise MyExc()
        finally:
            stop.set()

    pool.wake_up(task1)
    assert stop.wait(timeout=1)
    assert len(caplog.records) == 1

    record = caplog.records[0]

    assert issubclass(record.exc_info[0], MyExc)
