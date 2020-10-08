import logging
from unittest import mock
from lazyflow import cancel_token as ct


class TestCancellationToken:
    def test_cancel_source_provides_tokens(self):
        src = ct.CancellationTokenSource()
        assert isinstance(src.token, ct.CancellationToken)

    def test_cancel_source_provides_same_token(self):
        src = ct.CancellationTokenSource()
        token = src.token
        assert token is src.token

    def test_cancel_token_has_no_cancel_method(self):
        src = ct.CancellationTokenSource()
        token = src.token
        assert not hasattr(token, "cancel")

    def test_cancel_token_is_not_cancelled_when_created(self):
        src = ct.CancellationTokenSource()
        token = src.token
        assert not token.cancelled

    def test_cancel_token_is_cancelled_when_invoked(self):
        src = ct.CancellationTokenSource()
        assert not src.token.cancelled
        src.cancel()
        assert src.token.cancelled

    def test_cancel_token_add_callback(self):
        src = ct.CancellationTokenSource()
        callback_mock = mock.Mock()
        token = src.token
        token.add_callback(callback_mock)
        callback_mock.assert_not_called()
        src.cancel()
        callback_mock.assert_called_once_with()

    def test_cancel_token_add_callback_to_cancelled(self):
        src = ct.CancellationTokenSource()
        callback_mock = mock.Mock()

        token = src.token
        src.cancel()

        token.add_callback(callback_mock)
        callback_mock.assert_called_once_with()

    def test_cancel_token_add_callback_with_exception_logs(self, caplog):
        src = ct.CancellationTokenSource()
        token = src.token

        callback_mock = mock.Mock()
        callback_mock.side_effect = Exception("fail")

        token.add_callback(callback_mock)
        assert caplog.records == []
        src.cancel()

        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelno == logging.ERROR
        assert record.name == "lazyflow.cancel_token"
        assert record.exc_info
        assert record.message.startswith("Failed to invoke callback")

    def test_cancel_token_add_callback_with_exception_doesnt_prevent_consecutive_callbacks(self):
        src = ct.CancellationTokenSource()
        token = src.token

        callback_mock = mock.Mock()
        callback_mock.side_effect = Exception("fail")
        callback_mock2 = mock.Mock()

        token.add_callback(callback_mock)
        token.add_callback(callback_mock2)

        src.cancel()

        callback_mock.assert_called_once()
        callback_mock.assert_called_once()
