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

import utility
import roi
import rtype
import stype
import operators
import request
import graph
import slot
