###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2023, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# In addition, as a special exception, the copyright holders of
# ilastik give you permission to combine ilastik with applets,
# workflows and plugins which are not covered under the GNU
# General Public License.
#
# See the LICENSE file for details. License information is also available
# on the ilastik web site at:
#          http://ilastik.org/license.html
###############################################################################
import pytest
from lazyflow.utility.exception_helpers import exception_chain, is_root_cause, root_cause


def test_none_in_exc_chain():
    exc_chain = list(exception_chain(None))

    assert exc_chain == []


@pytest.fixture
def example_exceptions():
    ex0 = RuntimeError("ex 0")
    ex1 = ValueError("ex 1")
    ex2 = TypeError("ex 2")

    return [ex2, ex1, ex0]


@pytest.fixture
def raise_nested_exception(example_exceptions):
    ex2, ex1, ex0 = example_exceptions

    def fun0():
        raise ex0

    def fun1():
        try:
            fun0()
        except Exception as e:
            raise ex1 from e

    def fun2():
        try:
            fun1()
        except Exception as e:
            raise ex2 from e

    return fun2


def test_exc_chain(example_exceptions, raise_nested_exception):
    try:
        raise_nested_exception()
    except Exception as e:
        for exc, expected_exc in zip(exception_chain(e), example_exceptions):
            assert exc == expected_exc


def test_root_cause(example_exceptions, raise_nested_exception):
    *_, chain_root_cause = example_exceptions
    try:
        raise_nested_exception()
    except Exception as e:
        assert root_cause(e) == chain_root_cause


def test_is_root_cause(example_exceptions, raise_nested_exception):
    *_, chain_root_cause = example_exceptions
    try:
        raise_nested_exception()
    except Exception as e:
        assert is_root_cause(type(chain_root_cause), e)
