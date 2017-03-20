###############################################################################
#   ilastik: interactive learning and segmentation toolkit
#
#       Copyright (C) 2011-2014, the ilastik developers
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
#		   http://ilastik.org/license.html
##############################################################################


try:
    import opengm
except ImportError:
    _have_opengm = False
else:
    _have_opengm = True


def haveGraphCut():
    return _have_opengm


if haveGraphCut():
    from _OpGraphCut import OpGraphCut, segmentGC
    from _OpObjectsSegment import OpObjectsSegment
