#Python
import copy
import collections

class MetaDict(dict):
    """
    Helper class that manages the dirty state of the meta data of a slot.
    changing a meta dicts attributes sets it _dirty flag True.
    """
    def __init__(self, other=False):
        if(other):
            dict.__init__(self, other)
        else:
            dict.__init__(self)
            # flag that indicates whether all dependencies of the slot
            # are ready
            self._ready = False

        # flag that indicates whether any piece of meta information
        # changed since this flag was reset
        self._dirty = True

    def __setattr__(self, name, value):
        """Provide convenient acces to the metadict, allows using the
        . notation instead of [] access

        """
        if self.has_key(name):
            changed = True
            try:
                if self[name] == value:
                    changed = False
            except KeyError:
                pass
            if changed:
                self["_dirty"] = True
        self[name] = value
        return value

    def __getattr__(self, name):
        """Provide convenient acces to the metadict, allows using the
        . notation instead of [] access

        """
        return self[name]

    def __getitem__(self, name):
        """
        Does not throw KeyErrors.
        Non-existant items always return None.
        """
        if name in self.keys():
            return dict.__getitem__(self, name)
        else:
            return None

    def copy(self):
        """
        Construct a copy of the meta dict
        """
        return MetaDict(dict.copy(self))

    def assignFrom(self, other):
        """
        Copy all the elements from other into this
        """
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

    def getTaggedShape(self):
        """Convenience function for creating an OrderedDict of axistag
        keys and shape dimensions.

        """
        assert self.axistags is not None
        assert self.shape is not None
        keys = self.getAxisKeys()
        return collections.OrderedDict(zip(keys, self.shape))

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
