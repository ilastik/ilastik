###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2019, the ilastik developers
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
# 		   http://ilastik.org/license.html
###############################################################################

import sys
from importlib.abc import MetaPathFinder
from typing import Tuple


class Blacklist(MetaPathFinder):
    """Prevent importing of certain modules."""

    modules: Tuple[str]

    def __init__(self, *modules: str):
        self.modules = modules

    def find_spec(self, fullname, *_args):
        if fullname in self.modules:
            raise ImportError(f"Module {fullname} is blacklisted")

    def install(self) -> None:
        """Install the blacklist.

        Raises:
            ValueError: This blacklist has been already installed,
                or some of the blacklisted modules have been already imported.
        """
        if self in sys.meta_path:
            raise ValueError(f"{self} has been already installed")

        imported = ", ".join(filter(sys.modules.__contains__, self.modules))
        if imported:
            raise ValueError(f"Blacklisted modules {imported} have been already imported")

        sys.meta_path.insert(0, self)

    def __repr__(self) -> str:
        modules = ", ".join(map(repr, self.modules))
        return f"{self.__class__.__name__}({modules})"
