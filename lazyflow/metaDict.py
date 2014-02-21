# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Copyright 2011-2014, the ilastik developers

#Python
import copy
import numpy
from collections import OrderedDict, defaultdict

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

        if not '_ready' in self:
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
        
        # Special check: shape must be a tuple.
        # This avoids some common mistakes.
        if name == 'shape' and not isinstance(value, tuple):
            import logging
            logger = logging.getLogger(__name__)
            msg = "Slot.meta.shape must always be a tuple, not {}".format( type(value) )
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
            for k, v in other.items():
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
            for k, v in other.items():
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
        return OrderedDict(zip(keys, self.shape))

    def getAxisKeys(self):
        assert self.axistags is not None
        return [tag.key for tag in self.axistags]

    def getDtypeBytes(self):
        """
        For numpy dtypes only, return the size of the dtype in bytes.
        """
        dtype = self.dtype
        if type(dtype) is numpy.dtype:
            # Make sure we're dealing with a type (e.g. numpy.float64),
            #  not a numpy.dtype
            dtype = dtype.type        
        return dtype().nbytes
