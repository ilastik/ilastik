###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2024, the ilastik developers
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
def deleteIfPresent(parentGroup: h5py.Group, name: str) -> None:
    """Deletes parentGroup[name], if it exists."""
    # Check first. If we try to delete a non-existent key,
    # hdf5 will complain on the console.
    if name in parentGroup:
        del parentGroup[name]


def slicingToString(slicing: Sequence[slice]) -> bytes:
    """Convert the given slicing into a string of the form
    '[0:1,2:3,4:5]'

    slices need to have integer start and stop values, step-size of 1
    is assumed

    The result is a utf-8 encoded bytes, for easy storage via h5py
    """
    if any(sl.step not in [None, 1] for sl in slicing):
        raise ValueError("Only slices with step size of `1` or `None` are supported.")

    if any(sl.start == None for sl in slicing):
        raise ValueError("Start indices for slicing must be integer, got `None`.")

    if any(sl.stop == None for sl in slicing):
        raise ValueError("Stop indices for slicing must be integer, got `None`.")

    strSlicing = "["
    for s in slicing:
        strSlicing += str(s.start)
        strSlicing += ":"
        strSlicing += str(s.stop)
        strSlicing += ","

    strSlicing = strSlicing[:-1]  # Drop the last comma
    strSlicing += "]"
    return strSlicing.encode("utf-8")


def stringToSlicing(strSlicing: Union[bytes, str]) -> Tuple[slice, ...]:
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    tuple of slices)

    """
    if isinstance(strSlicing, bytes):
        strSlicing = strSlicing.decode("utf-8")

    assert isinstance(strSlicing, str)

    slicing = []
    strSlicing = strSlicing[1:-1]  # Drop brackets
    sliceStrings = strSlicing.split(",")
    for s in sliceStrings:
        ends = s.split(":")
        if len(ends) != 2:
            raise ValueError(f"Did not expect slice element of form {s}")
        start = int(ends[0])
        stop = int(ends[1])
        slicing.append(slice(start, stop))

    return tuple(slicing)
