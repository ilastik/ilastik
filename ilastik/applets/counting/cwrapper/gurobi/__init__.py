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
###############################################################################
import os
currentdir = os.path.dirname(__file__) 
import ctypes
libraryname = "libgurobiwrapper.so"
dllname = "gurobiwrapper.dll"
HAS_GUROBI = False
paths = [os.path.dirname(os.path.abspath(__file__)) + os.path.sep, ""]
for path in paths:
    try:
        sofile = path + libraryname
        extlib = ctypes.cdll.LoadLibrary(sofile)
        HAS_GUROBI = True
    except:
        pass

    try:
        dllfile = path + dllname
        extlib = ctypes.cdll.LoadLibrary(dllfile)
        HAS_GUROBI = True
    except:
        pass


if not HAS_GUROBI:
    raise RuntimeError("No gurobi wrapper found")
