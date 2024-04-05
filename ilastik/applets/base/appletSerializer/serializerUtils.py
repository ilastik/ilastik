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


def getOrCreateGroup(parentGroup, groupName):
    """Returns parentGroup[groupName], creating first it if
    necessary.

    """

    return parentGroup.require_group(groupName)


def deleteIfPresent(parentGroup, name):
    """Deletes parentGroup[name], if it exists."""
    # Check first. If we try to delete a non-existent key,
    # hdf5 will complain on the console.
    if name in parentGroup:
        del parentGroup[name]


def slicingToString(slicing):
    """Convert the given slicing into a string of the form
    '[0:1,2:3,4:5]'

    The result is a utf-8 encoded bytes, for easy storage via h5py
    """
    strSlicing = "["
    for s in slicing:
        strSlicing += str(s.start)
        strSlicing += ":"
        strSlicing += str(s.stop)
        strSlicing += ","

    strSlicing = strSlicing[:-1]  # Drop the last comma
    strSlicing += "]"
    return strSlicing.encode("utf-8")


def stringToSlicing(strSlicing):
    """Parse a string of the form '[0:1,2:3,4:5]' into a slicing (i.e.
    tuple of slices)

    """
    if isinstance(strSlicing, bytes):
        strSlicing = strSlicing.decode("utf-8")

    slicing = []
    strSlicing = strSlicing[1:-1]  # Drop brackets
    sliceStrings = strSlicing.split(",")
    for s in sliceStrings:
        ends = s.split(":")
        start = int(ends[0])
        stop = int(ends[1])
        slicing.append(slice(start, stop))

    return tuple(slicing)
