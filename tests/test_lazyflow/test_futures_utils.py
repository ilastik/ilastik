from unittest import mock
from concurrent.futures import Future
from lazyflow.futures_utils import MappableFuture, map_future

import pytest


class MyTestException(Exception):
    pass


class TestMappableFuture:
    def test_result_mapping(self):
        fut = MappableFuture()
        mapped_fut = fut.map(lambda v: v + 12)

        fut.set_result(30)
        assert mapped_fut.result() == 42

    def test_result_mapping_on_completed_future(self):
        fut = MappableFuture()
        fut.set_result(130)

        mapped_fut = fut.map(lambda v: v + 12)

        assert mapped_fut.result() == 142

    def test_result_mapping_concurrent_future(self):
        fut = Future()
        mapped_fut = map_future(fut, lambda v: v + 12)

        fut.set_result(30)
        assert isinstance(mapped_fut, MappableFuture)
        assert mapped_fut.result() == 42

    def test_result_mapping_map_function_raises(self):
        fut = MappableFuture()

        def _raise(v):
            raise MyTestException()

        mapped_fut = fut.map(_raise)

        fut.set_result(30)
        with pytest.raises(MyTestException):
            mapped_fut.result()

        assert isinstance(mapped_fut.exception(), MyTestException)

    def test_when_original_future_raises_exception_propagates(self):
        fut = MappableFuture()

        mock_func = mock.Mock()
        mapped_fut = fut.map(mock_func)

        fut.set_exception(MyTestException())

        assert not mock_func.called, "Map function should not be called in this case"
        assert isinstance(mapped_fut.exception(), MyTestException)

    def test_when_original_future_is_cancelled_status_propagates(self):
        fut = MappableFuture()

        mock_func = mock.Mock()
        mapped_fut = fut.map(mock_func)

        fut.cancel()
        assert not mock_func.called, "Map function should not be called in this case"
        assert mapped_fut.cancelled()
