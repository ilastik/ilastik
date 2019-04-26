import time
import threading

from unittest import mock

import pytest

from lazyflow.request.request import Request, SimpleSignal


class TExc(Exception):
    """
    Test exception to allow check if correct
    exception has propagated to top level
    """

    pass


@pytest.fixture
def signal():
    return SimpleSignal()


def test_signal_callable(signal):
    signal()


def test_allows_function_registration(signal):
    def foo(*args, **kwargs):
        pass

    signal.subscribe(foo)


def test_subscribed_functions_called_on_signal(signal):
    f = mock.Mock()

    signal.subscribe(f)

    signal(1, 2, 3, val=2)

    f.assert_called_with(1, 2, 3, val=2)


def test_subscribed_functions_called_in_sequence(signal):
    order = []
    for c in range(100):

        def fun(val=c):
            order.append(val)

        signal.subscribe(fun)

    signal()
    assert len(order) == 100

    for idx in range(len(order) - 1):
        assert order[idx] < order[idx + 1]


def test_cleaned_signal_raises_exception(signal):
    signal.clean()
    with pytest.raises(Exception):
        signal()


def test_signal_with_broken_subscriber(signal):
    subs = [mock.Mock(), mock.Mock(), mock.Mock()]

    subs[1].side_effect = TExc()

    for s in subs:
        signal.subscribe(s)

    with pytest.raises(TExc):
        signal(1, 2)

    subs[0].assert_called_once_with(1, 2)
    subs[1].assert_called_once_with(1, 2)
    subs[2].assert_not_called()


def test_submitting_request():
    stop = threading.Event()

    def work():
        time.sleep(0.3)
        stop.set()
        return 42

    req = Request(work)
    req.submit()
    assert req.wait() == 42
    assert req.assigned_worker in Request.global_thread_pool.workers


class Work:
    def __init__(self, work_fn=None):
        self.started = threading.Event()
        self.done = threading.Event()
        self.work_fn = work_fn

        self.result = None
        self.exception = None
        self.request = None

    def __call__(self):
        self.started.set()
        try:
            self.result = self.work_fn()
            return self.result
        except Exception as e:
            self.exception = e
            raise
        finally:
            self.done.set()


def test_submitting_requests_depending_on_each_other():
    stop = threading.Event()

    more_work = Request(Work(lambda: 42))

    req = Request(Work(lambda: more_work.wait()))
    req.submit()

    assert req.wait() == 42
    assert req.assigned_worker in Request.global_thread_pool.workers
    assert req.assigned_worker == more_work.assigned_worker


def test_signal_finished():
    recv = mock.Mock()
    work = Work(lambda: 42)
    req = Request(work)
    req.notify_finished(recv)
    req.submit()
    assert work.done.wait(timeout=1)
    recv.assert_called_once_with(42)


def test_signal_finished_on_exception():
    def broken():
        raise TExc()

    recv = mock.Mock()
    work = Work(broken)
    req = Request(work)
    req.notify_finished(recv)
    req.submit()

    with pytest.raises(TExc):
        assert req.wait() == 42

    recv.assert_not_called()


def test_signal_failed_on_exception():
    def broken():
        raise TExc()

    recv = mock.Mock()
    work = Work(broken)
    req = Request(work)
    req.notify_failed(recv)
    req.submit()

    with pytest.raises(TExc):
        assert req.wait() == 42

    recv.assert_called_once()
    assert isinstance(recv.call_args[0][0], TExc)


@pytest.fixture
def work():
    cont = threading.Event()
    children = []

    def work_fn():
        more_work = Request(lambda: 42)
        some_more_work = Request(lambda: 42)
        children.extend([more_work, some_more_work])
        cont.wait()
        return more_work.wait()

    work = Work(work_fn)
    work.cont = cont

    work.request = Request(work)
    work.request.submit()
    work.children = children

    assert work.started.wait()

    yield work

    if not work.cont.is_set():
        work.cont.set()

    assert work.done.wait()


def test_requests_created_within_request_considired_child_requests(work):
    assert work.request.child_requests == set(work.children)
    assert len(work.request.child_requests) == 2


@pytest.fixture
def cancelled_work(work):
    assert not work.request.cancelled
    work.request.cancel()
    assert work.request.cancelled

    work.cont.set()
    assert work.done.wait()

    return work


def test_wait_for_cancelled_rq_raises_invalid_request_exception(cancelled_work):
    work_rq = cancelled_work.request

    with pytest.raises(Request.InvalidRequestException):
        assert work_rq.wait()


def test_cancel_raises_exception_on_yield_point(cancelled_work):
    work_rq = cancelled_work.request
    assert isinstance(cancelled_work.exception, Request.CancellationException)


def test_cancels_child_requests(cancelled_work):
    assert len(cancelled_work.children) == 2

    for ch in cancelled_work.children:
        assert ch.cancelled

    work_rq = cancelled_work.request

    assert work_rq.child_requests == set()
