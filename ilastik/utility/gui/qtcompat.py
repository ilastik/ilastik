###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2026, the ilastik developers
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
"""
Tiny module to translate between numpy types and qt function signatures

Qt bindings have tight expectations on types, e.g. setChecked really expects
a Python bool and not a numpy.bool.
"""

from typing import Any

import numpy


class QtConversionError(TypeError):
    """Raised when a value cannot be converted to a Qt-compatible builtin."""


# NumPy 2.x exports both numpy.bool and numpy.bool_., 1.x only numpy.bool_
if hasattr(numpy, "bool"):
    NP_BOOL = numpy.bool
else:
    NP_BOOL = numpy.bool_

BOOL_TYPES = (bool, NP_BOOL, numpy.bool_)
INT_TYPES = (int, numpy.integer)
FLOAT_TYPES = (float, numpy.floating)


def ensure_bool(value: Any) -> bool:
    if isinstance(value, BOOL_TYPES + INT_TYPES + FLOAT_TYPES):
        return bool(value)

    raise QtConversionError(f"Potentially unintentional conversion: {type(value).__name__} to bool.")


def ensure_int(value: Any) -> int:
    if isinstance(value, BOOL_TYPES + INT_TYPES + FLOAT_TYPES):
        return int(value)

    raise QtConversionError(f"Potentially unintentional conversion: {type(value).__name__} to int.")


def ensure_float(value: Any) -> float:
    if isinstance(value, BOOL_TYPES + INT_TYPES + FLOAT_TYPES):
        return float(value)

    raise QtConversionError(f"Potentially unintentional conversion: {type(value).__name__} to float.")
