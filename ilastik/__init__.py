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
import sys
import re

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

__version_info__ = (1, 1, '6a7')
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
    
    # We permit versions like '1.0.5b', in which case '5b' 
    #  is simply converted to the integer 5 for compatibility purposes.
    int_tuple = ()
    for i in vstring.split('.'):
        m = re.search('(\d+)', i)
        assert bool(m), "Don't understand version component: {}".format( i )
        next_int = int(m.groups()[0])
        int_tuple = int_tuple + (next_int,)
    return int_tuple


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
    compatible_set = [(0,6), (1,0), (1,1)]
    if v1 in compatible_set and v2 in compatible_set:
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
