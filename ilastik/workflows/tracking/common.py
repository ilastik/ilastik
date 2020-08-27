###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2020, the ilastik developers
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
from dataclasses import dataclass
from typing import SupportsInt


@dataclass(frozen=True)
class PluralInflector:
    zero: str
    one: str
    many: str

    # arbitrarily defined maximum in case list() is called on this object
    max_index: int = 256

    def __getitem__(self, i: SupportsInt) -> str:
        i = int(i)
        if i < 0:
            raise ValueError("cannot inflect negative numbers")
        if i > self.max_index:
            raise IndexError(f"values above {self.max_index} not supported (got {i}).")
        if i == 0:
            return self.zero
        return f"{i} {self.one if i == 1 else self.many}"

    def __len__(self) -> int:
        return self.max_index


DIVISION_CLASSIFIER_LABEL_NAMES = PluralInflector(zero="False Detection", one="Object", many="Objects")
