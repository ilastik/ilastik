import time
import threading

from unittest import mock
from functools import partial

import pytest

from lazyflow.request.request import Request, SimpleSignal


class TExc(Exception):
    """
    Test exception to allow check if correct
    exception has propagated to top level
    """

    pass


class TestSignal:
    @pytest.fixture
    def signal(self):
        return SimpleSignal()

    def test_is_callable(self, signal: SimpleSignal):
        signal()

    def test_allows_function_registration(self, signal: SimpleSignal):
        def foo(*args, **kwargs):
            pass

        signal.subscribe(foo)

    def test_subscribed_functions_invoked_on_call(self, signal: SimpleSignal):
        f = mock.Mock()

        signal.subscribe(f)

        signal(1, 2, 3, val=2)

        f.assert_called_with(1, 2, 3, val=2)

    def test_subscribed_functions_called_in_sequence(self, signal: SimpleSignal):
        order = []
        for c in range(100):
            signal.subscribe(partial(order.append, c))

        signal()
        assert len(order) == 100
        assert order == sorted(order)

    def test_calling_cleaned_signal_raises_exception(self, signal: SimpleSignal):
        signal.clean()
        with pytest.raises(Exception):
            signal()

    def test_broken_subscriber(self, signal: SimpleSignal):
        subs = [mock.Mock(), mock.Mock(), mock.Mock()]

        subs[1].side_effect = TExc()

        for s in subs:
            signal.subscribe(s)

        with pytest.raises(TExc):
            signal(1, 2)

        subs[0].assert_called_once_with(1, 2)
        subs[1].assert_called_once_with(1, 2)
        subs[2].assert_not_called()


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


class TestRequest:
    def test_submit_should_assign_worker_and_execute(self):
        def work():
            return 42

        req = Request(work)
        req.submit()
        assert req.wait() == 42
        assert req.assigned_worker in Request.global_thread_pool.workers

    def test_submit_dependent_requests_should_execute_on_same_worker(self):
        more_work = Request(Work(lambda: 42))

        req = Request(Work(lambda: more_work.wait()))
        req.submit()

        assert req.wait() == 42
        assert req.assigned_worker in Request.global_thread_pool.workers
        assert req.assigned_worker == more_work.assigned_worker

    @pytest.fixture
    def broken_fn(self, request):
        def broken():
            raise TExc()

        return broken

    @pytest.fixture
    def work_fn(self, request):
        def work_fn():
            return 42

        return work_fn

    @staticmethod
    def work_req(fn):
        work = Work(fn)
        req = Request(work)
        return work, req

    def test_signal_finished_called_on_completion(self, work_fn):
        work, req = self.work_req(work_fn)

        recv = mock.Mock()

        req.notify_finished(recv)
        req.submit()
        assert work.done.wait(timeout=1)

        recv.assert_called_once_with(42)

    def test_signal_finished_called_when_subscription_happened_after_completion(self, work_fn):
        work, req = self.work_req(work_fn)

        recv = mock.Mock()
        req.submit()
        assert work.done.wait(timeout=1)

        req.notify_finished(recv)

        recv.assert_called_once_with(42)

    def test_signal_finished_should_not_be_called_on_exception(self, broken_fn):
        work, req = self.work_req(broken_fn)
        recv = mock.Mock()

        req.notify_finished(recv)
        req.submit()

        with pytest.raises(TExc):
            assert req.wait() == 42
        recv.assert_not_called()

    def test_signal_failed_should_be_called_on_exception(self, broken_fn):
        work, req = self.work_req(broken_fn)

        recv = mock.Mock()

        req = Request(work)
        req.notify_failed(recv)
        req.submit()

        with pytest.raises(TExc):
            assert req.wait() == 42
        recv.assert_called_once()
        assert isinstance(recv.call_args[0][0], TExc)

    def test_signal_failed_called_even_when_subscription_happened_after_completion(self, broken_fn):
        work, req = self.work_req(broken_fn)

        recv = mock.Mock()

        req = Request(work)
        req.submit()

        with pytest.raises(TExc):
            assert req.wait() == 42

        req.notify_failed(recv)
        recv.assert_called_once()
        assert isinstance(recv.call_args[0][0], TExc)


@pytest.fixture
def work():
    unpause = threading.Event()
    children = []

    def work_fn():
        more_work = Request(lambda: 42)
        some_more_work = Request(lambda: 42)
        children.extend([more_work, some_more_work])
        unpause.wait()
        return more_work.wait()

    work = Work(work_fn)
    work.unpause = unpause

    work.request = Request(work)
    work.request.submit()
    work.children = children

    assert work.started.wait()

    yield work

    if not work.unpause.is_set():
        work.unpause.set()

    assert work.done.wait()


def test_requests_created_within_request_considired_child_requests(work):
    assert work.request.child_requests == set(work.children)
    assert len(work.request.child_requests) == 2


@pytest.fixture
def cancelled_work(work):
    assert not work.request.cancelled
    work.request.cancel()
    assert work.request.cancelled

    work.unpause.set()
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
