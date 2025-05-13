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
import numpy
import vigra
import collections

from .roi import roiToSlice

import h5py


class InvalidResult(ValueError):
    """
    Raised within check_result_valid
    """

    pass


class SlotType:
    def __init__(self, slot):
        self.slot = slot

    def allocateDestination(self, roi):
        pass

    def writeIntoDestination(self, destination, value, roi):
        pass

    def isCompatible(self, value):
        """
        Slot types must implement this method.

        this method should check wether the supplied value
        is compatible with this type trait and should return true
        if this is the case.
        """
        pass

    def setupMetaForValue(self, value):
        """
        Slot types must implement this method.

        this method should extract valuable meta information
        from the provided value and set up the self.slot.meta
        MetaDict accordingly
        """
        pass

    def isConfigured(self):
        """
        Slot types must implement this method.

        it should analyse the .meta property of the slot
        and return wether the neccessary meta information
        is available.
        """
        return False

    def connect(self, slot):
        pass

    def copy_data(self, dst, src):
        """
        Slot types must implement this method

        if should copy all the data from src to dst.
        src and dst must be of the kind which is return by an operator with a slot
        of this type.

        usually dst, is the destination area specified by somebody, and src is the result
        that an operator returns.

        """
        pass

    def check_result_valid(self, roi, result):
        """
        Slot types must implement this method

        it must check wether the provided result is compatible with the user specified roi
        """
        return True


class ArrayLike(SlotType):
    def allocateDestination(self, roi):
        # If we do not support masked arrays, ensure that we are not allocating one.
        assert self.slot.allow_mask or (not self.slot.meta.has_mask), (
            'Allocation of a masked array is expected by the slot, "%s", of operator, '
            '"%s",'
            " even though it is not supported. If you believe this message to be incorrect, "
            "please pass the keyword argument `allow_mask=True` to the slot constructor."
            % (self.slot.operator.name, self.slot.name)
        )

        shape = roi.stop - roi.start if roi else self.slot.meta.shape
        storage = numpy.ndarray(shape, dtype=self.slot.meta.dtype)

        # if self.slot.meta.axistags is True:
        #     storage = vigra.taggedView(storage, self.slot.meta.axistags)
        #     #storage = vigra.VigraArray(storage, storage.dtype, axistags = copy.copy(self.slot.meta.axistags))))
        #     ##storage = storage.view(vigra.VigraArray)
        #     ##storage.axistags = copy.copy(self.slot.meta.axistags)
        if self.slot.meta.has_mask:
            storage_mask = numpy.zeros(storage.shape, dtype=bool)
            storage_fill_value = None
            if issubclass(storage.dtype.type, (numpy.bool_, numpy.integer)):
                storage_fill_value = storage.dtype.type(0)
            elif issubclass(storage.dtype.type, numpy.floating):
                storage_fill_value = storage.dtype.type(numpy.nan)
            elif issubclass(storage.dtype.type, numpy.complexfloating):
                storage_fill_value = storage.dtype.type(numpy.nan)
            storage = numpy.ma.masked_array(storage, mask=storage_mask, fill_value=storage_fill_value, shrink=False)

        return storage

    def writeIntoDestination(self, destination, value, roi):
        # If we do not support masked arrays, ensure that we are not being passed one.
        assert self.slot.allow_mask or (not self.slot.meta.has_mask), (
            "A masked array was provided as a destination. However,"
            ' the slot, "%s", of operator, '
            '"%s", does not support masked arrays.'
            " If you believe this message to be incorrect, "
            "please pass the keyword argument `allow_mask=True` to the slot constructor."
            % (self.slot.operator.name, self.slot.name)
        )

        if destination is not None:
            if not isinstance(destination, list):
                assert roi.dim == destination.ndim, "%r ndim=%r, shape=%r" % (
                    roi.toSlice(),
                    destination.ndim,
                    destination.shape,
                )
            sl = roiToSlice(roi.start, roi.stop)
            try:
                self.copy_data(destination, value[sl])
            except TypeError:
                # FIXME: This warning used to be triggered by a corner case that could be encountered by "value slots".
                #        The behavior here isn't truly deprecated.  But we need a better solution for lazyflow 2.0.
                # See ilastik/ilastik#704
                self.copy_data(destination, value)
        else:
            sl = roiToSlice(roi.start, roi.stop)
            try:
                destination = value[sl]
            except:
                # FIXME: This warning used to be triggered by a corner case that could be encountered by "value slots".
                #        The behavior here isn't truly deprecated.  But we need a better solution for lazyflow 2.0.
                # See ilastik/ilastik#704
                destination = [value]

            if isinstance(destination, numpy.ndarray) and destination.shape == ():
                # This is necessary because numpy types will not be caught in the except statement above.
                # They don't throw when used with __getitem__
                # e.g. try this:
                # x = np.int64(5)
                # assert type(x[()]) == np.ndarray and x[()].shape == ()

                # FIXME: This warning used to be triggered by a corner case that could be encountered by "value slots".
                #        The behavior here isn't truly deprecated.  But we need a better solution for lazyflow 2.0.
                # See ilastik/ilastik#704
                destination = [value]
        return destination

    def isCompatible(self, value):
        # FIXME ArrayLike.isCompatible
        return True

    def setupMetaForValue(self, value):
        if isinstance(value, numpy.ndarray):
            self.slot.meta.shape = value.shape
            self.slot.meta.dtype = value.dtype.type
            if hasattr(value, "axistags"):
                self.slot.meta.axistags = value.axistags
            if isinstance(value, numpy.ma.masked_array):
                self.slot.meta.has_mask = True
        else:
            self.slot.meta.shape = (1,)
            if (
                isinstance(value, int)
                or isinstance(value, float)
                or isinstance(value, numpy.floating)
                or isinstance(value, numpy.integer)
                or isinstance(value, numpy.bool_)
            ):
                self.slot.meta.dtype = type(value)
            else:
                self.slot.meta.dtype = object

    def isConfigured(self):
        meta = self.slot.meta
        if meta.shape is not None and meta.dtype is not None:
            return True
        else:
            return False

    def copy_data(self, dst, src):
        # Unfortunately, there appears to be a bug when copying masked arrays
        # ( https://github.com/numpy/numpy/issues/5558 ).
        # So, this must be used in the interim.
        if isinstance(dst, numpy.ma.masked_array):
            src_val = src[...]
            dst.data[...] = numpy.ma.getdata(src_val)
            dst.mask[...] = numpy.ma.getmaskarray(src_val)
            if isinstance(src_val, numpy.ma.masked_array):
                dst.fill_value = src_val.fill_value
        elif isinstance(dst, collections.abc.MutableSequence) or isinstance(src, collections.abc.MutableSequence):
            dst[:] = src[:]
        else:
            dst[...] = src[...]

    def check_result_valid(self, roi, result):
        if isinstance(result, numpy.ndarray):
            expected_shape = roi.stop - roi.start
            if not numpy.array_equal(result.shape, expected_shape):
                raise InvalidResult(f"Result has shape {result.shape}, but expected {expected_shape}")

        elif isinstance(result, list):
            expected_shape = roi.stop[0] - roi.start[0]
            if len(result) != expected_shape:
                raise InvalidResult(f"Result has shape {len(result)}, but expected {expected_shape}")

        elif isinstance(result, h5py.Group):
            # FIXME: this is a hack. the slot
            # OpCompressedCache.OutputHdf5 is not really array-like,
            # because it expects destinations of type h5py.Group.
            pass
        else:
            raise InvalidResult(f"Result of type {type(result).__name__} is not supported")


class Opaque(SlotType):
    def allocateDestination(self, roi):
        return None

    def writeIntoDestination(self, destination, value, roi):
        # FIXME: To be similar to the ArrayLike stype, we should return the value wrapped in a list:
        # destination = [value]
        # ...which is also why, for 'Opaque' slots, slot.value is not the same as slot[:].wait().
        # But for now, I'm leaving this alone.
        # "Fixing" this breaks many parts of the object classification workflow
        #  that are written to use the existing API, awkward as it is.
        # See also: ilastik/ilastik#704, and ilastik/ilastik#705.
        return value

    def isCompatible(self, value):
        return True

    def setupMetaForValue(self, value):
        self.slot.meta.shape = (1,)
        self.slot.meta.dtype = object
        self.slot.meta.axistags = vigra.defaultAxistags(1)

    def isConfigured(self):
        return True

    def copy_data(self, dst, src):
        raise NotImplementedError()
