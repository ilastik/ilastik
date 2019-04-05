from unittest import mock

import pytest

from lazyflow.request import request


@pytest.fixture
def signal():
    return request.SimpleSignal()


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
    # XXX: Is it valid behavior?
    subs = [
        mock.Mock(),
        mock.Mock(),
        mock.Mock(),
    ]

    class MyExc(Exception):
        pass

    subs[1].side_effect = MyExc()

    for s in subs:
        signal.subscribe(s)

    with pytest.raises(MyExc):
        signal(1, 2)

    subs[0].assert_called_once_with(1, 2)
    subs[1].assert_called_once_with(1, 2)
    subs[2].assert_not_called()
