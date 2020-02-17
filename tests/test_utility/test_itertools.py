import pytest


from ilastik.utility.itertools import pairwise


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ([1, 2, 3, 4], [(1, 2), (2, 3), (3, 4), (4, None)]),
        ([1, 2, 3, 4, 5], [(1, 2), (2, 3), (3, 4), (4, 5), (5, None)]),
        ([1], [(1, None)]),
        ([], []),
    ],
)
def test_pairwise_with_tail(test_input, expected):
    assert list(pairwise(test_input, tail=None)) == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ([1, 2, 3, 4], [(1, 2), (2, 3), (3, 4)]),
        ([1, 2, 3, 4, 5], [(1, 2), (2, 3), (3, 4), (4, 5)]),
        ([1], []),
        ([], []),
    ],
)
def test_pairwise_without_tail(test_input, expected):
    assert list(pairwise(test_input)) == expected
