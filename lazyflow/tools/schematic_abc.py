from builtins import object

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
from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass


def _has_attribute(cls, attr):
    return True if any(attr in B.__dict__ for B in cls.__mro__) else False


def _has_attributes(cls, attrs):
    return True if all(_has_attribute(cls, a) for a in attrs) else False


class DrawableABC(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def size(self):
        return NotImplemented

    @abstractmethod
    def drawAt(self, canvas, upperLeft):
        """
        Return the svg text for this item, starting at the given point.
        """
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        if cls is DrawableABC:
            return True if _has_attributes(C, ["size", "drawAt"]) else False
        return NotImplemented


class ConnectableABC(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def key(self):
        return NotImplemented

    @abstractmethod
    def upstream_slot_key(self):
        return NotImplemented

    @classmethod
    def __subclasshook__(cls, C):
        if cls is DrawableABC:
            return True if _has_attributes(C, ["key", "upstream_slot_key"]) else False
        return NotImplemented
