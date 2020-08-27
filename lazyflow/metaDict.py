from builtins import zip

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
# Python
import copy
import numpy
from collections import OrderedDict, defaultdict
from ndstructs import Shape5D


class MetaDict(defaultdict):
    """
    Helper class that manages the dirty state of the meta data of a slot.
    changing a meta dicts attributes sets it _dirty flag True.
    """

    def __init__(self, other=None, *args, **kwargs):
        if other is None:
            defaultdict.__init__(self, lambda: None, **kwargs)
        else:
            defaultdict.__init__(self, lambda: None, other, **kwargs)

        if not "_ready" in self:
            # flag that indicates whether all dependencies of the slot
            # are ready
            self._ready = False

        # flag that indicates whether any piece of meta information
        # changed since this flag was reset
        self._dirty = True

    def __setattr__(self, name, value):
        """Provide convenient access to the metadict, allows using the
        . notation instead of [] access

        """
        if self[name] != value:
            self["_dirty"] = True

        if name == "NOTREADY" and value is None:
            if "NOTREADY" in self:
                del self["NOTREADY"]

        # Special check: shape must be a tuple.
        # This avoids some common mistakes.
        if name == "shape" and not isinstance(value, tuple):
            import logging

            logger = logging.getLogger(__name__)
            msg = "Slot.meta.shape must always be a tuple, not {}".format(type(value))
            logger.error(msg)
            raise Exception(msg)

        self[name] = value
        return value

    def __getattr__(self, name):
        """Provide convenient acces to the metadict, allows using the
        . notation instead of [] access

        """
        return self[name]

    def copy(self):
        return MetaDict(dict.copy(self))

    def __eq__(self, other):
        if other is None:
            return False
        for k in set(list(self.keys()) + list(other.keys())):
            if k.startswith("__") or k == "NOTREADY":
                continue
            if k not in other or k not in self:
                return False
            if other[k] != self[k]:
                return False

        # Special case for NOTREADY.
        # If it is True in one and either False or missing in the other, then return False.
        if bool(self.NOTREADY) != bool(other.NOTREADY):
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        # This ensures that a given MetaDict can be relocated in a dict/set,
        # but doesn't ensure that identical MetaDicts hash to the same place.
        return hash(id(self))

    def assignFrom(self, other):
        """
        Copy all the elements from other into this
        """
        assert isinstance(other, MetaDict), "assignFrom() arg must be another MetaDict."
        dirty = not (self == other)
        origdirty = self._dirty
        origready = self._ready
        if dirty:
            self.clear()
            for k, v in list(other.items()):
                self[k] = copy.copy(v)
        self._dirty = origdirty | dirty

        # Readiness can't be assigned. It can only be assigned in
        # _setupOutputs or setValue (or copied via _changed)
        self._ready = origready

    def updateFrom(self, other):
        """
        Like dict.update(), but with special treatment for _ready and _dirty fields.
        """
        assert isinstance(other, MetaDict), "updateFrom() arg must be another MetaDict."
        dirty = not (self == other)
        origdirty = self._dirty
        origready = self._ready
        if dirty:
            for k, v in list(other.items()):
                self[k] = copy.copy(v)
        self._dirty = origdirty | dirty

        # Readiness can't be assigned. It can only be assigned in
        # _setupOutputs or setValue (or copied via _changed)
        self._ready = origready

    def getTaggedShape(self):
        """Convenience function for creating an OrderedDict of axistag
        keys and shape dimensions.

        """
        assert self.axistags is not None
        assert self.shape is not None
        keys = self.getAxisKeys()
        return OrderedDict(list(zip(keys, self.shape)))

    def getShape5D(self):
        return Shape5D(**self.getTaggedShape())

    def getAxisKeys(self):
        assert self.axistags is not None
        return [tag.key for tag in self.axistags]

    def getOriginalAxisKeys(self):
        """Returns the original axis keys

        In case we have `OpReorderAxes` in the chain somewhere, the original
        axistags are preserved in `original_axistags`, thus this is returned if
        present. Fallback is the `axistags` attribute (via `getAxisKeys()`).
        """
        if self.original_axistags is None:
            return self.getAxisKeys()

        return [tag.key for tag in self.original_axistags]

    def getOriginalShape(self):
        """Returns the original shape

        In case we have `OpReorderAxes` in the chain somewhere, the original shape
        is preserved in `original_shape`, thus this is returned if present.
        Fallback is the `shape` attribute.
        """
        if self.original_shape is None:
            assert self.shape is not None
            return self.shape

        return self.original_shape

    def getDtypeBytes(self):
        """
        For numpy dtypes only, return the size of the dtype in bytes.
        """
        dtype = self.dtype
        if isinstance(dtype, numpy.dtype):
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type
        return dtype().nbytes

    def __str__(self):
        """
        Used for debugging purposes.
        """
        pairs = []
        # For easy comparison, start with these in the same order every time.
        standard_keys = [
            "_ready",
            "NOTREADY",
            "shape",
            "axistags",
            "original_axistags",
            "dtype",
            "drange",
            "has_mask",
            "_dirty",
        ]
        for key in standard_keys:
            if key in self:
                pairs.append(key + " : " + repr(self[key]))

        for key, value in list(self.items()):
            if key not in standard_keys:
                pairs.append(key + " : " + repr(value))

        return "{" + ", ".join(pairs) + "}"

    def __repr__(self):
        return self.__str__()
