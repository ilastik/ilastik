import itertools


not_set = object()


def pairwise(iterable, tail=not_set):
    """
    Return pairwise iterator over sequence
    In case tail is provided last pair will include this value
    See examples below:

    >>> list(pairwise([1, 2, 3, 4], tail=None))
    [(1, 2), (2, 3), (3, 4), (4, None)]
    >>> list(pairwise([1, 2, 3, 4, 5], tail=None))
    [(1, 2), (2, 3), (3, 4), (4, 5), (5, None)]
    >>> list(pairwise([1], tail=None))
    [(1, None)]
    >>> list(pairwise([1]))
    []
    >>> list(pairwise([]))
    []
    """

    a, b = itertools.tee(iterable)
    next(b, None)

    if tail is not_set:
        return zip(a, b)
    else:
        return itertools.zip_longest(a, b, fillvalue=tail)
