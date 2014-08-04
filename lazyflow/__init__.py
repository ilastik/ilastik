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
#		   http://ilastik.org/license/
###############################################################################
try:
    import faulthandler
    faulthandler.enable()
except ImportError:
    pass

import os
this_file = os.path.abspath(__file__)
this_file = os.path.realpath( this_file )
lazyflow_package_dir = os.path.dirname(this_file)
lazyflow_repo_dir = os.path.dirname(lazyflow_package_dir)
submodule_dir = os.path.join( lazyflow_repo_dir, 'submodules' )

# Add all submodules to the PYTHONPATH
import expose_submodules
expose_submodules.expose_submodules(submodule_dir)

AVAILABLE_RAM_MB = 0 # 0 means "determine with psutil"

import utility
import roi
import rtype
import stype
import operators
import request
import graph
import slot
