###############################################################################
#   lazyflow: data flow based lazy parallel computation framework
#
#       Copyright (C) 2011-2014, the ilastik developers
#                                <team@ilastik.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the Lesser GNU General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# See the files LICENSE.lgpl2 and LICENSE.lgpl3 for full text of the
# GNU Lesser General Public License version 2.1 and 3 respectively.
# This information is also available on the ilastik web site at:
# 		   http://ilastik.org/license/
###############################################################################

"""Utilities for numpy-like indices and shapes.

Adapted from "slicingtools.py" in volumina.
"""

import collections.abc
from typing import Sequence, Tuple, Union


def is_bounded(slicing: Union[slice, Sequence[slice]]) -> bool:
    """Do all slices have upper bounds?

    Examples:
        >>> is_bounded(slice(None, None))
        False
        >>> is_bounded(slice(1, None))
        False
        >>> is_bounded(slice(None, 5))
        True
        >>> is_bounded(slice(1, 5))
        True
        >>> is_bounded(slice(1, 5, 2))
        True
        >>> is_bounded((slice(1, 5), slice(6, None)))
        False
    """
    if not isinstance(slicing, collections.abc.Sequence):
        slicing = (slicing,)
    return all(sl.stop is not None for sl in slicing)


def slicing2shape(slicing: Union[slice, Sequence[slice]]) -> Tuple[int, ...]:
    """``X[slicing].shape``, where ``X`` is a sufficiently large array with the same number of dimensions.

    Raises:
        ValueError: Some slice is not bounded or not contiguous.

    Examples:
        >>> slicing2shape(())
        ()
        >>> slicing2shape(slice(2, 5))
        (3,)
        >>> slicing2shape([slice(2, 5), slice(4, 8)])
        (3, 4)
        >>> slicing2shape(slice(2, None))  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        ValueError
        >>> slicing2shape(slice(2, 5, 2))  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
          ...
        ValueError
    """
    items = slicing
    if not isinstance(slicing, collections.abc.Sequence):
        items = (slicing,)

    shape = []

    for sl in items:
        if sl.stop is None or sl.step is not None and sl.step != 1:
            raise ValueError(f"slicing {slicing} is not bounded or contiguous")
        shape.append(sl.stop - (sl.start or 0))

    return tuple(shape)
