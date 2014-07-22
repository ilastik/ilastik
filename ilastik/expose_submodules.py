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
import sys

def expose_submodules( submodule_dir ):
    walker = os.walk(submodule_dir, followlinks=True)
    try:
        path, dirnames, filenames = walker.next()
    except StopIteration:
        pass
    else:
        for dirname in dirnames:
            if dirname[0] != '.':
                sys.path.append( os.path.abspath( os.path.join(path, dirname) ) )
            
