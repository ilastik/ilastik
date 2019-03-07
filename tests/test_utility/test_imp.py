import importlib
import importlib.util
import sys

import pytest

from ilastik.utility import imp


def test_blacklist_works():
    with pytest.raises(imp.BlacklistedModuleError):
        with imp.ImportBlacklist("spam"):
            importlib.util.find_spec("spam")


def test_blacklist_ignores_other_modules():
    assert importlib.util.find_spec("eggs") is None
    with imp.ImportBlacklist("spam"):
        assert importlib.util.find_spec("eggs") is None


def test_blacklist_detects_already_imported_modules():
    with pytest.raises(imp.AlreadyImportedError):
        assert importlib.util.find_spec("spam") is None
        try:
            sys.modules["spam"] = None
            with imp.ImportBlacklist("spam"):
                    importlib.util.find_spec("spam")
        finally:
            del sys.modules["spam"]
