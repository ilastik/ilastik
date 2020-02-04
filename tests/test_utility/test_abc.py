from abc import ABC, abstractmethod
from contextlib import nullcontext as does_not_raise

import pytest
from ilastik.utility.abc import StrictABC
from pytest import raises


class SpamABC(StrictABC):
    @abstractmethod
    def spam(self):
        pass


class SpamEggsABC(SpamABC):
    @abstractmethod
    def eggs(self):
        pass


def noop(_self):
    pass


@abstractmethod
def abstract_noop(_self):
    pass


@pytest.mark.parametrize(
    "abc_class,subclass,expectation",
    [
        (SpamABC, type("MyCls", (), {"spam": noop}), does_not_raise()),
        (SpamEggsABC, type("MyCls", (), {"spam": noop}), raises(TypeError)),
        (SpamEggsABC, type("MyCls", (), {"spam": noop, "eggs": noop}), does_not_raise()),
        (SpamABC, type("MyCls", (ABC,), {"spam": abstract_noop}), does_not_raise()),
        (SpamEggsABC, type("MyCls", (ABC,), {"spam": abstract_noop}), raises(TypeError)),
        (SpamEggsABC, type("MyCls", (ABC,), {"spam": abstract_noop, "eggs": abstract_noop}), does_not_raise()),
    ],
)
def test_StrictABC(abc_class, subclass, expectation):
    with expectation:
        abc_class.register(subclass)
