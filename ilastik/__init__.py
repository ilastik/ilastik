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

import sys

################################
## Add Submodules to sys.path ##
################################
import os
this_file = os.path.abspath(__file__)
this_file = os.path.realpath( this_file )
ilastik_package_dir = os.path.dirname(this_file)
ilastik_repo_dir = os.path.dirname(ilastik_package_dir)
submodule_dir = os.path.join( ilastik_repo_dir, 'submodules' )

# Add all submodules to the PYTHONPATH
import expose_submodules
expose_submodules.expose_submodules(submodule_dir)

##################
## Version info ##
##################

def _format_version(t):
    """converts a tuple to a string"""
    return '.'.join(str(i) for i in t)

__version_info__ = (1, 0, 0)
__version__ = _format_version(__version_info__)

core_developers = [ "Stuart Berg", 
                    "Fred Hamprecht", 
                    "Bernhard Kausler", 
                    "Anna Kreshuk", 
                    "Ullrich Koethe", 
                    "Thorben Kroeger", 
                    "Martin Schiegg", 
                    "Christoph Sommer", 
                    "Christoph Straehle" ]

developers = [ "Markus Doering", 
               "Kemal Eren", 
               "Burcin Erocal", 
               "Luca Fiaschi", 
               "Carsten Haubold", 
               "Ben Heuer", 
               "Philipp Hanslovsky", 
               "Kai Karius", 
               "Jens Kleesiek", 
               "Markus Nullmeier", 
               "Oliver Petra", 
               "Buote Xu", 
               "Chong Zhang" ]

def convertVersion(vstring):
    if not isinstance(vstring, str):
        raise Exception('tried to convert non-string version: {}'.format(vstring))
    return tuple(int(i) for i in vstring.split('.'))


def isVersionCompatible(version):
    """Return True if the current project file format is
    backwards-compatible with the format used in this version of
    ilastik.
    """
    if isinstance( version, float ):
        version = str(version)

    # Only consider major and minor rev
    v1 = convertVersion(version)[0:2]
    v2 = __version_info__[0:2]
    
    # Version 1.0 is compatible in all respects with version 0.6
    if v1 in [(0,6), (1,0)] and v2 in [(0,6), (1,0)]:
        return True
    
    # Otherwise, we need an exact match (for now)
    return v1 == v2

#######################
## Dependency checks ##
#######################

def _do_check(fnd, rqd, msg):
    if fnd < rqd:
        fstr = _format_version(fnd)
        rstr = _format_version(rqd)
        raise Exception(msg.format(fstr, rstr))

def _check_depends():
    import h5py

    _do_check(h5py.version.version_tuple,
              (2, 1, 0),
              "h5py version {0} too old; versions of h5py before {1} are not threadsafe.")

_check_depends()